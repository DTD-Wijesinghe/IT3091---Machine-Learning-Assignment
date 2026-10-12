from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "Raw Datasets"
OUTPUT = ROOT / "Preprocessed Datasets" / "03_price_preprocessed.csv"

files = list(RAW.glob("*Weekly*Average*Retail*Prices*.xlsx")) or list(RAW.glob("*Weekly*Prices*.xlsx"))
if not files:
    raise FileNotFoundError("Weekly wholesale workbook not found.")

source = files[0]
preview = pd.read_excel(source, header=None, nrows=15)
header_row = next(
    (i for i, row in preview.iterrows() if "market type" in {str(v).strip().lower() for v in row.values}),
    None,
)
if header_row is None:
    raise ValueError("Market Type header was not found.")

raw = pd.read_excel(source, header=header_row)
raw.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in raw.columns]
raw = raw.loc[:, ~raw.columns.astype(str).str.startswith("Unnamed")]
price = raw[raw["Market Type"].astype(str).str.strip().str.lower().eq("wholesale")].copy()
price["Year"] = pd.to_numeric(price["Year"], errors="coerce")
price = price.dropna(subset=["Year", "Commodity"])
price["Year"] = price["Year"].astype(int)

week_cols = [c for c in price.columns if re.fullmatch(r"W\d+", str(c).strip(), flags=re.I)]
long = price.melt(
    id_vars=["Year", "Market Type", "Commodity"],
    value_vars=week_cols,
    var_name="Week",
    value_name="WholesalePrice_RsKg",
)
long["WeekNumber"] = pd.to_numeric(long["Week"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
long["WholesalePrice_RsKg"] = pd.to_numeric(long["WholesalePrice_RsKg"], errors="coerce")
long = long.dropna(subset=["WeekNumber", "WholesalePrice_RsKg"])
long["WeekNumber"] = long["WeekNumber"].astype(int)
long["WeekDate"] = pd.to_datetime(
    long["Year"].astype(str) + "-W" + long["WeekNumber"].astype(str).str.zfill(2) + "-1",
    format="%G-W%V-%u",
    errors="coerce",
)
long = long.dropna(subset=["WeekDate"])

def normalise(value):
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", str(value).upper())).strip()


crop_map = {
    "GREEN BEANS": "Beans", "CARROT": "Carrot", "LEEKS": "Leeks", "BEETROOT": "Beetroot",
    "KNOL KHOL": "Knolkhol", "RADDISH": "Raddish", "CABBAGE": "Cabbage", "TOMATOES": "Tomatoes",
    "BRINJALS": "Brinjals", "CAPSICUM": "Capsicum", "ASH PLANTAINS": "Ash Plantain",
    "BITTER GOURD": "Bitter Gourd", "CUCUMBER": "Cucumber", "DRUMSTIC": "Drumstics",
    "LADIES FINGERS": "Bandakka", "LONG BEANS": "Long Bean", "LUFFA": "Luffa", "SNAKE GOURD": "Snake Gourd",
}
long["Crop"] = long["Commodity"].map(normalise).map(crop_map)
long = long.dropna(subset=["Crop"])

weekly = long.groupby(["Crop", "WeekDate"], as_index=False)["WholesalePrice_RsKg"].mean()
weekly = weekly.sort_values(["Crop", "WeekDate"])
groups = weekly.groupby("Crop", group_keys=False)
weekly["PreviousWeekWholesalePrice_RsKg"] = groups["WholesalePrice_RsKg"].shift(1)
weekly["NextWeekWholesalePrice_RsKg"] = groups["WholesalePrice_RsKg"].shift(-1)
weekly["Year"] = weekly["WeekDate"].dt.year
weekly["WeekNumber"] = weekly["WeekDate"].dt.isocalendar().week.astype(int)
weekly["Month"] = weekly["WeekDate"].dt.month
weekly["Market"] = "Colombo and suburbs"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
weekly.to_csv(OUTPUT, index=False)
print(f"Saved {len(weekly):,} weekly records to {OUTPUT}")
