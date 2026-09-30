from pathlib import Path

import streamlit as st

from predictor import load_assets, make_forecast_context, run_forecast


BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Crop Planning Forecast",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource(show_spinner="Loading the saved production and price model…")
def get_assets():
    return load_assets(BASE_DIR)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
        :root { --green:#146b45; --deep:#123b2b; --lime:#d8ef9a; --gold:#f4c95d; --cream:#fffdf6; --line:#d8e5d8; --muted:#60766a; }
        .stApp { background:#f4f7f1; color:var(--deep); font-family:'DM Sans',sans-serif; }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] { display:none; }
        .block-container { max-width:1500px; width:calc(100% - 2rem); padding:1.6rem 1rem 4rem; }
        h1,h2,h3 { font-family:'Plus Jakarta Sans',sans-serif; color:var(--deep); letter-spacing:-.03em; }
        h1 { font-size:clamp(2rem,4vw,3.45rem); line-height:1.05; margin-bottom:.45rem; }
        .hero { background:linear-gradient(115deg,#103b2b 0%,#1c6946 65%,#2b8055 100%); border-radius:28px; padding:2.2rem 2.4rem; display:flex; justify-content:space-between; gap:2rem; align-items:flex-end; margin-bottom:1.35rem; box-shadow:0 14px 30px rgba(16,59,43,.18); overflow:hidden; position:relative; }
        .hero::after { content:'🌾'; position:absolute; right:12%; top:-1.15rem; font-size:8rem; opacity:.12; transform:rotate(-10deg); }
        .hero h1 { color:#fff; }
        .eyebrow { color:var(--lime); font-size:.75rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.7rem; }
        .hero-copy { max-width:720px; position:relative; z-index:1; }
        .hero-copy p { color:#dcefe1; font-size:1.05rem; margin:0; max-width:650px; }
        .hero-badge { background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.32); border-radius:999px; color:#fff; font-weight:700; padding:.7rem 1rem; white-space:nowrap; position:relative; z-index:1; }
        .section-label { color:var(--deep); font-family:'Plus Jakarta Sans',sans-serif; font-size:1.15rem; font-weight:800; letter-spacing:.02em; margin:1.25rem 0 .65rem; }
        .input-card,.result-card { background:var(--cream); border:1px solid var(--line); border-radius:22px; padding:1.35rem 1.45rem .65rem; box-shadow:0 8px 22px rgba(31,70,45,.07); }
        .input-card-title { color:var(--deep); font-family:'Plus Jakarta Sans',sans-serif; font-size:1.3rem; font-weight:700; margin-bottom:.2rem; }
        .input-card-subtitle { color:var(--muted); margin-bottom:1rem; }
        [data-testid="stVerticalBlockBorderWrapper"] { background:var(--cream); border:1px solid var(--line); border-radius:22px; box-shadow:0 8px 22px rgba(31,70,45,.07); }
        [data-testid="stForm"] { border:0; padding:0; }
        [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { color:var(--deep)!important; font-weight:700!important; }
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div, [data-testid="stSelectbox"] div[role="combobox"] { background:#fff!important; border:1px solid #cbdccc!important; border-radius:11px!important; color:var(--deep)!important; }
        [data-testid="stSelectbox"] div[data-baseweb="select"] *, [data-testid="stSelectbox"] div[role="combobox"] * { color:var(--deep)!important; background-color:transparent!important; }
        [data-testid="stSelectbox"] [role="group"] { background:#fff!important; border:1px solid #cbdccc!important; border-radius:11px!important; color:var(--deep)!important; }
        [data-testid="stSelectbox"] input[role="combobox"] { background:#fff!important; color:var(--deep)!important; -webkit-text-fill-color:var(--deep)!important; }
        [data-testid="stSelectbox"] button { background:#fff!important; color:var(--green)!important; border:0!important; }
        [data-testid="stNumberInput"] > div { background:#fff!important; border:1px solid #cbdccc!important; border-radius:11px!important; }
        [data-testid="stNumberInput"] input { background:#fff!important; color:var(--deep)!important; }
        [data-testid="stNumberInput"] button { background:#fff!important; color:var(--green)!important; border-color:#e2ebe1!important; }
        [data-testid="stPopover"] button { color:var(--deep)!important; }
        [data-testid="stExpander"] details > summary, [data-testid="stExpander"] summary { background:#fff!important; border:1px solid var(--line)!important; border-radius:12px!important; color:var(--deep)!important; }
        [data-testid="stExpander"] details > summary *, [data-testid="stExpander"] details > summary p, [data-testid="stExpander"] summary * { color:var(--deep)!important; -webkit-text-fill-color:var(--deep)!important; }
        [data-testid="stExpander"] details[open] > summary { border-radius:12px 12px 0 0!important; }
        [data-testid="stAlert"] { border-radius:14px!important; }
        .feature-table-wrap { overflow-x:auto; border:1px solid var(--line); border-radius:12px; background:#fff; }
        table.feature-table { width:100%; border-collapse:collapse; color:var(--deep); font-size:.82rem; min-width:900px; }
        table.feature-table th { background:#eaf4df; color:#28583b; font-weight:800; text-align:left; padding:.7rem .65rem; border-bottom:1px solid #cfe0c9; white-space:nowrap; }
        table.feature-table td { background:#fff; color:var(--deep); padding:.7rem .65rem; border-bottom:1px solid #edf2e9; white-space:nowrap; }
        table.feature-table tr:last-child td { border-bottom:0; }
        [data-testid="stFormSubmitButton"] button { background:var(--green); border:0; border-radius:12px; color:#fff; font-weight:800; min-height:2.7rem; margin-top:1.72rem; box-shadow:0 5px 0 #0d4c31; }
        [data-testid="stFormSubmitButton"] button:hover { background:#154a2c; color:#fff; }
        [data-testid="stMetric"] { background:#fff; border:1px solid #dfeee2; border-radius:16px; padding:1rem 1.05rem; box-shadow:0 4px 12px rgba(31,70,45,.05); }
        [data-testid="stMetricLabel"] { color:var(--muted); font-weight:600; }
        [data-testid="stMetricValue"] { color:var(--deep); font-size:1.55rem; }
        .context-strip { background:#eef7d9; border:1px solid #d7e8ae; border-radius:14px; padding:.75rem 1rem; color:#41613b; font-size:.92rem; margin:1rem 0 1.25rem; }
        .workflow { display:flex; align-items:stretch; gap:.5rem; margin:0 0 1.35rem; overflow-x:auto; padding:.15rem .1rem .6rem; scrollbar-width:thin; }
        .workflow-step { min-width:150px; flex:1; background:#fff; border:1px solid var(--line); border-radius:15px; padding:.72rem .7rem; text-align:center; position:relative; box-shadow:0 4px 12px rgba(31,70,45,.04); }
        .workflow-step:not(:last-child)::after { content:'›'; position:absolute; right:-.55rem; top:.78rem; color:#8daa93; font-size:1.5rem; font-weight:800; z-index:2; }
        .workflow-step .icon { font-size:1.15rem; display:block; margin-bottom:.18rem; }
        .workflow-step strong { color:var(--deep); display:block; font-size:.83rem; }
        .workflow-step span { color:var(--muted); display:block; font-size:.7rem; margin-top:.18rem; }
        .recommendation { border-radius:16px; padding:1rem 1.1rem; margin:1rem 0; background:#eef8f0; border:1px solid #cfe7d4; color:#1e5b35; font-weight:700; }
        .footer-note { color:#789083; font-size:.78rem; text-align:center; margin-top:2.5rem; }
        @media (max-width:800px) { .block-container { width:100%; padding:1rem .8rem 3rem; } .hero { display:block; border-radius:20px; padding:1.5rem 1.25rem; } .hero-badge { display:inline-block; margin-top:1rem; } .workflow { gap:.45rem; } .workflow-step { min-width:132px; } .workflow-step:not(:last-child)::after { content:'›'; right:-.5rem; top:.78rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_workflow() -> None:
    st.markdown(
        """
        <div class="workflow">
          <div class="workflow-step"><span class="icon">👨‍🌾</span><strong>Plan</strong><span>Choose crop & area</span></div>
          <div class="workflow-step"><span class="icon">🌦️</span><strong>Auto data</strong><span>Weather & market</span></div>
          <div class="workflow-step"><span class="icon">🧮</span><strong>Build features</strong><span>Exact 9-feature row</span></div>
          <div class="workflow-step"><span class="icon">🤖</span><strong>Predict</strong><span>Yield & price</span></div>
          <div class="workflow-step"><span class="icon">✅</span><strong>Decide</strong><span>Production & advice</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


inject_styles()
st.markdown(
    """
    <div class="hero">
      <div class="hero-copy">
        <div class="eyebrow">Smart farming decision support</div>
        <h1>Plan your next crop<br>with more confidence.</h1>
        <p>Estimate yield, expected production and next-month price outlook using your crop plan and automatically matched historical data.</p>
      </div>
      <div class="hero-badge">🌱 Leakage-safe ML model</div>
    </div>
    """,
    unsafe_allow_html=True,
)
render_workflow()

try:
    assets = get_assets()
except Exception as exc:
    st.error("The saved model or required dataset could not be loaded.")
    st.exception(exc)
    st.stop()

automatic_context = make_forecast_context()
st.markdown('<div class="section-label">Start a forecast</div>', unsafe_allow_html=True)
with st.container(border=True):
    st.markdown('<div class="input-card-title">Tell us about your planting plan</div><div class="input-card-subtitle">The remaining weather and price inputs are retrieved automatically.</div>', unsafe_allow_html=True)
    with st.form("forecast_form"):
        input_cols = st.columns([1.35, 1, 1, .9], gap="medium")
        with input_cols[0]:
            crop = st.selectbox("Crop", assets["crops"])
        with input_cols[1]:
            season = st.selectbox(
                "Season", ["Yala", "Maha"],
                index=["Yala", "Maha"].index(automatic_context.season),
                help="The current date sets the default. You can compare either Yala or Maha.",
            )
        with input_cols[2]:
            planned_area = st.number_input("Planned area (hectares)", min_value=0.01, value=1.0, step=0.25)
        with input_cols[3]:
            run = st.form_submit_button("Generate forecast", type="primary", use_container_width=True)

context = make_forecast_context(season=season)
st.markdown(
    f'<div class="context-strip">📅 Forecast set for <strong>{context.season} {context.year}</strong> · Anchor date <strong>{context.forecast_date:%d %b %Y}</strong> · Weather window <strong>{context.weather_window_start:%d %b}–{context.weather_window_end:%d %b %Y}</strong></div>',
    unsafe_allow_html=True,
)

if "forecast" not in st.session_state or run:
    try:
        st.session_state.forecast = run_forecast(crop, planned_area, context, assets)
        st.session_state.forecast_crop = crop
        st.session_state.forecast_area = planned_area
    except Exception as exc:
        st.error("This forecast could not be generated. Check the selected inputs and local data files.")
        st.exception(exc)
        st.stop()

result = st.session_state.forecast
decision = result["recommendation"]
retrieved = result["retrieved"]
forecast_crop = st.session_state.get("forecast_crop", crop)
forecast_area = st.session_state.get("forecast_area", planned_area)

st.markdown('<div class="section-label">Your forecast</div>', unsafe_allow_html=True)
st.markdown(f'<div class="result-card"><div class="input-card-title">{forecast_crop} · {result["context"].season} {result["context"].year}</div><div class="input-card-subtitle">A practical snapshot for {forecast_area:.2f} hectares</div>', unsafe_allow_html=True)
metric_cols = st.columns(4, gap="medium")
with metric_cols[0]:
    render_metric("Predicted yield", f"{decision['yield_t_ha']:.2f} t/ha")
with metric_cols[1]:
    render_metric("Expected production", f"{decision['expected_production_tonnes']:.2f} t")
with metric_cols[2]:
    render_metric("Next-month price", f"Rs {decision['next_month_price']:.2f}/kg")
with metric_cols[3]:
    render_metric("Planned area", f"{forecast_area:.2f} ha")

if decision["label"].startswith("Favourable"):
    st.markdown(f'<div class="recommendation">✅ {decision["label"]}</div>', unsafe_allow_html=True)
elif decision["label"].startswith("Caution"):
    st.warning(decision["label"])
else:
    st.info(decision["label"])
st.caption(decision["note"])
st.markdown('</div>', unsafe_allow_html=True)

details_col, notes_col = st.columns(2, gap="large")
with details_col:
    with st.expander("Automatic data details", expanded=True):
        st.write(f"Weather retrieval: {retrieved.weather_source}.")
        st.write(f"Previous-price retrieval: {retrieved.price_source}.")
        st.write(f"Previous-month wholesale price used: Rs {retrieved.previous_price:.2f}/kg.")
with notes_col:
    with st.expander("Model and limitation notes"):
        st.write("The model uses national aggregated weather and historical production/market data. It cannot represent every farm's soil, irrigation, pests, disease, variety or practice.")
        st.write("Price performance was weak out of sample, so use this dashboard alongside local farm and market knowledge.")

with st.expander("View the exact 9-feature model row"):
    feature_display = result["feature_row"].copy()
    numeric_columns = feature_display.select_dtypes(include="number").columns
    feature_display[numeric_columns] = feature_display[numeric_columns].round(3)
    feature_html = feature_display.to_html(index=False, classes="feature-table", border=0)
    st.markdown(f'<div class="feature-table-wrap">{feature_html}</div>', unsafe_allow_html=True)

st.markdown('<div class="footer-note">Built for practical crop planning · Always validate recommendations with local conditions.</div>', unsafe_allow_html=True)
