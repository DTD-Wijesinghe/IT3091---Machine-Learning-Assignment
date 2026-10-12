from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sri Lankan Vegetable Planning", page_icon="🌱", layout="wide")
st.title("Sri Lankan Vegetable Planning")
st.write("Use the trained project outputs to review next-week Colombo wholesale price signals and crop-yield planning evidence.")

ROOT = Path(__file__).resolve().parents[1]
PREPROCESSED = ROOT / "Preprocessed Datasets"
WEEKLY_DATA = PREPROCESSED / "03_price_preprocessed.csv"
WEEKLY_MODEL = ROOT / "weekly_price_model.joblib"

if not WEEKLY_DATA.exists() or not WEEKLY_MODEL.exists():
    st.warning("Run the four notebooks in order before using the application. The weekly price dataset and model are created by Members 3 and 4.")
    st.stop()

weekly = pd.read_csv(WEEKLY_DATA, parse_dates=["WeekDate"])
model = joblib.load(WEEKLY_MODEL)

st.sidebar.header("Price inputs")
crops = sorted(weekly["Crop"].dropna().unique())
crop = st.sidebar.selectbox("Crop", crops)
crop_rows = weekly[weekly["Crop"] == crop].sort_values("WeekDate")
latest = crop_rows.dropna(subset=["PreviousWeekWholesalePrice_RsKg"]).iloc[-1]

week_date = st.sidebar.date_input("Forecast week", value=latest["WeekDate"].date())
week_date = pd.Timestamp(week_date)
current_price = st.sidebar.number_input("Current wholesale price Rs/kg", min_value=0.0, value=float(latest["WholesalePrice_RsKg"]), step=1.0)
previous_price = st.sidebar.number_input("Previous-week wholesale price Rs/kg", min_value=0.0, value=float(latest["PreviousWeekWholesalePrice_RsKg"]), step=1.0)

features = pd.DataFrame([{
    "Crop": crop,
    "Market": "Colombo and suburbs",
    "Year": week_date.year,
    "WeekNumber": int(week_date.isocalendar().week),
    "Month": week_date.month,
    "WholesalePrice_RsKg": current_price,
    "PreviousWeekWholesalePrice_RsKg": previous_price,
}])

if st.button("Predict next-week price", type="primary"):
    prediction = float(model.predict(features)[0])
    change = ((prediction - current_price) / current_price * 100) if current_price else None
    left, right = st.columns(2)
    left.metric("Predicted next-week wholesale price", f"Rs {prediction:,.2f}/kg")
    right.metric("Change from current price", "Not available" if change is None else f"{change:+.1f}%")
    st.caption("This is decision-support evidence, not a guaranteed market price. Check current local market information before making a production decision.")

st.subheader("Weekly source coverage")
st.write(f"The prepared weekly table contains {len(weekly):,} usable crop-week records.")
st.dataframe(weekly.tail(20), use_container_width=True)

