import re
import streamlit as st
import pandas as pd
from sklearn.linear_model import Ridge
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Subscription Revenue Forecasting",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }

    div[data-testid="stMetric"] {
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 14px 16px;
        background: #ffffff;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 46px;
        font-weight: 600;
    }

    .section-copy {
        color: #6b7280;
        margin-top: -8px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
<style>

.block-container {
    padding-top: 1.6rem;
    max-width: 1250px;
}

section[data-testid="stSidebar"]{
    background-color:#F8FAFC;
}

div[data-testid="stMetric"]{
    background:white;
    border:1px solid #E5E7EB;
    border-left:5px solid #2563EB;
    border-radius:14px;
    padding:18px;
    box-shadow:0 1px 6px rgba(0,0,0,0.05);
}

div.stButton > button{
    width:100%;
    background:#2563EB;
    color:white;
    border:none;
    border-radius:10px;
    height:46px;
    font-weight:600;
}

div.stButton > button:hover{
    background:#1D4ED8;
}

</style>
""", unsafe_allow_html=True)

st.title("Subscription Revenue Forecasting")
st.markdown(
    """
    <div class="section-copy">
        Forecast subscription revenue using historical company performance,
        recent ARPU and customer growth, and Ridge Regression.
    </div>
    """,
    unsafe_allow_html=True,
)


def quarter_to_number(quarter_text):
    match = re.search(r"Q([1-4])\s*FY(\d{2})", str(quarter_text))

    if not match:
        return None

    quarter = int(match.group(1))
    year = int(match.group(2))

    return ((year - 19) * 4) + quarter


def load_company_data(company):
    if company == "Airtel":
        return pd.read_csv(
            "data/airtel_auto_training_data.csv"
        ), "Automated"

    if company == "Jio":
        return pd.read_csv(
            "data/jio_data.csv"
        ), "Manual"

    uploaded_file = st.file_uploader(
        "Upload Company CSV",
        type=["csv"],
        help=(
            "Required columns: Quarter, Revenue, ARPU, "
            "and Customer Base."
        ),
    )

    if uploaded_file is not None:
        return pd.read_csv(uploaded_file), "Uploaded"

    return None, None


def forecast_using_recent_growth(
    df,
    column,
    target_quarter_no,
    periods=4,
):
    temp = (
        df.sort_values("Quarter No")
        .tail(periods + 1)
        .copy()
    )

    latest_value = temp[column].iloc[-1]
    latest_quarter_no = temp["Quarter No"].iloc[-1]
    average_change = temp[column].diff().dropna().mean()

    quarters_ahead = (
        target_quarter_no - latest_quarter_no
    )

    return latest_value + (
        average_change * quarters_ahead
    )


company = st.selectbox(
    "Company",
    ["Airtel", "Jio", "Custom Company"],
)

df, dataset_status = load_company_data(company)

if df is not None:
    df = df.copy()

    required_columns = {
        "Quarter",
        "Revenue",
        "ARPU",
        "Customer Base",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        st.error(
            "The dataset is missing: "
            + ", ".join(sorted(missing_columns))
        )
        df = None

if df is not None:
    if "Quarter No" not in df.columns:
        df["Quarter No"] = df["Quarter"].apply(
            quarter_to_number
        )

    df = df.dropna(
        subset=[
            "Quarter No",
            "Revenue",
            "ARPU",
            "Customer Base",
        ]
    )

    df = df[
        df["Quarter"] != "Q4 FY19"
    ]

    df = df.sort_values(
        "Quarter No"
    ).reset_index(drop=True)

    latest_quarter = (
        df.iloc[-1]["Quarter"]
        if not df.empty
        else "N/A"
    )
else:
    latest_quarter = "N/A"


with st.sidebar:
    st.header("Model Information")
    st.write(f"**Company:** {company}")

    if df is not None and not df.empty:
        st.write(f"**Dataset:** {dataset_status}")
        st.write(
            f"**Training Samples:** {len(df)}"
        )
        st.write(
            f"**Latest Quarter:** {latest_quarter}"
        )
        st.write("**Algorithm:** Ridge Regression")

        if df is not None and not df.empty:
            model_df_sidebar = df.copy()
            model_df_sidebar["Revenue Driver"] = (
                model_df_sidebar["ARPU"]
                * model_df_sidebar["Customer Base"]
            )

            sidebar_X = model_df_sidebar[["Revenue Driver"]]
            sidebar_y = model_df_sidebar["Revenue"]

            sidebar_model = Ridge(alpha=1.0)
            sidebar_model.fit(sidebar_X, sidebar_y)

            sidebar_r2 = sidebar_model.score(
                sidebar_X,
                sidebar_y
            )

            st.write(f"**R² Score:** {sidebar_r2:.3f}")
            st.success("Ready")
    else:
        st.info("Upload a valid CSV to begin.")


if df is not None and not df.empty:
    latest_row = df.iloc[-1]

    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "Latest Revenue",
        f"₹ {latest_row['Revenue']:,.0f} Cr",
    )

    k2.metric(
        "Latest ARPU",
        f"₹ {latest_row['ARPU']:.0f}",
    )

    k3.metric(
        "Customer Base",
        f"{latest_row['Customer Base']:.1f} Mn",
    )

    k4.metric(
        "Latest Quarter",
        latest_quarter,
    )

st.divider()

st.subheader("Forecast Setup")

setup_left, setup_right = st.columns(2)

with setup_left:
    forecast_quarter = st.selectbox(
        "Forecast Quarter",
        ["Q1", "Q2", "Q3", "Q4"],
    )

    forecast_year = st.number_input(
        "Financial Year",
        min_value=2026,
        max_value=2035,
        value=2027,
        step=1,
    )

with setup_right:
    inflation = st.number_input(
        "Expected Inflation (%)",
        min_value=0.0,
        max_value=20.0,
        value=2.8,
        step=0.1,
    )

    target_period = (
        f"{forecast_quarter} "
        f"FY{str(forecast_year)[-2:]}"
    )

    target_quarter_no = quarter_to_number(
        target_period
    )

    q2_fy25_no = quarter_to_number(
        "Q2 FY25"
    )

    auto_tariff = (
        1
        if target_quarter_no > q2_fy25_no
        else 0
    )

    use_tariff = st.toggle(
        "Apply tariff hike impact",
        value=bool(auto_tariff),
        help=(
            "Enabled by default for quarters "
            "after Q2 FY25."
        ),
    )

    tariff = 1 if use_tariff else 0


if df is None or df.empty:
    st.warning(
        "Please select a company with valid data "
        "or upload a compatible CSV."
    )

else:
    generate_forecast = st.button(
        "Generate Forecast",
        type="primary",
    )

    if generate_forecast:
        predicted_arpu = forecast_using_recent_growth(
            df,
            "ARPU",
            target_quarter_no,
        )

        predicted_customers = forecast_using_recent_growth(
            df,
            "Customer Base",
            target_quarter_no,
        )

        model_df = df.copy()

        model_df["Revenue Driver"] = (
            model_df["ARPU"]
            * model_df["Customer Base"]
        )

        X = model_df[["Revenue Driver"]]
        y = model_df["Revenue"]

        revenue_model = Ridge(alpha=1.0)
        revenue_model.fit(X, y)

        predicted_driver = (
            predicted_arpu
            * predicted_customers
        )

        input_data = pd.DataFrame(
            {
                "Revenue Driver": [
                    predicted_driver
                ]
            }
        )

        base_revenue = revenue_model.predict(
            input_data
        )[0]

        predicted_revenue = (
            base_revenue
            - (596.87 * inflation)
            + (1366.22 * tariff)
        )

        # Approximate uncertainty range from historical residuals
        historical_predictions = revenue_model.predict(X)
        residuals = y - historical_predictions
        rmse = (residuals.pow(2).mean()) ** 0.5

        lower_bound = predicted_revenue - (1.96 * rmse)
        upper_bound = predicted_revenue + (1.96 * rmse)

        # Compare forecast with latest actual quarter
        latest_actual_revenue = model_df.iloc[-1]["Revenue"]
        latest_actual_quarter = model_df.iloc[-1]["Quarter"]

        revenue_change = (
            predicted_revenue
            - latest_actual_revenue
        )

        revenue_change_percent = (
            revenue_change
            / latest_actual_revenue
        ) * 100

        change_direction = (
            "Increase"
            if revenue_change >= 0
            else "Decrease"
        )

        change_symbol = (
            "+"
            if revenue_change >= 0
            else ""
        )

        st.divider()
        st.subheader("Forecast Result")

        r1, r2, r3, r4 = st.columns(4)

        r1.metric(
            "Predicted Revenue",
            f"₹ {predicted_revenue:,.2f} Cr",
            delta=f"{change_symbol}{revenue_change_percent:.2f}% vs {latest_actual_quarter}",
        )

        r2.metric(
            "Predicted ARPU",
            f"₹ {predicted_arpu:.2f}",
        )

        r3.metric(
            "Customer Base",
            f"{predicted_customers:.2f} Mn",
        )

        r4.metric(
            "Forecast Period",
            target_period,
        )

        st.markdown("#### Estimated Prediction Range")

        range_col1, range_col2, range_col3 = st.columns(3)

        range_col1.metric(
            "Lower Estimate",
            f"₹ {lower_bound:,.2f} Cr",
        )

        range_col2.metric(
            "Central Forecast",
            f"₹ {predicted_revenue:,.2f} Cr",
        )

        range_col3.metric(
            "Upper Estimate",
            f"₹ {upper_bound:,.2f} Cr",
        )

        st.caption(
            "The estimated range is calculated using the model's historical "
            "residual error and should be treated as an approximate uncertainty range."
        )
        result_tab, trends_tab = st.tabs(
            [
                "Forecast Summary",
                "Trend Analysis",
            ]
        )

        with result_tab:
            summary_df = pd.DataFrame(
                {
                    "Metric": [
                        "Company",
                        "Forecast Period",
                        "Predicted Revenue",
                        "Change vs Latest Quarter",
                        "Estimated Revenue Range",
                        "Predicted ARPU",
                        "Predicted Customer Base",
                        "Inflation",
                        "Tariff Impact",
                    ],
                    "Value": [
                        company,
                        target_period,
                        f"₹ {predicted_revenue:,.2f} Cr",
                        f"{change_symbol}{revenue_change_percent:.2f}% ({change_direction})",
                        f"₹ {lower_bound:,.2f} Cr – ₹ {upper_bound:,.2f} Cr",
                        f"₹ {predicted_arpu:.2f}",
                        f"{predicted_customers:.2f} Mn",
                        f"{inflation:.1f}%",
                        "Applied" if tariff else "Not Applied",
                    ],
                }
            )
            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True,
            )

        with trends_tab:
            metric_choice = st.radio(
                "Trend",
                [
                    "Revenue",
                    "ARPU",
                    "Customer Base",
                ],
                horizontal=True,
            )

            fig, ax = plt.subplots(
                figsize=(10, 4)
            )

            ax.plot(
                model_df["Quarter"],
                model_df[metric_choice],
                marker="o",
                label=f"Historical {metric_choice}",
            )

            if metric_choice == "Revenue":
                ax.scatter(
                    [target_period],
                    [predicted_revenue],
                    s=120,
                    label="Forecast",
                )

            elif metric_choice == "ARPU":
                ax.scatter(
                    [target_period],
                    [predicted_arpu],
                    s=120,
                    label="Forecast",
                )

            else:
                ax.scatter(
                    [target_period],
                    [predicted_customers],
                    s=120,
                    label="Forecast",
                )

            ax.set_xlabel("Quarter")
            ax.set_ylabel(metric_choice)
            ax.set_title(
                f"{metric_choice} Trend"
            )
            ax.tick_params(
                axis="x",
                rotation=45,
            )
            ax.legend()
            ax.grid(
                alpha=0.2
            )

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            ax.grid(alpha=0.2)

            fig.tight_layout()

            st.pyplot(fig)

st.divider()

with st.expander(
    "View Historical Training Data"
):
    if df is not None and not df.empty:
        visible_columns = [
            column
            for column in [
                "Quarter",
                "Revenue",
                "ARPU",
                "Customer Base",
                "Inflation",
                "Tariff",
            ]
            if column in df.columns
        ]

        st.dataframe(
            df[visible_columns],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No training data available.")