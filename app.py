from pathlib import Path

import pandas as pd
import streamlit as st

from predictor import FEATURES, load_assets, make_forecast_context, run_forecast


BASE_DIR = Path(__file__).resolve().parent


st.set_page_config(page_title="Crop Planning Forecast", page_icon="🌱", layout="wide")


@st.cache_resource(show_spinner="Loading the saved production and price model…")
def get_assets():
    return load_assets(BASE_DIR)


def render_metric(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


def render_workflow() -> None:
    """Render the end-to-end prediction workflow as a compact visual map."""

    st.markdown(
        """
        <style>
        .workflow { margin: 0.5rem 0 1.5rem; font-family: sans-serif; }
        .workflow-title { color: #15351a; font-size: 1.15rem; font-weight: 700; margin-bottom: .65rem; }
        .workflow-node { background: #ffffff; border: 1px solid #b7d3b2; border-radius: 12px; padding: .72rem .85rem; text-align: center; box-shadow: 0 2px 8px rgba(35, 83, 39, .07); min-height: 3.2rem; display: flex; flex-direction: column; justify-content: center; }
        .workflow-node strong { color: #1f5c27; font-size: .95rem; }
        .workflow-node span { color: #506452; font-size: .78rem; margin-top: .18rem; }
        .workflow-node.primary { background: #eaf4e7; border-color: #77ad70; }
        .workflow-node.output { background: #f3f8ef; }
        .workflow-arrow { color: #55904d; font-size: 1.35rem; font-weight: 700; text-align: center; padding: .35rem 0; }
        .workflow-branch { display: grid; grid-template-columns: 1fr 1fr; gap: .7rem; }
        .workflow-data { display: grid; grid-template-columns: repeat(3, 1fr); gap: .7rem; }
        @media (max-width: 700px) { .workflow-data { grid-template-columns: 1fr; } .workflow-branch { grid-template-columns: 1fr; } }
        </style>
        <div class="workflow">
          <div class="workflow-title">How the forecast is produced</div>
          <div class="workflow-node primary"><strong>👨‍🌾 Farmer</strong><span>Chooses crop and planned area</span></div>
          <div class="workflow-arrow">↓</div>
          <div class="workflow-node primary"><strong>Streamlit Web UI</strong><span>Crop · Season · Planned Area</span></div>
          <div class="workflow-arrow">↓</div>
          <div class="workflow-data">
            <div class="workflow-node"><strong>📅 Date / Year</strong><span>Season anchor and 3-month window</span></div>
            <div class="workflow-node"><strong>🌦️ Weather Data</strong><span>Rainfall, temperature, wind, solar, ET0</span></div>
            <div class="workflow-node"><strong>📈 Market Price</strong><span>Previous-month crop price</span></div>
          </div>
          <div class="workflow-arrow">↓</div>
          <div class="workflow-node"><strong>Feature Builder</strong><span>Exact 9-feature model row</span></div>
          <div class="workflow-arrow">↓</div>
          <div class="workflow-node primary"><strong>Saved ML Model</strong><span>Random Forest multi-output pipeline</span></div>
          <div class="workflow-arrow">↓</div>
          <div class="workflow-branch">
            <div class="workflow-node output"><strong>Yield Prediction</strong><span>Predicted tonnes per hectare</span></div>
            <div class="workflow-node output"><strong>Price Prediction</strong><span>Next-month Rs/kg outlook</span></div>
          </div>
          <div class="workflow-arrow">↓</div>
          <div class="workflow-node output"><strong>Expected Production</strong><span>Predicted Yield × Planned Area</span></div>
          <div class="workflow-arrow">↓</div>
          <div class="workflow-node primary"><strong>Recommendation</strong><span>Favourable, mixed or caution outlook</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.title("🌱 Crop Planning Forecast")
st.caption("Yield and next-month wholesale-price decision support from the saved leakage-safe model.")
render_workflow()

try:
    assets = get_assets()
except Exception as exc:  # Keep a corrupt/missing deployment actionable.
    st.error("The saved model or required dataset could not be loaded.")
    st.exception(exc)
    st.stop()

with st.sidebar:
    st.header("Plan a crop")
    crop = st.selectbox("Crop", assets["crops"])
    automatic_context = make_forecast_context()
    season = st.selectbox(
        "Season",
        ["Yala", "Maha"],
        index=["Yala", "Maha"].index(automatic_context.season),
        help="The current date selects the default automatically; you can override it to compare Yala and Maha.",
    )
    context = make_forecast_context(season=season)
    planned_area = st.number_input("Planned Area (hectares)", min_value=0.01, value=1.0, step=0.25)
    run = st.button("Generate forecast", type="primary", use_container_width=True)

st.info(
    f"Season/date logic selected **{context.season} {context.year}** "
    f"with forecast anchor **{context.forecast_date:%d %b %Y}**. "
    f"Weather uses the three complete months from **{context.weather_window_start:%d %b %Y}** "
    f"to **{context.weather_window_end:%d %b %Y}**."
)

if "forecast" not in st.session_state or run:
    try:
        st.session_state.forecast = run_forecast(crop, planned_area, context, assets)
    except Exception as exc:
        st.error("This forecast could not be generated. Check the selected inputs and local data files.")
        st.exception(exc)
        st.stop()

result = st.session_state.forecast
prediction = result["prediction"]
decision = result["recommendation"]
retrieved = result["retrieved"]

st.subheader(f"Forecast for {crop}")
metric_cols = st.columns(4)
with metric_cols[0]:
    render_metric("Predicted yield", f"{decision['yield_t_ha']:.2f} t/ha")
with metric_cols[1]:
    render_metric("Expected production", f"{decision['expected_production_tonnes']:.2f} t")
with metric_cols[2]:
    render_metric("Next-month price", f"Rs {decision['next_month_price']:.2f}/kg")
with metric_cols[3]:
    render_metric("Planned area", f"{planned_area:.2f} ha")

if decision["label"].startswith("Favourable"):
    st.success(decision["label"])
elif decision["label"].startswith("Caution"):
    st.warning(decision["label"])
else:
    st.info(decision["label"])

st.caption(decision["note"])

with st.expander("Automatic-data details", expanded=True):
    st.write(f"Weather retrieval: {retrieved.weather_source}.")
    st.write(f"Previous-price retrieval: {retrieved.price_source}.")
    st.write(f"Previous-month wholesale price used: Rs {retrieved.previous_price:.2f}/kg.")
    st.write("The model row below is the exact nine-feature input passed to the saved pipeline.")
    st.dataframe(result["feature_row"].style.format(precision=3), width="stretch", hide_index=True)

with st.expander("Model and limitation notes"):
    st.write(
        "The model uses national aggregated weather and historical production/market data. "
        "It cannot represent every farm's soil, irrigation, pests, disease, variety or practice. "
        "The price target had weak out-of-sample performance in the supplied test metrics, "
        "so this dashboard supports planning and does not replace farmer or agronomist judgement."
    )
    st.write(f"Training/modelling period in the supplied metadata: {assets['metadata']['common_modelling_period'][0]}–{assets['metadata']['common_modelling_period'][1]}.")
