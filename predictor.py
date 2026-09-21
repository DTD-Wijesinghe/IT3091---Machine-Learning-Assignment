"""Core data and prediction logic for the crop planning dashboard.

The model was trained on the leakage-safe 04_final_modelling_dataset.csv
using the nine columns listed in model_metadata.json.  This module deliberately
keeps Streamlit out of the core so it can be tested from a plain Python process.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


FEATURES = [
    "Crop",
    "Season",
    "Year",
    "Rainfall_3M_mm",
    "TempMean_3M_C",
    "WindSpeed_3M_kmh",
    "SolarRadiation_3M_MJ_m2",
    "ET0_3M_mm",
    "PrevMonthWholesalePrice_RsKg",
]
TARGETS = ["Yield_t_ha", "NextMonthWholesalePrice_RsKg"]


@dataclass(frozen=True)
class ForecastContext:
    forecast_date: pd.Timestamp
    weather_window_start: pd.Timestamp
    weather_window_end: pd.Timestamp
    season: str
    year: int
    anchor_month: int


@dataclass(frozen=True)
class RetrievedData:
    weather: dict[str, float]
    previous_price: float
    weather_source: str
    price_source: str


def load_assets(base_dir: str | Path) -> dict[str, Any]:
    """Load the saved model and local datasets used by the dashboard."""

    base = Path(base_dir)
    with (base / "model_metadata.json").open(encoding="utf-8") as handle:
        metadata = json.load(handle)

    model = joblib.load(base / "final_multioutput_model.joblib")
    modelling = pd.read_csv(base / "Preprocessed Datasets" / "04_final_modelling_dataset.csv")
    weather = pd.read_csv(base / "Preprocessed Datasets" / "02_weather_preprocessed.csv")
    prices = pd.read_csv(base / "Preprocessed Datasets" / "03_price_preprocessed.csv")
    weather["ForecastDate"] = pd.to_datetime(weather["ForecastDate"])
    weather["WeatherWindowStart"] = pd.to_datetime(weather["WeatherWindowStart"])
    weather["WeatherWindowEnd"] = pd.to_datetime(weather["WeatherWindowEnd"])
    prices["MonthDate"] = pd.to_datetime(prices["MonthDate"])
    modelling["ForecastDate"] = pd.to_datetime(modelling["ForecastDate"])
    modelling["AnchorDate"] = pd.to_datetime(modelling["AnchorDate"])

    return {
        "metadata": metadata,
        "model": model,
        "modelling": modelling,
        "weather": weather,
        "prices": prices,
        "crops": sorted(modelling["Crop"].dropna().astype(str).unique().tolist()),
    }


def make_forecast_context(
    today: date | pd.Timestamp | None = None,
    season: str | None = None,
) -> ForecastContext:
    """Return the next applicable Yala/Maha anchor and its complete 3-month window."""

    current = pd.Timestamp(today or date.today())
    detected_season = "Yala" if 4 <= current.month <= 8 else "Maha" if current.month >= 9 else "Yala"
    if season is None:
        season = detected_season
    if season not in {"Yala", "Maha"}:
        raise ValueError("Season must be either Yala or Maha.")
    if season == "Yala":
        anchor_month = 4
    else:
        anchor_month = 9

    forecast_date = pd.Timestamp(year=current.year, month=anchor_month, day=1)
    weather_window_end = forecast_date - pd.Timedelta(days=1)
    weather_window_start = weather_window_end - pd.DateOffset(months=3) + pd.Timedelta(days=1)
    return ForecastContext(
        forecast_date=forecast_date,
        weather_window_start=pd.Timestamp(weather_window_start),
        weather_window_end=weather_window_end,
        season=season,
        year=current.year,
        anchor_month=anchor_month,
    )


def _weather_values(row: pd.Series) -> dict[str, float]:
    return {
        "Rainfall_3M_mm": float(row["Rainfall_3M_mm"]),
        "TempMean_3M_C": float(row["TempMean_3M_C"]),
        "WindSpeed_3M_kmh": float(row["WindSpeed_3M_kmh"]),
        "SolarRadiation_3M_MJ_m2": float(row["SolarRadiation_3M_MJ_m2"]),
        "ET0_3M_mm": float(row["ET0_3M_mm"]),
    }


def retrieve_automatic_inputs(context: ForecastContext, assets: dict[str, Any]) -> RetrievedData:
    """Retrieve weather and previous price from the saved historical datasets.

    An exact year/season row is used for historical tests. For a current/future
    year outside the training period, the same-season historical median is used,
    preserving the three-complete-month rule and making the fallback explicit.
    """

    weather = assets["weather"]
    exact = weather[(weather["Year"] == context.year) & (weather["Season"] == context.season)]
    if not exact.empty:
        weather_row = exact.iloc[0]
        weather_source = f"Exact historical {context.year} {context.season} row"
    else:
        seasonal = weather[weather["Season"] == context.season]
        if seasonal.empty:
            raise ValueError(f"No historical weather rows are available for {context.season}.")
        weather_row = seasonal[FEATURES[3:8]].median(numeric_only=True)
        weather_source = (
            f"Historical median for {context.season} "
            f"({int(seasonal['Year'].min())}-{int(seasonal['Year'].max())})"
        )

    prices = assets["prices"]
    previous_month = context.forecast_date - pd.offsets.MonthBegin(1)
    crop_prices = prices[prices["MonthDate"].dt.month == previous_month.month].copy()
    if not crop_prices.empty:
        latest_crop = crop_prices[crop_prices["Crop"].astype(str).eq(str(assets.get("selected_crop", "")))]
    else:
        latest_crop = pd.DataFrame()

    # The crop is inserted into assets for this short-lived retrieval call by
    # build_feature_row; the fallback below is used when called independently.
    if latest_crop.empty:
        latest_crop = prices[prices["MonthDate"].dt.month == previous_month.month]
    if latest_crop.empty:
        latest_crop = prices
    latest_crop = latest_crop.sort_values("MonthDate")
    price_row = latest_crop.iloc[-1]
    previous_price = price_row.get("WholesalePrice_RsKg")
    if pd.isna(previous_price):
        previous_price = price_row.get("PrevMonthWholesalePrice_RsKg")
    if pd.isna(previous_price):
        raise ValueError("No usable previous-month price is available in the price dataset.")
    price_source = f"Latest available {price_row['MonthDate'].strftime('%b %Y')} price history"
    return RetrievedData(
        weather=_weather_values(weather_row),
        previous_price=float(previous_price),
        weather_source=weather_source,
        price_source=price_source,
    )


def retrieve_inputs_for_crop(context: ForecastContext, crop: str, assets: dict[str, Any]) -> RetrievedData:
    scoped = dict(assets)
    scoped["selected_crop"] = crop
    data = retrieve_automatic_inputs(context, scoped)
    prices = assets["prices"]
    previous_month = context.forecast_date - pd.offsets.MonthBegin(1)
    exact_date = prices[
        prices["Crop"].astype(str).eq(str(crop))
        & prices["MonthDate"].eq(previous_month)
    ].sort_values("MonthDate")
    matching = prices[
        prices["Crop"].astype(str).eq(str(crop))
        & prices["MonthDate"].dt.month.eq(previous_month.month)
    ].sort_values("MonthDate")
    if not exact_date.empty:
        row = exact_date.iloc[-1]
        source_suffix = "exact historical month"
    elif not matching.empty:
        row = matching.iloc[-1]
        source_suffix = "matching-month history"
    else:
        row = None
        source_suffix = "latest available history"
    if row is not None:
        value = row["WholesalePrice_RsKg"]
        if pd.isna(value):
            value = row["PrevMonthWholesalePrice_RsKg"]
        if not pd.isna(value):
            data = RetrievedData(data.weather, float(value), data.weather_source,
                                 f"{crop}: {row['MonthDate'].strftime('%b %Y')} {source_suffix}")
    return data


def build_feature_row(crop: str, context: ForecastContext, retrieved: RetrievedData) -> pd.DataFrame:
    """Build the exact nine-feature model row in metadata order."""

    values = {
        "Crop": crop,
        "Season": context.season,
        "Year": context.year,
        **retrieved.weather,
        "PrevMonthWholesalePrice_RsKg": retrieved.previous_price,
    }
    return pd.DataFrame([values], columns=FEATURES)


def predict(feature_row: pd.DataFrame, assets: dict[str, Any]) -> dict[str, float]:
    if list(feature_row.columns) != FEATURES:
        raise ValueError(f"Feature row must use exactly {FEATURES}.")
    output = np.asarray(assets["model"].predict(feature_row), dtype=float).reshape(-1)
    if output.size != 2 or not np.isfinite(output).all():
        raise ValueError("The model returned an invalid two-target prediction.")
    return {"Yield_t_ha": float(output[0]), "NextMonthWholesalePrice_RsKg": float(output[1])}


def recommendation(prediction: dict[str, float], planned_area_ha: float, assets: dict[str, Any]) -> dict[str, Any]:
    if planned_area_ha <= 0:
        raise ValueError("Planned area must be greater than zero.")
    yield_t_ha = max(0.0, prediction["Yield_t_ha"])
    price = prediction["NextMonthWholesalePrice_RsKg"]
    expected_production = yield_t_ha * planned_area_ha
    baseline = float(assets["modelling"]["Yield_t_ha"].median())
    if yield_t_ha >= baseline and price >= 0:
        label = "Favourable: predicted yield is at or above the historical median."
    elif yield_t_ha < baseline and price < 0:
        label = "Caution: predicted yield and price outlook are weak."
    else:
        label = "Mixed outlook: review costs, farm conditions and market timing."
    return {
        "yield_t_ha": yield_t_ha,
        "next_month_price": price,
        "expected_production_tonnes": expected_production,
        "historical_median_yield_t_ha": baseline,
        "label": label,
        "note": "Experimental decision support; price performance was weak out of sample and should not be used alone.",
    }


def run_forecast(crop: str, planned_area_ha: float, context: ForecastContext, assets: dict[str, Any]) -> dict[str, Any]:
    retrieved = retrieve_inputs_for_crop(context, crop, assets)
    row = build_feature_row(crop, context, retrieved)
    prediction = predict(row, assets)
    return {
        "context": context,
        "retrieved": retrieved,
        "feature_row": row,
        "prediction": prediction,
        "recommendation": recommendation(prediction, planned_area_ha, assets),
    }
