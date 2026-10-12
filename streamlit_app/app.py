from pathlib import Path

import joblib
import pandas as pd
import streamlit as st


BASE = Path(__file__).resolve().parent
OUT = BASE / "Revised Outputs"


@st.cache_data
def load_data():
    price = pd.read_csv(OUT / "price_next_week_dataset.csv", parse_dates=["Date", "NextWeekStart"])
    yield_data = pd.read_csv(OUT / "yield_dataset.csv", parse_dates=["ForecastDate"])
    return price, yield_data


@st.cache_resource
def load_models():
    return joblib.load(OUT / "price_model.joblib"), joblib.load(OUT / "yield_model.joblib")


st.set_page_config(page_title="Sri Lankan Crop Decision Support", page_icon="🌱", layout="wide")
st.title("Sri Lankan Crop Decision Support")
st.caption("Two evidence-based modules: Colombo next-week wholesale price and district-level crop yield.")

try:
    price_data, yield_data = load_data()
    price_model, yield_model = load_models()
except Exception as exc:
    st.error("The revised datasets or trained models are not available. Run scripts/revised_pipeline.py first.")
    st.exception(exc)
    st.stop()

price_tab, yield_tab = st.tabs(["Colombo next-week price", "Crop yield"])

with price_tab:
    st.subheader("Colombo next-week wholesale price")
    st.info("This is a historical-data-backed forecast. The source data end in 2025, so it is not a live October 2026 market quote.")
    crop = st.selectbox("Vegetable", sorted(price_data["Crop"].unique()), key="price_crop")
    crop_rows = price_data[price_data["Crop"].eq(crop)].sort_values("Date")
    forecast_date = st.selectbox("Forecast observation date", crop_rows["Date"].dt.strftime("%Y-%m-%d").tolist(), index=len(crop_rows) - 1, key="price_date")
    selected = crop_rows[crop_rows["Date"].eq(pd.Timestamp(forecast_date))].iloc[-1]
    price_features = ["Crop", "Market", "Year", "Month", "WeekOfYear", "CurrentPrice_RsKg", "Lag1Price_RsKg", "Lag2Price_RsKg", "Lag3Price_RsKg", "Rolling7Mean_RsKg", "Rolling28Mean_RsKg", "Rolling7Std_RsKg"]
    prediction = float(price_model.predict(pd.DataFrame([selected[price_features]]))[0])
    c1, c2, c3 = st.columns(3)
    c1.metric("Predicted next-week price", f"Rs {prediction:,.2f}/kg")
    c2.metric("Observed price at forecast date", f"Rs {selected['CurrentPrice_RsKg']:,.2f}/kg")
    c3.metric("Target week", selected["NextWeekStart"].strftime("%d %b %Y"))
    st.line_chart(crop_rows.set_index("Date")["CurrentPrice_RsKg"].tail(90))
    st.warning("Use this as a market signal, not a guaranteed price. The model is trained on Colombo/Pettah observations and may not represent every Sri Lankan market.")

with yield_tab:
    st.subheader("District-level crop yield")
    district = st.selectbox("District", sorted(yield_data["District"].unique()), key="yield_district")
    crop_options = sorted(yield_data[yield_data["District"].eq(district)]["Crop"].unique())
    crop = st.selectbox("Crop", crop_options, key="yield_crop")
    subset = yield_data[yield_data["District"].eq(district) & yield_data["Crop"].eq(crop)]
    season = st.selectbox("Season", sorted(subset["Season"].unique()), key="yield_season")
    subset = subset[subset["Season"].eq(season)].sort_values("Year")
    year = st.selectbox("Historical forecast year", subset["Year"].astype(int).tolist(), index=len(subset) - 1, key="yield_year")
    area = st.number_input("Planned cultivated area (hectares)", min_value=0.01, value=1.0, step=0.25)
    selected = subset[subset["Year"].eq(year)].iloc[-1]
    yield_features = ["District", "CropCategory", "Crop", "Season", "Year", "Rainfall_3M_mm", "TempMean_3M_C", "WindSpeed_3M_kmh", "SolarRadiation_3M_MJ_m2", "ET0_3M_mm", "WeatherDays_3M"]
    prediction = max(0.0, float(yield_model.predict(pd.DataFrame([selected[yield_features]]))[0]))
    c1, c2, c3 = st.columns(3)
    c1.metric("Predicted yield", f"{prediction:,.2f} t/ha")
    c2.metric("Expected production", f"{prediction * area:,.2f} tonnes")
    c3.metric("Planning area", f"{area:,.2f} ha")
    st.caption("Yield observations are district-crop-season-year records matched to a three-month pre-forecast weather window. Predictions should support, not replace, agronomic advice.")
