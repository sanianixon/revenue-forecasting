import pandas as pd
import streamlit as st

from data_loader import load_company_data, prepare_company_data
from models.backtesting import build_model_comparison
from ui.external_intelligence import render_external_intelligence
from ui.forecast_workspace import render_forecast_workspace
from ui.navigation import render_navigation
from ui.sidebar import render_sidebar
from ui.styles import apply_global_styles


@st.cache_data(show_spinner="Evaluating forecasting models...")
def get_model_evaluation(data: pd.DataFrame):
    return build_model_comparison(data)


st.set_page_config(
    page_title="AI Business Forecasting Studio",
    layout="wide",
)

apply_global_styles()

if "current_page" not in st.session_state:
    st.session_state.current_page = "setup"

st.title("AI Business Forecasting Studio")
st.caption(
    "Forecast subscription revenue, compare models, and review external "
    "market developments in one connected workflow."
)

company = st.selectbox(
    "Company",
    ["Airtel", "Jio", "Custom Company"],
    key="company_selector",
)

raw_df, dataset_status = load_company_data(company)
df, data_error = prepare_company_data(raw_df)

if data_error:
    st.error(data_error)

if df is None or df.empty:
    render_sidebar(company=company, dataset_status=dataset_status, df=df)
    st.info("Select a company with valid data or upload a compatible CSV.")
    st.stop()

render_sidebar(company=company, dataset_status=dataset_status, df=df)
render_navigation()

comparison_df = pd.DataFrame()
backtest_results = {}
recommended_models = []

if st.session_state.current_page == "results":
    comparison_df, backtest_results, recommended_models = get_model_evaluation(df)

if st.session_state.current_page == "setup":
    render_forecast_workspace(
        df=df,
        comparison_df=comparison_df,
        backtest_results=backtest_results,
        recommended_models=recommended_models,
        mode="setup",
    )
elif st.session_state.current_page == "ai":
    render_external_intelligence(df=df)
elif st.session_state.current_page == "results":
    render_forecast_workspace(
        df=df,
        comparison_df=comparison_df,
        backtest_results=backtest_results,
        recommended_models=recommended_models,
        mode="results",
    )