import re
import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
import plotly.graph_objects as go

from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
)

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
        recent ARPU and customer growth, and model_name.
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

model_names = [
    "Linear Regression",
    "Ridge Regression",
    "Random Forest Regression",
]

comparison_rows = []
backtest_results = {}

def create_revenue_model(model_name):
    if model_name == "Linear Regression":
        return LinearRegression()

    if model_name == "Ridge Regression":
        return Ridge(alpha=1.0)

    if model_name == "Random Forest Regression":
        return RandomForestRegressor(
            n_estimators=200,
            max_depth=4,
            min_samples_leaf=2,
            random_state=42,
        )

    raise ValueError(f"Unsupported model: {model_name}")

def run_backtest(
    df,
    model_name,
    min_train_rows=12,
):
    """
    Walk-forward backtesting.

    For every test quarter, the model is trained only on
    quarters occurring before that test quarter.
    """

    backtest_data = (
        df.sort_values("Quarter No")
        .reset_index(drop=True)
        .copy()
    )

    results = []

    for test_index in range(
        min_train_rows,
        len(backtest_data),
    ):
        train_df = backtest_data.iloc[
            :test_index
        ].copy()

        actual_row = backtest_data.iloc[
            test_index
        ]

        target_quarter_no = int(
            actual_row["Quarter No"]
        )

        # Forecast inputs using only earlier quarters
        predicted_arpu = forecast_using_recent_growth(
            train_df,
            "ARPU",
            target_quarter_no,
        )

        predicted_customers = forecast_using_recent_growth(
            train_df,
            "Customer Base",
            target_quarter_no,
        )

        # Build training feature
        train_df["Revenue Driver"] = (
            train_df["ARPU"]
            * train_df["Customer Base"]
        )

        X_train = train_df[
            ["Revenue Driver"]
        ]

        y_train = train_df["Revenue"]

        model = create_revenue_model(
            model_name
        )

        model.fit(
            X_train,
            y_train,
        )

        predicted_driver = (
            predicted_arpu
            * predicted_customers
        )

        prediction_input = pd.DataFrame(
            {
                "Revenue Driver": [
                    predicted_driver
                ]
            }
        )

        predicted_revenue = model.predict(
            prediction_input
        )[0]

        results.append(
            {
                "Quarter": actual_row["Quarter"],
                "Quarter No": target_quarter_no,
                "Actual Revenue": actual_row["Revenue"],
                "Predicted Revenue": predicted_revenue,
                "Error": (
                    predicted_revenue
                    - actual_row["Revenue"]
                ),
                "Absolute Error": abs(
                    predicted_revenue
                    - actual_row["Revenue"]
                ),
                "Error %": (
                    (
                        predicted_revenue
                        - actual_row["Revenue"]
                    )
                    / actual_row["Revenue"]
                )
                * 100,
            }
        )

    results_df = pd.DataFrame(results)

    if len(results_df) < 2:
        return results_df, None

    actual = results_df["Actual Revenue"]
    predicted = results_df["Predicted Revenue"]

    metrics = {
        "Model": model_name,
        "Backtest R²": r2_score(
            actual,
            predicted,
        ),
        "MAE": mean_absolute_error(
            actual,
            predicted,
        ),
        "RMSE": mean_squared_error(
            actual,
            predicted,
        ) ** 0.5,
        "MAPE": (
            (
                (
                    actual
                    - predicted
                ).abs()
                / actual
            ).mean()
            * 100
        ),
        "Test Quarters": len(
            results_df
        ),
    }

    return results_df, metrics

if df is not None and not df.empty:
    for name in model_names:
        result_df, metrics = run_backtest(
            df,
            name,
        )

        backtest_results[name] = result_df

        if metrics is not None:
            comparison_rows.append(metrics)

model_comparison_df = pd.DataFrame(
    comparison_rows
)

if not model_comparison_df.empty:
    model_comparison_df = (
        model_comparison_df
        .sort_values("RMSE")
        .reset_index(drop=True)
    )

    recommended_model = (
        model_comparison_df.iloc[0]["Model"]
    )
else:
    recommended_model = None

