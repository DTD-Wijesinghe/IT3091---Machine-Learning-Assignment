from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def canonical_crop(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value).strip().upper())
    text = text.replace("(UP)", "").replace("(OTHER)", "")
    text = text.replace("_", " ")
    aliases = {
        "BRINJALS": "Brinjal",
        "EGGPLANT": "Brinjal",
        "BEETROOT": "Beetroot",
        "CABBAGE": "Cabbage",
        "BITTER GOURD": "Bitter Gourd",
        "ASH PLANTAINS": "Ash Plantain",
        "GREEN BEANS": "Green Beans",
        "GREEN CHILLIES": "Green Chillies",
        "LADIES FINGERS": "Ladies Fingers",
        "KNOL-KHOL": "Knolkhol",
        "SWEET POTATOES": "Sweet Potato",
        "DRUMSTIC": "Drumstick",
        "LONG BEANS": "Long Beans",
        "SNAKE GOURD": "Snake Gourd",
    }
    return aliases.get(text, text.title())


def metric_row(task: str, model: str, split: str, y_true: pd.Series, y_pred: np.ndarray) -> dict:
    return {
        "Task": task,
        "Model": model,
        "Split": split,
        "Records": int(len(y_true)),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "R2": float(r2_score(y_true, y_pred)),
    }


def make_preprocessor(categorical: list[str], numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
            ("num", StandardScaler(), numeric),
        ],
        remainder="drop",
    )


def models(categorical: list[str], numeric: list[str]) -> dict[str, Pipeline]:
    def pipe(estimator):
        return Pipeline([("prep", make_preprocessor(categorical, numeric)), ("model", estimator)])

    return {
        "Ridge": pipe(Ridge(alpha=10.0)),
        "Random Forest": pipe(RandomForestRegressor(n_estimators=250, min_samples_leaf=2, random_state=42, n_jobs=-1)),
        "Gradient Boosting": pipe(GradientBoostingRegressor(n_estimators=250, learning_rate=0.04, max_depth=2, random_state=42)),
    }


def build_price_dataset(path: Path) -> pd.DataFrame:
    rows: list[tuple[pd.Timestamp, str, float]] = []
    for sheet in pd.ExcelFile(path).sheet_names:
        raw = pd.read_excel(path, sheet_name=sheet, header=3)
        item_col = raw.columns[3]
        for _, row in raw[raw[item_col].notna()].iterrows():
            crop = canonical_crop(row[item_col])
            for column in raw.columns[4:]:
                if isinstance(column, pd.Timestamp):
                    date = column
                elif isinstance(column, str) and re.match(r"^\d{4}[.-]\d{2}[.-]\d{2}$", column):
                    date = pd.to_datetime(column, errors="coerce")
                else:
                    continue
                value = pd.to_numeric(row[column], errors="coerce")
                if pd.notna(date) and pd.notna(value) and float(value) >= 0:
                    rows.append((pd.Timestamp(date).normalize(), crop, float(value)))
    daily = pd.DataFrame(rows, columns=["Date", "Crop", "Price"])
    daily = daily.groupby(["Date", "Crop"], as_index=False)["Price"].mean()
    daily = daily.sort_values(["Crop", "Date"]).reset_index(drop=True)
    daily["WeekStart"] = daily["Date"] - pd.to_timedelta(daily["Date"].dt.weekday, unit="D")
    weekly = daily.groupby(["Crop", "WeekStart"], as_index=False)["Price"].mean().rename(columns={"Price": "NextWeekWholesalePrice_RsKg"})
    weekly["ForecastDate"] = weekly["WeekStart"] - pd.Timedelta(days=7)
    weekly = weekly[["Crop", "ForecastDate", "NextWeekWholesalePrice_RsKg"]]
    out = daily.copy()
    out["NextWeekStart"] = out["WeekStart"] + pd.Timedelta(days=7)
    target = weekly.rename(columns={"ForecastDate": "NextWeekStart"})
    out = out.merge(target, on=["Crop", "NextWeekStart"], how="inner")
    out["CurrentPrice_RsKg"] = out["Price"]
    grouped = out.groupby("Crop", group_keys=False)
    out["Lag1Price_RsKg"] = grouped["Price"].shift(1)
    out["Lag2Price_RsKg"] = grouped["Price"].shift(2)
    out["Lag3Price_RsKg"] = grouped["Price"].shift(3)
    out["Rolling7Mean_RsKg"] = grouped["Price"].transform(lambda s: s.rolling(7, min_periods=3).mean())
    out["Rolling28Mean_RsKg"] = grouped["Price"].transform(lambda s: s.rolling(28, min_periods=7).mean())
    out["Rolling7Std_RsKg"] = grouped["Price"].transform(lambda s: s.rolling(7, min_periods=3).std())
    out["Month"] = out["Date"].dt.month
    out["WeekOfYear"] = out["Date"].dt.isocalendar().week.astype(int)
    out["Year"] = out["Date"].dt.year
    out["Market"] = "Pettah/Peliyagoda Colombo"
    feature_cols = ["Crop", "Market", "Year", "Month", "WeekOfYear", "CurrentPrice_RsKg", "Lag1Price_RsKg", "Lag2Price_RsKg", "Lag3Price_RsKg", "Rolling7Mean_RsKg", "Rolling28Mean_RsKg", "Rolling7Std_RsKg"]
    out = out.dropna(subset=feature_cols + ["NextWeekWholesalePrice_RsKg"]).copy()
    return out[["Date", "NextWeekStart", *feature_cols, "NextWeekWholesalePrice_RsKg"]].reset_index(drop=True)


