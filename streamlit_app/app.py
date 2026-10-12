from pathlib import Path

import joblib
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="AgriPlan | Sri Lankan Crop Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #f5f8f4; color: #173026; }
    [data-testid="stHeader"] { background: rgba(245,248,244,0.9); }
    .stApp p, .stApp label, .stApp li,
    .stApp [data-testid="stMarkdownContainer"] { color: #173026; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #0b5d3b; }
    .hero { padding: 1.4rem 1.6rem; border-radius: 18px; color: white;
            background: linear-gradient(120deg, #0b5d3b, #2f8f5b 62%, #74b84a); }
    .hero h1, .hero p { color: white !important; }
    .hero h1 { margin: 0; font-size: 2.25rem; }
    .hero p { margin: .5rem 0 0; opacity: .9; font-size: 1.05rem; }
    .section-label { color: #2f8f5b; font-weight: 700; letter-spacing: .04em;
                     text-transform: uppercase; font-size: .78rem; }
    div[data-testid="stMetric"] { background: white; border: 1px solid #dce8dc;
                                    padding: 1rem; border-radius: 14px; }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"],
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] { color: #173026 !important; }
    .stTabs [data-baseweb="tab"] { color: #24543b !important; }
    .stTabs [aria-selected="true"] { color: #0b5d3b !important; }
    .stButton > button { background: #0b7a4b; color: white !important;
                         border: 0; border-radius: 9px; font-weight: 700; }
    .stButton > button:hover { background: #095c39; color: white !important; }
    [data-testid="stSidebar"] { background: #edf5ed; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span { color: #173026 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

ROOT = Path(__file__).resolve().parents[1]
PRICE_DATA = ROOT / "Preprocessed Datasets" / "03_price_preprocessed.csv"
PRICE_MODEL = ROOT / "weekly_price_model.joblib"
YIELD_DATA = ROOT / "Wijesinghe.D.T.D-Crop Yield Preprocessing" / "wijesinghe_yield_preprocessed_15000plus.csv"
YIELD_MODEL = ROOT / "Wijesinghe.D.T.D-Crop Yield Outputs" / "wijesinghe_yield_model.joblib"


@st.cache_data
def load_price_data():
    return pd.read_csv(PRICE_DATA, parse_dates=["WeekDate"])


@st.cache_data
def load_yield_data():
    return pd.read_csv(YIELD_DATA)


@st.cache_resource
def load_model(path):
    return joblib.load(path)


st.markdown(
    "<div class='hero'><h1>🌱 AgriPlan</h1><p>Evidence-based weekly price and crop-yield planning for Sri Lankan agriculture.</p></div>",
    unsafe_allow_html=True,
)
st.write("")

if not PRICE_DATA.exists() or not PRICE_MODEL.exists():
    st.error("The weekly price dataset or model is missing from the repository.")
    st.stop()

weekly = load_price_data()
price_model = load_model(PRICE_MODEL)
yield_ready = YIELD_DATA.exists() and YIELD_MODEL.exists()
yield_data = load_yield_data() if yield_ready else None

with st.sidebar:
    st.markdown("### Planning inputs")
    st.caption("Choose a crop and enter the latest field or market information.")
    price_crops = sorted(weekly["Crop"].dropna().unique())
    crop = st.selectbox("Crop", price_crops)
    crop_rows = weekly[weekly["Crop"] == crop].sort_values("WeekDate")
    latest = crop_rows.dropna(subset=["PreviousWeekWholesalePrice_RsKg"]).iloc[-1]
    forecast_date = st.date_input("Forecast week", value=latest["WeekDate"].date())
    current_price = st.number_input(
        "Current wholesale price (Rs/kg)", min_value=0.0,
        value=float(latest["WholesalePrice_RsKg"]), step=1.0,
    )
    previous_price = st.number_input(
        "Previous-week price (Rs/kg)", min_value=0.0,
        value=float(latest["PreviousWeekWholesalePrice_RsKg"]), step=1.0,
    )

st.markdown("<div class='section-label'>Decision support dashboard</div>", unsafe_allow_html=True)
st.subheader("Market and yield outlook")
overview_tab, price_tab, yield_tab, data_tab = st.tabs([
    "🏠 Overview", "📈 Weekly price forecast", "🌾 Crop-yield forecast", "📊 Data coverage"
])

with overview_tab:
    st.write("A single view of the latest market coverage and agricultural planning signals.")
    overview_one, overview_two, overview_three, overview_four = st.columns(4)
    overview_one.metric("Weekly price records", f"{len(weekly):,}")
    overview_two.metric("Available crops", f"{weekly['Crop'].nunique():,}")
    overview_three.metric("Yield records", f"{len(yield_data):,}" if yield_ready else "Not generated")
    overview_four.metric("Latest price date", weekly["WeekDate"].max().strftime("%d %b %Y"))
    st.markdown("#### Selected crop price trend")
    trend = crop_rows[["WeekDate", "WholesalePrice_RsKg"]].dropna().set_index("WeekDate")
    st.line_chart(trend, y="WholesalePrice_RsKg", use_container_width=True)
    flow_one, flow_two, flow_three = st.columns(3)
    with flow_one:
        st.markdown("**1 · Select inputs**")
        st.caption("Choose a crop, season, district, hectares, and current market values.")
    with flow_two:
        st.markdown("**2 · Run forecasts**")
        st.caption("Generate weekly price and season-aware yield estimates from trained models.")
    with flow_three:
        st.markdown("**3 · Review evidence**")
        st.caption("Use the forecast, trends, and data coverage to support—not replace—decisions.")

with price_tab:
    st.write("Estimate the next weekly Colombo wholesale price using the current and previous price signals.")
    if st.button("Predict next-week price", type="primary", key="price_button"):
        date = pd.Timestamp(forecast_date)
        features = pd.DataFrame([{
            "Crop": crop,
            "Market": "Colombo and suburbs",
            "Year": date.year,
            "WeekNumber": int(date.isocalendar().week),
            "Month": date.month,
            "WholesalePrice_RsKg": current_price,
            "PreviousWeekWholesalePrice_RsKg": previous_price,
        }])
        prediction = float(price_model.predict(features)[0])
        change = ((prediction - current_price) / current_price * 100) if current_price else None
        one, two, three = st.columns(3)
        one.metric("Predicted next-week price", f"Rs {prediction:,.2f}/kg")
        two.metric("Expected movement", "Unavailable" if change is None else f"{change:+.1f}%")
        three.metric("Forecast crop", crop)
        st.info("Use this as decision-support evidence, not as a guaranteed market price.")

with yield_tab:
    if not yield_ready:
        st.warning("Run the Wijesinghe crop-yield preprocessing notebook once to create the yield dataset and model.")
    else:
        st.write("Estimate yield per hectare and expected production for the selected season and cultivated area.")
        yield_crops = sorted(yield_data["Crop"].dropna().unique())
        yield_crop = st.selectbox("Yield crop", yield_crops, index=yield_crops.index(crop) if crop in yield_crops else 0)
        yield_rows = yield_data[yield_data["Crop"] == yield_crop]
        yield_category = yield_rows["CropCategory"].mode().iloc[0]
        y_one, y_two, y_three = st.columns(3)
        with y_one:
            season = st.selectbox("Season", ["Maha", "Yala", "Total"])
        with y_two:
            hectares = st.number_input("Cultivated area (hectares)", min_value=0.01, value=1.0, step=0.5)
        with y_three:
            yield_year = st.number_input("Production year", min_value=2001, max_value=2100, value=2025, step=1)
        district = st.selectbox("District", sorted(yield_data["District"].dropna().unique()))
        if st.button("Predict crop yield", type="primary", key="yield_button"):
            yield_features = pd.DataFrame([{
                "District": district,
                "Season": season,
                "CropCategory": yield_category,
                "Crop": yield_crop,
                "Year": int(yield_year),
                "Extent": hectares,
            }])
            yield_prediction = max(0.0, float(load_model(YIELD_MODEL).predict(yield_features)[0]))
            expected_production = yield_prediction * hectares
            y_left, y_mid, y_right = st.columns(3)
            y_left.metric("Predicted yield", f"{yield_prediction:,.2f} t/ha")
            y_mid.metric("Estimated production", f"{expected_production:,.2f} t")
            y_right.metric("Season", season)
            st.caption("The estimate uses crop, season, district, year, and cultivated hectares. It is a planning estimate, not a guaranteed harvest result.")

with data_tab:
    data_one, data_two, data_three = st.columns(3)
    data_one.metric("Weekly price records", f"{len(weekly):,}")
    if yield_ready:
        data_two.metric("Prepared yield records", f"{len(yield_data):,}")
        data_three.metric("Yield seasons", f"{yield_data['Season'].nunique():,}")
    st.markdown("#### Recent weekly price observations")
    st.dataframe(weekly.tail(20), use_container_width=True, hide_index=True)
    if yield_ready:
        st.markdown("#### Average yield by season")
        season_chart = yield_data.groupby("Season", as_index=True)["Yield_t_ha"].mean().sort_values(ascending=False)
        st.bar_chart(season_chart, use_container_width=True)
