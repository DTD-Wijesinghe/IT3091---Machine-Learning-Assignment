from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks"
OUT.mkdir(exist_ok=True)

def make_notebook(title, owner, cells):
    nb = nbf.v4.new_notebook()
    nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.cells = [nbf.v4.new_markdown_cell(f"# {title}\n\n**Student responsibility:** {owner}\n\nThis revised notebook reads the validated project outputs and keeps paths repository-relative.")] + cells
    return nb

common = nbf.v4.new_code_cell("""from pathlib import Path
import pandas as pd

ROOT = Path.cwd()
if not (ROOT / 'data').exists():
    ROOT = ROOT.parent
print('Repository root:', ROOT)
""")

notebooks = {
    "01_production_data_wijesinghe.ipynb": make_notebook(
        "Production Data and Yield Target Audit", "IT24100858 - Wijesinghe D.T.D", [
            common,
            nbf.v4.new_code_cell("""yield_df = pd.read_csv(ROOT / 'data' / 'preprocessed' / 'crop_yield_preprocessed.csv')
print('Final yield observations:', len(yield_df))
print('Distinct crops:', yield_df['Crop'].nunique())
print('Distinct districts:', yield_df['District'].nunique())
print('Yield range (t/ha):', round(yield_df['Yield_t_ha'].min(), 3), 'to', round(yield_df['Yield_t_ha'].max(), 3))
yield_df[['Crop', 'District', 'Season', 'Year', 'Yield_t_ha']].head()
"""),
            nbf.v4.new_markdown_cell("The yield target is calculated from valid production and cultivated extent at the district-crop-season-year observational level. National totals are excluded from the modelling table.")
        ]),
    "02_weather_data_danthanarayana.ipynb": make_notebook(
        "Weather and Location Alignment Audit", "IT24100533 - Danthanarayana D.M.R", [
            common,
            nbf.v4.new_code_cell("""weather = pd.read_csv(ROOT / 'data' / 'raw' / 'weatherData.csv')
locations = pd.read_csv(ROOT / 'data' / 'raw' / 'locationData.csv')
yield_df = pd.read_csv(ROOT / 'data' / 'preprocessed' / 'crop_yield_preprocessed.csv')
print('Weather rows:', len(weather))
print('Location rows:', len(locations))
print('Yield rows with matched weather features:', len(yield_df))
yield_df[['Rainfall_3M_mm', 'TempMean_3M_C', 'WindSpeed_3M_kmh', 'SolarRadiation_3M_MJ_m2', 'ET0_3M_mm']].describe().round(2)
"""),
            nbf.v4.new_markdown_cell("Weather features are aggregated over the three-month pre-forecast window. The realised production outcome is not used as a weather feature.")
        ]),
    "03_price_data_jayakody.ipynb": make_notebook(
        "Colombo Wholesale Price Preparation", "IT24101090 - Jayakody N.D", [
            common,
            nbf.v4.new_code_cell("""price_df = pd.read_csv(ROOT / 'data' / 'preprocessed' / 'colombo_weekly_prices_preprocessed.csv', parse_dates=['Date', 'NextWeekStart'])
print('Final price observations:', len(price_df))
print('Crops:', price_df['Crop'].nunique())
print('Observation dates:', price_df['Date'].min().date(), 'to', price_df['Date'].max().date())
print('Target:', 'NextWeekWholesalePrice_RsKg')
price_df[['Crop', 'Date', 'CurrentPrice_RsKg', 'NextWeekWholesalePrice_RsKg']].head()
"""),
            nbf.v4.new_markdown_cell("The price target is the mean price in the following calendar week. Lag and rolling features are constructed from information available before the target week.")
        ]),
    "04_model_training_gunathilake.ipynb": make_notebook(
        "Model Comparison and Prediction Integration", "IT23361690 - Gunathilake B.M.P", [
            common,
            nbf.v4.new_code_cell("""metrics = pd.read_csv(ROOT / 'evidence' / 'model_metrics.csv')
print(metrics.to_string(index=False))
"""),
            nbf.v4.new_code_cell("""import joblib
price_model = joblib.load(ROOT / 'models' / 'wholesale_price_model.joblib')
yield_model = joblib.load(ROOT / 'models' / 'crop_yield_model.joblib')
print('Loaded price model:', type(price_model).__name__)
print('Loaded yield model:', type(yield_model).__name__)
"""),
            nbf.v4.new_markdown_cell("Both models are saved preprocessing-and-regression pipelines. The application loads these artefacts rather than using hardcoded predictions.")
        ]),
}

for name, nb in notebooks.items():
    nbf.write(nb, OUT / name)
    print('Wrote', name)
