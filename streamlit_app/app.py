from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import joblib
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="AgriPlan | Sri Lankan Crop Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background: #f5f8f4; color: #173026; }
    [data-testid="stHeader"] { background: rgba(245,248,244,0.9); }
    [data-testid="stAppViewContainer"] { background: #f5f8f4; }
    [data-testid="stMainBlockContainer"] { max-width: 1380px; padding-top: 2rem; }
    .stApp p, .stApp label, .stApp li,
    .stApp [data-testid="stMarkdownContainer"] { color: #173026; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #0b5d3b; }
    .hero { margin-top: 2.2rem; padding: 1.55rem 1.7rem; border-radius: 22px; color: white;
            background: linear-gradient(120deg, #075936, #258b58 62%, #78bd4f);
            border: 1px solid rgba(255,255,255,.35);
            box-shadow: 0 14px 32px rgba(21, 91, 52, .18); }
    .hero h1, .hero p { color: white !important; }
    .hero h1 { margin: 0; font-size: 2.25rem; }
    .hero p { margin: .5rem 0 0; opacity: .9; font-size: 1.05rem; }
    .section-label { color: #2f8f5b; font-weight: 700; letter-spacing: .04em;
                     text-transform: uppercase; font-size: .78rem; }
    div[data-testid="stMetric"] { background: rgba(255,255,255,.92); border: 1px solid #d4e4d7;
                                    padding: 1rem; border-radius: 16px;
                                    box-shadow: 0 5px 16px rgba(32, 78, 48, .07); }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"],
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] { color: #173026 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: #eaf3eb;
                                          padding: 7px; border: 1px solid #d3e4d6;
                                          border-radius: 15px; }
    .stTabs [data-baseweb="tab"] { color: #24543b !important; border-radius: 10px;
                                    padding: 9px 15px; font-weight: 600; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: white !important;
                                    background: #0b7a4b; }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stButton > button { background: #0b7a4b; color: white !important;
                         border: 1px solid #075d39; border-radius: 11px; font-weight: 700;
                         box-shadow: 0 5px 12px rgba(11,122,75,.18); }
    .stButton > button:hover { background: #095c39; color: white !important;
                               border-color: #06472d; transform: translateY(-1px); }
    [data-baseweb="select"] > div, [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input { background: #ffffff; color: #173026;
                                         border: 1px solid #c8dccd; border-radius: 10px; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #eaf5eb, #f5f8f4);
                                 border-right: 1px solid #d3e4d6; }
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
LEAFY_BUNDLE_CROPS = {"GOTUKOLA", "KANKUN", "MUKUNUWENNA"}


def price_unit(crop_name):
    return "Rs/bundle" if crop_name in LEAFY_BUNDLE_CROPS else "Rs/kg"


def price_quantity(crop_name):
    return "bundle" if crop_name in LEAFY_BUNDLE_CROPS else "kg"


def file_version(path):
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


@st.cache_data
def load_price_data(version):
    return pd.read_csv(PRICE_DATA, parse_dates=["WeekDate"])


@st.cache_data
def load_yield_data(version):
    return pd.read_csv(YIELD_DATA)


@st.cache_resource
def load_model(path, version):
    return joblib.load(path)


st.markdown(
    "<div class='hero'><h1>🌱 AgriPlan</h1><p>Evidence-based weekly price and crop-yield planning for Sri Lankan agriculture.</p></div>",
    unsafe_allow_html=True,
)
st.write("")

if not PRICE_DATA.exists() or not PRICE_MODEL.exists():
    st.error("The weekly price dataset or model is missing from the repository.")
    st.stop()

weekly = load_price_data(file_version(PRICE_DATA))
if weekly.empty or weekly["WeekDate"].isna().all():
    st.error("The weekly price dataset has no valid dated observations.")
    st.stop()
price_model = load_model(PRICE_MODEL, file_version(PRICE_MODEL))
yield_ready = YIELD_DATA.exists() and YIELD_MODEL.exists()
yield_data = load_yield_data(file_version(YIELD_DATA)) if yield_ready else None

price_crops = sorted(weekly["Crop"].dropna().unique())
if not price_crops:
    st.error("The weekly price dataset has no crops to forecast.")
    st.stop()
default_crop = price_crops[0]
latest_price_date = weekly["WeekDate"].max().date()
today = datetime.now(ZoneInfo("Asia/Colombo")).date()
current_week = today - timedelta(days=today.weekday())
price_data_is_old = (today - latest_price_date).days > 14

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
    overview_four.metric("Latest price date", latest_price_date.strftime("%d %b %Y"))
    if price_data_is_old:
        st.warning(
            f"The stored prices end on {latest_price_date:%d %b %Y}. "
            "For a current forecast, enter recent Colombo wholesale prices yourself."
        )
    st.markdown("#### Selected crop price trend")
    overview_crop = st.selectbox(
        "Select crop for price trend",
        price_crops,
        index=price_crops.index(default_crop),
        key="overview_trend_crop",
    )
    overview_crop_rows = weekly[weekly["Crop"] == overview_crop].sort_values("WeekDate")
    trend_label = f"Wholesale price ({price_unit(overview_crop)})"
    trend = (
        overview_crop_rows[["WeekDate", "WholesalePrice_RsKg"]]
        .dropna()
        .set_index("WeekDate")
        .rename(columns={"WholesalePrice_RsKg": trend_label})
    )
    st.line_chart(trend, y=trend_label, width="stretch")
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
    crop = st.selectbox("Forecast crop", price_crops, index=price_crops.index(default_crop), key="forecast_crop")
    selected_crop_rows = weekly[weekly["Crop"] == crop].sort_values("WeekDate")
    available_rows = selected_crop_rows.dropna(subset=["PreviousWeekWholesalePrice_RsKg"])
    if available_rows.empty:
        st.error("This crop needs at least two recorded weeks for a price forecast.")
        st.stop()
    latest = available_rows.iloc[-1]
    unit = price_unit(crop)
    quantity = price_quantity(crop)
    st.caption(f"Last recorded price for {crop}: {latest['WeekDate']:%d %b %Y} ({unit}).")
    scenario = st.radio(
        "Price inputs",
        ["Current market prices", "Historical example"],
        horizontal=True,
        key="price_scenario",
    )
    historical = scenario == "Historical example"
    if not historical and price_data_is_old:
        st.warning("Enter current and previous-week prices from the same Colombo wholesale market before forecasting.")
    input_one, input_two, input_three = st.columns(3)
    with input_one:
        forecast_date = st.date_input(
            "Observed price week", value=latest["WeekDate"].date() if historical else current_week,
            key=f"forecast_week_{scenario}_{crop}",
        )
    with input_two:
        current_price = st.number_input(
            f"Current wholesale price ({unit})", min_value=0.0,
            value=float(latest["WholesalePrice_RsKg"]) if historical else 0.0,
            step=1.0, key=f"current_price_{scenario}_{crop}",
        )
    with input_three:
        previous_price = st.number_input(
            f"Previous-week price ({unit})", min_value=0.0,
            value=float(latest["PreviousWeekWholesalePrice_RsKg"]) if historical else 0.0,
            step=1.0, key=f"previous_price_{scenario}_{crop}",
        )
    st.caption("Training pairs use the next recorded price; a missing week can make that interval longer than seven days.")
    if st.button("Predict next-week price", type="primary", key="price_button"):
        if current_price <= 0 or previous_price <= 0:
            st.error("Enter both the current and previous-week wholesale prices above zero.")
        else:
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
            change = (prediction - current_price) / current_price * 100
            one, two, three = st.columns(3)
            one.metric("Predicted next-week price", f"Rs {prediction:,.2f}/{quantity}")
            two.metric("Expected movement", f"{change:+.1f}%")
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
        latest_yield_year = int(pd.to_numeric(yield_data["Year"], errors="coerce").max())
        if yield_year > latest_yield_year:
            st.warning(f"The yield records end in {latest_yield_year}; a later-year estimate is an extrapolation.")
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
            yield_prediction = max(0.0, float(load_model(YIELD_MODEL, file_version(YIELD_MODEL)).predict(yield_features)[0]))
            expected_production = yield_prediction * hectares
            y_left, y_mid, y_right = st.columns(3)
            y_left.metric("Predicted yield", f"{yield_prediction:,.2f} t/ha")
            y_mid.metric("Estimated production", f"{expected_production:,.2f} t")
            y_right.metric("Season", season)
            st.caption("The estimate uses crop, season, district, year, and cultivated hectares. It is a planning estimate, not a guaranteed harvest result.")

with data_tab:
    st.markdown("#### Recent weekly price observations")
    data_crop = st.selectbox(
        "Select crop to view price records",
        ["All crops", *price_crops],
        key="data_crop",
    )
    crop_records = weekly if data_crop == "All crops" else weekly[weekly["Crop"] == data_crop]
    latest_crop_date = crop_records["WeekDate"].max()
    data_one, data_two, data_three, data_four = st.columns(4)
    data_one.metric("All weekly price records", f"{len(weekly):,}")
    data_two.metric("Selected price records", f"{len(crop_records):,}")
    data_three.metric("Latest selected price date", latest_crop_date.strftime("%d %b %Y"))
    data_four.metric("Prepared yield records", f"{len(yield_data):,}" if yield_ready else "Not generated")
    recent = (
        crop_records
        .sort_values(["WeekDate", "Crop"], ascending=[False, True])
        .head(20)
        [["WeekDate", "Crop", "Market", "WholesalePrice_RsKg",
          "PreviousWeekWholesalePrice_RsKg", "NextWeekWholesalePrice_RsKg"]]
        .copy()
    )
    recent.insert(3, "Price unit", recent["Crop"].map(price_unit))
    recent["WeekDate"] = recent["WeekDate"].dt.strftime("%d %b %Y")
    recent = recent.rename(columns={
        "WeekDate": "Observed week",
        "WholesalePrice_RsKg": "Observed price",
        "PreviousWeekWholesalePrice_RsKg": "Previous recorded price",
        "NextWeekWholesalePrice_RsKg": "Following recorded price",
    })
    st.caption("Showing the 20 newest stored observations for the selected crop or all crops. Some leafy vegetables are priced per bundle.")
    st.dataframe(recent, width="stretch", hide_index=True)
    if yield_ready:
        st.markdown("#### Average yield by season")
        season_chart = yield_data.groupby("Season", as_index=True)["Yield_t_ha"].mean().sort_values(ascending=False)
        st.bar_chart(season_chart, width="stretch")
