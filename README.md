# Crop Planning Forecast

Streamlit dashboard built around the supplied `final_multioutput_model.joblib` artifact.

## Run locally

In PowerShell, activate the project environment before running Streamlit:

```powershell
cd "C:\Users\D.T.D.Wijesinghe\Documents\Codex\2026-09-21\17-build-it-in-this-order\repo"
.venv\Scripts\Activate.ps1
streamlit run app.py
```

If `.venv` does not exist yet, create it with Python 3.12 and install the dependencies:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Running `streamlit run app.py` before activating `.venv` can produce `'streamlit' is not recognized` because Streamlit is not installed globally.

The saved model was serialized with scikit-learn 1.6.1, so the requirements file pins that version for reliable loading.

## Push the app to GitHub

The working folder was created from a ZIP download, so it has no `.git` history. The safest way to publish the changes is to clone the existing repository and copy the app files into that clone:

```powershell
cd "C:\Users\D.T.D.Wijesinghe\Documents\Codex\2026-09-21\17-build-it-in-this-order"
git clone https://github.com/DTD-Wijesinghe/IT3091---Machine-Learning-Assignment.git repo-publish
Copy-Item "repo\app.py","repo\predictor.py","repo\test_predictor.py","repo\requirements.txt","repo\README.md","repo\.gitignore" "repo-publish" -Force
New-Item -ItemType Directory -Force "repo-publish\.streamlit" | Out-Null
Copy-Item "repo\.streamlit\config.toml" "repo-publish\.streamlit\config.toml" -Force
cd repo-publish
git add app.py predictor.py test_predictor.py requirements.txt README.md .gitignore .streamlit/config.toml
git commit -m "Add crop planning Streamlit dashboard"
git push origin main
```

The existing repository already contains the model and preprocessed datasets, so they do not need to be copied again.

## Deploy on Streamlit Community Cloud

1. Open [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **Create app** and choose `DTD-Wijesinghe/IT3091---Machine-Learning-Assignment`.
3. Select branch `main` and entrypoint file `app.py`.
4. In **Advanced settings**, select Python 3.12, then deploy.

Community Cloud reads `requirements.txt` from the repository and keeps the model/data files available beside `app.py`. Future pushes to `main` trigger an app update.

## Implementation sequence

The dashboard follows the requested sequence: Crop, Season, and Planned Area are the only user inputs. Season defaults automatically from today's date (Yala in the Yala window and Maha in the Maha window), while both Yala and Maha remain available for comparison. Crops come from the modelling dataset; historical weather and previous price are retrieved from the saved preprocessed tables; the exact nine-feature row is built before prediction; expected production and transparent recommendation logic are shown with automatic-data details and error handling.

For years outside the supplied historical weather period, the app uses the same-season historical median and labels that fallback in the details panel. Known historical rows use exact year/season weather and matching-month crop price history.

## Smoke test

```powershell
$env:PYTHONPATH = "."
python test_predictor.py
```