def build_yield_dataset(production_path: Path, weather_path: Path, location_path: Path) -> pd.DataFrame:
    production = pd.read_excel(production_path)
    production["Year"] = pd.to_numeric(production["Year"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
    production["Extent"] = pd.to_numeric(production["Extent"], errors="coerce")
    production["Production"] = pd.to_numeric(production["Production"], errors="coerce")
    production = production[
        production["Season"].isin(["Yala", "Maha"])
        & production["Year"].between(2012, 2023)
        & (production["District"] != "National Total")
        & (production["Extent"] > 0)
        & production["Production"].notna()
    ].copy()
    production["Yield_t_ha"] = production["Production"] / production["Extent"]
    district_map = {"Hanbantota": "Hambantota", "Kaluthara": "Kalutara", "Monaragala": "Moneragala", "Mullativu": "Mullaitivu"}
    production["District"] = production["District"].replace(district_map)
    locations = pd.read_csv(location_path)
    production = production[production["District"].isin(locations["city_name"])].copy()
    production = production.merge(locations[["location_id", "city_name"]], left_on="District", right_on="city_name", how="inner")
    weather = pd.read_csv(weather_path)
    weather["date"] = pd.to_datetime(weather["date"], errors="coerce")
    weather = weather.merge(locations[["location_id", "city_name"]], on="location_id", how="inner")
    weather = weather.rename(columns={"city_name": "District"})
    def find_column(prefix: str) -> str:
        matches = [c for c in weather.columns if str(c).startswith(prefix)]
        if not matches:
            raise KeyError(f"Required weather column was not found: {prefix}")
        return matches[0]

    weather = weather.rename(columns={
        find_column("rain_sum"): "Rainfall_mm",
        find_column("temperature_2m_mean"): "Temperature_C",
        find_column("wind_speed_10m_max"): "WindSpeed_kmh",
        find_column("shortwave_radiation_sum"): "SolarRadiation_MJ_m2",
        find_column("et0_fao_evapotranspiration"): "ET0_mm",
    })
    weather_features = []
    for district, year, season in production[["District", "Year", "Season"]].drop_duplicates().itertuples(index=False, name=None):
        anchor = pd.Timestamp(year=int(year), month=4 if season == "Yala" else 9, day=1)
        window = weather[(weather["District"] == district) & (weather["date"] < anchor) & (weather["date"] >= anchor - pd.DateOffset(months=3))]
        if len(window) < 80:
            continue
        weather_features.append({
            "District": district,
            "Year": year,
            "Season": season,
            "ForecastDate": anchor,
            "Rainfall_3M_mm": window["Rainfall_mm"].sum(),
            "TempMean_3M_C": window["Temperature_C"].mean(),
            "WindSpeed_3M_kmh": window["WindSpeed_kmh"].mean(),
            "SolarRadiation_3M_MJ_m2": window["SolarRadiation_MJ_m2"].mean(),
            "ET0_3M_mm": window["ET0_mm"].sum(),
            "WeatherDays_3M": len(window),
        })
    out = production.merge(pd.DataFrame(weather_features), on=["District", "Year", "Season"], how="inner")
    out["Crop"] = out["Crop"].map(canonical_crop)
    return out[["District", "CropCategory", "Crop", "Season", "Year", "Extent", "Production", "Yield_t_ha", "ForecastDate", "Rainfall_3M_mm", "TempMean_3M_C", "WindSpeed_3M_kmh", "SolarRadiation_3M_MJ_m2", "ET0_3M_mm", "WeatherDays_3M"]].reset_index(drop=True)


def train_task(df: pd.DataFrame, task: str, target: str, categorical: list[str], numeric: list[str], output: Path) -> tuple[pd.DataFrame, dict]:
    df = df.sort_values("ForecastDate" if "ForecastDate" in df else "Date").reset_index(drop=True)
    time_col = "ForecastDate" if "ForecastDate" in df else "Date"
    dates = pd.to_datetime(df[time_col])
    train = df[dates.dt.year <= 2019]
    validation = df[dates.dt.year.isin([2020, 2021])]
    test = df[dates.dt.year >= 2022]
    feature_cols = categorical + numeric
    metrics = []
    best_name = None
    best_score = float("inf")
    best_model = None
    for name, model in {"Dummy Baseline": Pipeline([("prep", make_preprocessor(categorical, numeric)), ("model", DummyRegressor(strategy="median"))]), **models(categorical, numeric)}.items():
        model.fit(train[feature_cols], train[target])
        pred_val = model.predict(validation[feature_cols])
        metrics.append(metric_row(task, name, "validation", validation[target], pred_val))
        score = metrics[-1]["MAE"]
        if name != "Dummy Baseline" and score < best_score:
            best_score, best_name, best_model = score, name, model
    final_train = pd.concat([train, validation], ignore_index=True)
    best_model.fit(final_train[feature_cols], final_train[target])
    pred_test = best_model.predict(test[feature_cols])
    metrics.append(metric_row(task, best_name, "test", test[target], pred_test))
    baseline = float(train[target].iloc[-1]) if task == "price" else float(train[target].median())
    baseline_pred = np.full(len(test), baseline)
    metrics.append(metric_row(task, "Simple baseline", "test", test[target], baseline_pred))
    joblib.dump(best_model, output / f"{task}_model.joblib")
    with (output / f"{task}_metadata.json").open("w", encoding="utf-8") as f:
        json.dump({"task": task, "target": target, "features": feature_cols, "selected_model": best_name}, f, indent=2)
    return pd.DataFrame(metrics), {"train": len(train), "validation": len(validation), "test": len(test), "selected_model": best_name}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--daily-price", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    price = build_price_dataset(args.daily_price)
    yield_df = build_yield_dataset(args.repo / "Raw Datasets/researchData.xlsx", args.repo / "Raw Datasets/weatherData.csv", args.repo / "Raw Datasets/locationData.csv")
    price.to_csv(args.output / "price_next_week_dataset.csv", index=False)
    yield_df.to_csv(args.output / "yield_dataset.csv", index=False)
    price_metrics, price_counts = train_task(price, "price", "NextWeekWholesalePrice_RsKg", ["Crop", "Market"], ["Year", "Month", "WeekOfYear", "CurrentPrice_RsKg", "Lag1Price_RsKg", "Lag2Price_RsKg", "Lag3Price_RsKg", "Rolling7Mean_RsKg", "Rolling28Mean_RsKg", "Rolling7Std_RsKg"], args.output)
    yield_metrics, yield_counts = train_task(yield_df, "yield", "Yield_t_ha", ["District", "CropCategory", "Crop", "Season"], ["Year", "Rainfall_3M_mm", "TempMean_3M_C", "WindSpeed_3M_kmh", "SolarRadiation_3M_MJ_m2", "ET0_3M_mm", "WeatherDays_3M"], args.output)
    pd.concat([price_metrics, yield_metrics], ignore_index=True).to_csv(args.output / "model_metrics.csv", index=False)
    counts = pd.DataFrame([
        {
            "Task": "Price",
            "Original_records": 47886,
            "Valid_source_records": 42056,
            "After_cleaning": 42056,
            "After_preprocessing": len(price),
            "Final_usable_labelled_records": len(price),
            **price_counts,
        },
        {
            "Task": "Yield",
            "Original_records": 94755,
            "Valid_source_records": 16626,
            "After_cleaning": len(yield_df),
            "After_preprocessing": len(yield_df),
            "Final_usable_labelled_records": len(yield_df),
            **yield_counts,
        },
    ])
    counts.to_csv(args.output / "record_counts.csv", index=False)
    (args.output / "source_notes.md").write_text(
        "# Revised data sources\n\n"
        "Price observations come from the Colombo/Pettah daily wholesale workbook. Each row is a crop-date observation with a target equal to the mean wholesale price in the following calendar week.\n\n"
        "Yield observations come from valid district-crop-season-year production records matched to a district weather location and a pre-forecast three-month weather window.\n\n"
        "The weekly Colombo/suburbs workbook remains a documented source for comparison and historical checks; it is not concatenated with daily observations as if it were the same measurement process.\n",
        encoding="utf-8",
    )
    print(counts.to_string(index=False))
    print(pd.concat([price_metrics, yield_metrics], ignore_index=True).to_string(index=False))


if __name__ == "__main__":
    main()
