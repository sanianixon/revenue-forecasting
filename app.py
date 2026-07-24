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

def render_industry_selection():
    if "industry_preview" not in st.session_state:
        st.session_state.industry_preview = None

    # Coming-soon screen
    if st.session_state.industry_preview:
        st.write("")

        left_space, content, right_space = st.columns([1, 2, 1])

        with content:
            st.caption("COMING SOON")

            title_col, back_col = st.columns([3, 1])

            with title_col:
                st.title(st.session_state.industry_preview)

            with back_col:
                st.write("")

                if st.button(
                    "Change industry",
                    width="stretch",
                    key="back_to_industries",
                ):
                    st.session_state.industry_preview = None
                    st.rerun()

            st.write(
                "We’re still building this forecasting workspace. "
                "Telecom is available right now."
            )

            st.image(
                "images/under_construction.gif",
                width="stretch",
            )

        st.stop()

    def render_card(
        status,
        title,
        description,
        button_label,
        key,
        available=False,
    ):
        with st.container(
            border=True,
            height=285,
        ):
            st.caption(status)

            # Fixed title space
            st.markdown(
                (
                    '<div style="min-height: 52px;">'
                    f'<h3 style="margin: 0;">{title}</h3>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            # Fixed description space
            st.markdown(
                (
                    '<div style="min-height: 78px; '
                    'line-height: 1.55;">'
                    f"{description}"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            if st.button(
                button_label,
                type="primary" if available else "secondary",
                width="stretch",
                key=key,
            ):
                if available:
                    st.session_state.selected_industry = "Telecom"
                    st.session_state.current_page = "setup"
                else:
                    st.session_state.industry_preview = title

                st.rerun()

    # Industry-selection screen
    st.write("")

    st.caption("INDIA · INDUSTRY FORECASTING")
    st.title("Pick your industry.")

    st.write(
        "Each workspace is designed around the business drivers "
        "that actually matter for that industry."
    )

    st.write("")

    row_one = st.columns(3, gap="medium")

    with row_one[0]:
        render_card(
            status="AVAILABLE NOW",
            title="Telecom",
            description=(
                "Revenue forecasting using ARPU, subscriber trends "
                "and Indian telecom market intelligence."
            ),
            button_label="Open workspace",
            key="open_telecom",
            available=True,
        )

    with row_one[1]:
        render_card(
            status="COMING SOON",
            title="Aviation",
            description=(
                "Revenue forecasting using passenger demand, fares, "
                "route capacity and operating conditions."
            ),
            button_label="Take a look",
            key="open_aviation",
        )

    with row_one[2]:
        render_card(
            status="COMING SOON",
            title="Retail",
            description=(
                "Sales forecasting using customer demand, pricing, "
                "seasonality and market conditions."
            ),
            button_label="Take a look",
            key="open_retail",
        )

    st.write("")

    row_two = st.columns(3, gap="medium")

    with row_two[0]:
        render_card(
            status="COMING SOON",
            title="OTT & Subscription",
            description=(
                "Subscription forecasting using pricing, customer "
                "growth, engagement and churn."
            ),
            button_label="Take a look",
            key="open_ott",
        )

    with row_two[1]:
        render_card(
            status="COMING SOON",
            title="Banking",
            description=(
                "Revenue forecasting using lending activity, "
                "customer growth and interest-rate movement."
            ),
            button_label="Take a look",
            key="open_banking",
        )

    with row_two[2]:
        render_card(
            status="IN DEVELOPMENT",
            title="More soon",
            description=(
                "Additional industry-specific forecasting "
                "workspaces are currently being explored."
            ),
            button_label="See what’s next",
            key="open_more",
        )

st.set_page_config(
    page_title="AI Business Forecasting Studio",
    layout="wide",
)

apply_global_styles()

if "current_page" not in st.session_state:
    st.session_state.current_page = "setup"

if "selected_industry" not in st.session_state:
    st.session_state.selected_industry = None


# Stop here until an available industry is selected.
if st.session_state.selected_industry is None:
    render_industry_selection()
    st.stop()


st.title("AI Business Forecasting Studio")
st.caption(
    "Forecast telecom revenue, compare models, and review external "
    "market developments in one connected workflow."
)

industry_col, change_col = st.columns([5, 1])

with industry_col:
    st.caption("Industry: Telecom · Market: India")

with change_col:
    if st.button(
        "Change industry",
        width="stretch",
        key="change_industry",
    ):
        st.session_state.selected_industry = None
        st.session_state.industry_preview = None
        st.session_state.current_page = "setup"
        st.rerun()

st.subheader("Company Data")

data_source = st.selectbox(
    "Choose how to provide company data",
    [
        "Airtel",
        "Upload telecom data",
    ],
    format_func=lambda option: (
        "Airtel — built-in verified dataset"
        if option == "Airtel"
        else "Upload another Indian telecom company"
    ),
    key="telecom_data_source",
)

company = "Airtel"

if data_source == "Upload telecom data":
    company = st.text_input(
        "Company name",
        placeholder="For example: Vodafone Idea",
        help=(
            "This name is used to personalise the forecast "
            "and retrieve relevant market news."
        ),
        key="uploaded_company_name",
    ).strip()

    with st.expander("CSV format and requirements"):
        st.write(
            "Upload official historical quarterly data for an "
            "Indian telecom company."
        )

        st.markdown(
            """
**Required columns**

- `Quarter` — Indian financial quarter, such as `Q1 FY23`
- `Revenue` — quarterly revenue in ₹ crore
- `ARPU` — monthly blended ARPU in ₹
- `Customer Base` — end-of-quarter subscribers in millions
            """
        )

        st.code(
            """Quarter,Revenue,ARPU,Customer Base
Q1 FY23,10410.1,128,240.4
Q2 FY23,10614.6,131,234.4
Q3 FY23,10620.6,135,228.6
Q4 FY23,10531.9,135,225.9""",
            language="csv",
        )

        sample_csv = (
            "Quarter,Revenue,ARPU,Customer Base\n"
            "Q1 FY23,10410.1,128,240.4\n"
            "Q2 FY23,10614.6,131,234.4\n"
            "Q3 FY23,10620.6,135,228.6\n"
            "Q4 FY23,10531.9,135,225.9\n"
        )

        st.download_button(
            "Download sample CSV",
            data=sample_csv,
            file_name="telecom_data_template.csv",
            mime="text/csv",
            width="content",
        )

raw_df, dataset_status = load_company_data(data_source)

if (
    data_source == "Upload telecom data"
    and raw_df is not None
    and not company
):
    st.warning(
        "Enter the company name before continuing."
    )
    st.stop()

df, data_error = prepare_company_data(raw_df)

if data_error:
    st.error(data_error)

if df is None or df.empty:
    render_sidebar(
        company=company,
        dataset_status=dataset_status,
        df=df,
    )
    st.info(
        "Select a company with valid data or upload a compatible CSV."
    )
    st.stop()

render_sidebar(
    company=company,
    dataset_status=dataset_status,
    df=df,
)

render_navigation()

comparison_df = pd.DataFrame()
backtest_results = {}
recommended_models = []

if st.session_state.current_page == "results":
    (
        comparison_df,
        backtest_results,
        recommended_models,
    ) = get_model_evaluation(df)

if st.session_state.current_page == "setup":
    render_forecast_workspace(
        df=df,
        comparison_df=comparison_df,
        backtest_results=backtest_results,
        recommended_models=recommended_models,
        mode="setup",
    )

elif st.session_state.current_page == "ai":
    render_external_intelligence(
        df=df,
        company=company,
    )
elif st.session_state.current_page == "results":
    render_forecast_workspace(
        df=df,
        comparison_df=comparison_df,
        backtest_results=backtest_results,
        recommended_models=recommended_models,
        mode="results",
    )