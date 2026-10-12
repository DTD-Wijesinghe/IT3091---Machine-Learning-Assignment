# Crop and Colombo Price Decision Support

This revised IT3091 project contains two separate, leakage-safe regression modules in one Streamlit application:

1. Colombo next-week wholesale price prediction.
2. District-level crop yield prediction.

## Data units and counts

The price dataset uses one crop-date observation from the Colombo/Pettah daily wholesale workbook. The target is the mean wholesale price in the following calendar week. The final dataset contains 39,377 genuine labelled observations.

The yield dataset uses one district-crop-season-year production observation matched to a district weather location and a three-month pre-forecast weather window. The final dataset contains 15,698 genuine labelled observations.

See `Revised Outputs/record_counts.csv` for the auditable processing counts and `Revised Outputs/model_metrics.csv` for the executed model comparisons.

## Reproduce the revised pipeline

From PowerShell, create an environment with Python 3.12 and install `requirements.txt`. Then run:

```powershell
python scripts/revised_pipeline.py `
  --repo . `
  --daily-price "C:\path\to\2018-2025 Daily Wholesale Prices(Colombo).xlsx" `
  --output "Revised Outputs"
```

The script writes both processed CSV datasets, trained pipelines, metadata, metrics, and record-count evidence.

## Run Streamlit

```powershell
streamlit run app.py
```

The price module is historical-data-backed. The supplied daily Colombo workbook ends in 2025, so the app displays a data-freshness warning rather than presenting a historical backtest as a live October 2026 quote.

## Evaluation summary

The revised price model selected Gradient Boosting and achieved test R² of approximately 0.36, outperforming the simple persistence baseline in the executed test. The revised yield model selected Random Forest and achieved test R² of approximately 0.12, also outperforming its median baseline. These results are reported honestly and should not be interpreted as guaranteed commercial forecasts.

The weekly Colombo/suburbs workbook remains a documented source for historical comparison. It is not concatenated with the daily workbook as if the two sources were identical measurements.