model_name = st.selectbox(
    "Forecasting Model",
    [
        "Linear Regression",
        "Ridge Regression",
        "Random Forest Regression",
    ],
    index=1,
    help="Select the algorithm used to predict revenue.",
)

model_descriptions = {
    "Linear Regression": (
        "Simple baseline model that learns a linear relationship "
        "between the revenue driver and revenue."
    ),
    "Ridge Regression": (
        "Regularised linear model designed to produce more stable "
        "coefficients when predictors are correlated."
    ),
    "Random Forest Regression": (
        "Tree-based nonlinear model that captures more complex patterns, "
        "but may be less reliable when forecasting beyond historical data."
    ),
}

st.caption(model_descriptions[model_name])

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
        st.write(f"**Algorithm:** {model_name}")

        if df is not None and not df.empty:
            model_df_sidebar = df.copy()
            model_df_sidebar["Revenue Driver"] = (
                model_df_sidebar["ARPU"]
                * model_df_sidebar["Customer Base"]
            )

            sidebar_X = model_df_sidebar[["Revenue Driver"]]
            sidebar_y = model_df_sidebar["Revenue"]

            sidebar_model = create_revenue_model(model_name)
            sidebar_model.fit(sidebar_X, sidebar_y)

            sidebar_r2 = sidebar_model.score(
                sidebar_X,
                sidebar_y
            )

    selected_metrics = model_comparison_df[
        model_comparison_df["Model"]
        == model_name
    ]

    if not selected_metrics.empty:
        backtest_r2 = selected_metrics.iloc[0][
            "Backtest R²"
        ]

        st.write(
            f"**Backtest R²:** "
            f"{backtest_r2:.3f}"
        )
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

        revenue_model = create_revenue_model(model_name)
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
        trends_tab, comparison_tab, data_tab = st.tabs(
            [
                "Revenue Trend",
                "Model Comparison",
                "Historical Data",
            ]
        )
        with data_tab:
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
                width="stretch",
                hide_index=True,
            )

        with trends_tab:

            chart_df = df.copy()
            chart_df = chart_df.sort_values("Quarter No")

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=chart_df["Quarter"],
                    y=chart_df["Revenue"],
                    mode="lines+markers",
                    name="Historical Revenue",
                    line=dict(width=3),
                    marker=dict(size=8),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=[target_period],
                    y=[predicted_revenue],
                    mode="markers",
                    name="Forecast",
                    marker=dict(
                        size=14,
                        symbol="diamond",
                    ),
                )
            )

            fig.update_layout(
                title="Revenue Trend",
                xaxis_title="Quarter",
                yaxis_title="Revenue (Cr)",
                hovermode="x unified",
                height=450,
            )

            st.plotly_chart(fig, use_container_width=True)

        with comparison_tab:
            st.subheader(
                "Walk-Forward Model Evaluation"
            )

            st.caption(
                "Each quarter is predicted using only "
                "the historical data available before it."
            )

            display_comparison = (
                model_comparison_df.copy()
            )

            display_comparison[
                "Backtest R²"
            ] = display_comparison[
                "Backtest R²"
            ].round(3)

            display_comparison[
                "MAE"
            ] = display_comparison[
                "MAE"
            ].round(2)

            display_comparison[
                "RMSE"
            ] = display_comparison[
                "RMSE"
            ].round(2)

            display_comparison[
                "MAPE"
            ] = display_comparison[
                "MAPE"
            ].round(2)

            st.dataframe(
                display_comparison,
                width="stretch",
                hide_index=True,
            )


            with st.expander("What do these metrics mean?"):
                st.markdown(
                    """
                    **Backtest R²** – Shows how well the model predicts unseen historical quarters. Closer to 1 is better.

                    **MAE** – The average prediction error in crore. Lower is better.

                    **RMSE** – Similar to MAE, but large mistakes count more heavily. Lower is better.

                    **MAPE** – The average prediction error as a percentage. Lower is better.

                    **Test Quarters** – The number of historical quarters used during walk-forward backtesting.
                    """
                )

            if recommended_model:
                st.success(
                    f"Recommended model: "
                    f"{recommended_model} "
                    f"(lowest backtest RMSE)"
                )