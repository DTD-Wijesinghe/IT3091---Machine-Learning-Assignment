from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "Raw Datasets" / "researchData.xlsx"
PREPROCESSED_DIR = ROOT / "Wijesinghe.D.T.D-Crop Yield Preprocessing"
OUTPUT_DIR = ROOT / "Wijesinghe.D.T.D-Crop Yield Outputs"
PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

required = ["District", "Season", "CropCategory", "Crop", "Year", "Extent", "Production"]
data = pd.read_excel(RAW_FILE, usecols=required)

for column in ["Year", "Extent", "Production"]:
    data[column] = pd.to_numeric(
        data[column].astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )
for column in ["District", "Season", "CropCategory", "Crop"]:
    data[column] = data[column].astype("string").str.strip()

data = data.dropna(subset=required).copy()
data = data[(data["Extent"] > 0) & (data["Production"] >= 0)].copy()
data["Yield_t_ha"] = data["Production"] / data["Extent"]
data = data.replace([np.inf, -np.inf], np.nan).dropna(subset=["Yield_t_ha"])
data = data[data["Yield_t_ha"] <= data["Yield_t_ha"].quantile(0.995)].copy()
data["Year"] = data["Year"].astype(int)
data = data.sort_values(["Crop", "District", "Year", "Season"]).reset_index(drop=True)

prepared_file = PREPROCESSED_DIR / "wijesinghe_yield_preprocessed_15000plus.csv"
data.to_csv(prepared_file, index=False)

features = ["District", "Season", "CropCategory", "Crop", "Year", "Extent"]
target = "Yield_t_ha"
train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)
categorical = ["District", "Season", "CropCategory", "Crop"]
numeric = ["Year", "Extent"]
preprocessor = ColumnTransformer([
    ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
    ("numeric", "passthrough", numeric),
])
model = Pipeline([
    ("preprocessor", preprocessor),
    ("model", RandomForestRegressor(
        n_estimators=50, max_depth=18, min_samples_leaf=3, random_state=42, n_jobs=-1
    )),
])
model.fit(train_data[features], train_data[target])
prediction = model.predict(test_data[features])

metrics = pd.DataFrame([{
    "Records": len(data),
    "TrainRecords": len(train_data),
    "TestRecords": len(test_data),
    "MAE_t_per_ha": mean_absolute_error(test_data[target], prediction),
    "RMSE_t_per_ha": np.sqrt(mean_squared_error(test_data[target], prediction)),
    "R2": r2_score(test_data[target], prediction),
}])
metrics.to_csv(OUTPUT_DIR / "wijesinghe_yield_model_metrics.csv", index=False)
joblib.dump(model, OUTPUT_DIR / "wijesinghe_yield_model.joblib")

print(f"Prepared yield records: {len(data):,}")
print(f"Saved dataset: {prepared_file}")
print(metrics.round(4).to_string(index=False))
