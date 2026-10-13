# AgriPlan: weekly vegetable prices and crop yield prediction system

AgriPlan is an IT3091 group project for agricultural planning in Sri Lanka. The app estimates the **next week's wholesale vegetable price for Colombo and suburbs** and **crop yield in tonnes per hectare**. A user can also enter cultivated hectares to see an estimated total production. These are planning estimates, not guaranteed market or harvest outcomes.

## What is in the repository

| Work | Notebook | Main output |
| --- | --- | --- |
| Production data preparation | `01_IT24100858_Wijesinghe_DTD_Production.ipynb` | `Preprocessed Datasets/01_production_preprocessed.csv` |
| Weather and location preparation | `02_IT24100533_Danthanarayana_DMR_Weather.ipynb` | `Preprocessed Datasets/02_weather_preprocessed.csv` |
| Weekly wholesale price preparation | `03_IT24101090_JAYAKODY_ND_Price_Weekly_Only.ipynb` | `Preprocessed Datasets/03_price_preprocessed.csv` |
| Weekly price model comparison | `04_IT23361690_Gunathilake_BMP_Weekly_Only.ipynb` | `weekly_price_model.joblib`, comparison, metrics, and test predictions |
| Crop-yield data and model | `07_Wijesinghe_DTD_Crop_Yield_Preprocessing.ipynb` | `Wijesinghe.D.T.D-Crop Yield Preprocessing/` and `Wijesinghe.D.T.D-Crop Yield Outputs/` |

The raw workbooks and weather files are in `Raw Datasets/`. The active Streamlit entry point is `app.py`, which loads `streamlit_app/app.py`. The current price and yield models run as **separate prediction pipelines**; the app displays both in one place. The production and weather notebooks are retained as group data work, but their prepared outputs are not inputs to the active weekly price or yield models.

## Data and results currently committed

- The price workbook covers Colombo and suburbs. Its 15,598 prepared crop-week wholesale prices span January 2012 to March 2025. After removing rows without a previous-week price or a next-week target, 15,546 rows were used for modelling.
- The price model trains on records through 2019 and reports performance on 2020 onward: **Linear Regression**, MAE **27.24 Rs/kg**, RMSE **48.33 Rs/kg**, and R² **0.906** on 6,159 test rows.
- The crop-yield dataset contains **60,529** prepared rows from 2001 to 2025. A Random Forest model was evaluated with a random 80/20 row split: MAE **1.99 t/ha**, RMSE **3.10 t/ha**, and R² **0.676** on 12,106 test rows.
- The app uses the current wholesale price, previous-week price, crop, and calendar fields for the next-week price estimate. For yield it uses district, season, crop category, crop, year, and cultivated extent. Estimated production equals predicted yield multiplied by the entered hectares.

These figures describe the committed outputs, not a guaranteed score after a new run. The price series does not represent a national wholesale price. Its latest committed observation is from March 2025, so a current forecast requires an up-to-date current and previous-week price supplied by the user.

## Reproduce the work

Open the notebooks in Google Colab and run their cells in order. Run 01 and 02 for the group production and weather preparation, 03 for the weekly price table, 04 for the weekly price model, and 07 for the separate crop-yield model. Notebook 04 includes a cleanup cell for identified old monthly outputs. Review its listed paths before running that cell. The final cells in 03 and 04 ask for the student's own GitHub username, email, and personal access token before committing and pushing; running earlier cells alone does not update GitHub.

**Known rerun issue:** the committed Member 3 notebook searches for a `Crop` column, while the raw weekly workbook names that column `Commodity`. Running Member 3 as committed can create an empty price table. Member 4 currently rebuilds the weekly table from the workbook in an extra cell, which produced the valid committed dataset, but that bypasses Member 3's saved output. Before a clean end-to-end rerun, update Member 3 to accept `Commodity` and have Member 4 read its output without rebuilding it. The committed dataset and model results above are populated; this note concerns reproducibility from the notebooks.

Some files in `Evidence Logs/` still describe the earlier monthly, combined-model experiment. They are historical records and should not be cited as documentation of the current weekly price model. The active model outputs are the `weekly_price_*` files and the yield files listed above.

To run the app locally after cloning the repository:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The repository pins `scikit-learn==1.6.1` because the saved model files were created with that version. Loading them under a different version may fail.


