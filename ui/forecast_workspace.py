import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import (
    APPROACH_DESCRIPTIONS,
    MODEL_DESCRIPTIONS,
    REGRESSION_MODELS,
    TREND_MODELS,
)
from models.core import PROPHET_AVAILABLE
from ui.navigation import go_to_page
from utils.quarters import quarter_to_number


def render_forecast_workspace(
    df,
    comparison_df,
    backtest_results,
    recommended_models,
    mode,
):
    if mode == "setup":
        _render_setup(df)
    else:
        _render_results(
            df,
            comparison_df,
            backtest_results,
            recommended_models,
        )


def _render_setup(df):
    st.subheader("Forecast Configuration")
    st.caption(
        "Choose the forecasting method and target period. Review external "
        "intelligence in the next step before generating the forecast."
    )

    approach_col, model_col = st.columns(2)

    with approach_col:
        approach = st.selectbox(
            "Forecasting Approach",
            ["Regression Based", "Trend Based"],
            key="forecasting_approach",
        )

    available_models = (
        REGRESSION_MODELS
        if approach == "Regression Based"
        else TREND_MODELS
    )

    current_model = st.session_state.get("forecasting_model")

    if current_model not in available_models:
        st.session_state["forecasting_model"] = available_models[0]

    with model_col:
        model_name = st.selectbox(
            "Forecasting Model",
            available_models,
            key="forecasting_model",
        )

    st.caption(
        f"{APPROACH_DESCRIPTIONS[approach]} "
        f"{MODEL_DESCRIPTIONS[model_name]}"
    )

    if model_name == "Prophet" and not PROPHET_AVAILABLE:
        st.error(
            "Prophet is not installed. Add `prophet` to requirements.txt."
        )

    st.markdown("#### Target Period and Assumptions")

    left, right = st.columns(2)

    with left:
        forecast_quarter = st.selectbox(
            "Forecast Quarter",
            ["Q1", "Q2", "Q3", "Q4"],
            key="forecast_quarter",
        )

        forecast_year = st.number_input(
            "Financial Year",
            min_value=2026,
            max_value=2035,
            value=2027,
            step=1,
            key="forecast_year",
        )

    with right:
        controls_disabled = approach == "Trend Based"

        inflation = st.number_input(
            "Expected Inflation (%)",
            min_value=0.0,
            max_value=20.0,
            value=2.8,
            step=0.1,
            disabled=controls_disabled,
            key="forecast_inflation",
        )

        target_period = (
            f"{forecast_quarter} FY{str(forecast_year)[-2:]}"
        )
        target_quarter_no = quarter_to_number(target_period)
        q2_fy25_no = quarter_to_number("Q2 FY25")

        use_tariff = st.toggle(
            "Apply tariff hike impact",
            value=target_quarter_no > q2_fy25_no,
            disabled=controls_disabled,
            key="forecast_tariff_toggle",
        )

    if approach == "Trend Based":
        st.info(
            "Trend-based forecasting ignores inflation, tariff, ARPU, "
            "and customer-base controls."
        )

    latest_quarter_no = int(df["Quarter No"].max())

    if target_quarter_no <= latest_quarter_no:
        st.warning(
            f"Choose a quarter after {df.iloc[-1]['Quarter']}."
        )

    next_disabled = (
        target_quarter_no <= latest_quarter_no
        or (
            model_name == "Prophet"
            and not PROPHET_AVAILABLE
        )
    )

    button_left, button_right = st.columns([3, 1])

    with button_right:
        if st.button(
            "Next →",
            type="primary",
            use_container_width=True,
            disabled=next_disabled,
            key="setup_next_button",
        ):
            # IMPORTANT:
            # Streamlit removes widget values when their page is no longer rendered.
            # Save a permanent copy before leaving Forecast Setup.
            st.session_state["forecast_config"] = {
                "approach": approach,
                "model_name": model_name,
                "forecast_quarter": forecast_quarter,
                "forecast_year": int(forecast_year),
                "inflation": float(inflation),
                "use_tariff": bool(use_tariff),
                "target_period": target_period,
                "target_quarter_no": int(target_quarter_no),
            }

            go_to_page("ai")
            st.rerun()


def _render_results(
    df,
    comparison_df,
    backtest_results,
    recommended_models,
):
    st.subheader("Results & Analysis")

    output = st.session_state.get("forecast_output")

    market_adjustment = output.get("market_adjustment", {})
    adjustment_percent = market_adjustment.get("adjustment_percent", 0.0)
    adjustment_applied = market_adjustment.get("applied", False)

    if not output:
        st.info(
            "Generate a forecast from Forecast Setup to view results."
        )

        if st.button(
            "Go to Forecast Setup",
            key="results_to_setup_button",
        ):
            go_to_page("setup")
            st.rerun()

        return

    forecast_df = output["forecast_df"]
    approach = output["approach"]
    model_name = output["model_name"]
    target_period = output["target_period"]

    target = forecast_df.iloc[-1]

    predicted_revenue = float(target["Predicted Revenue"])
    lower_bound = float(target["Lower Estimate"])
    upper_bound = float(target["Upper Estimate"])

    latest_actual_revenue = float(df.iloc[-1]["Revenue"])
    latest_actual_quarter = df.iloc[-1]["Quarter"]

    change_percent = (
        (predicted_revenue - latest_actual_revenue)
        / latest_actual_revenue
        * 100
    )

    st.caption(f"FORECAST FOR {target_period}")

    if adjustment_applied:
        base_revenue = float(
            target.get("Base Model Revenue", predicted_revenue)
        )

        adjustment_amount = predicted_revenue - base_revenue

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Base Model Forecast",
                f"₹ {base_revenue:,.2f} Cr",
            )

        with col2:
            st.markdown(
                f"""
        <div style="
            border-left:4px solid #2F80ED;
            border-radius:12px;
            padding:18px 18px 14px 18px;
            border:1px solid rgba(49,51,63,0.2);
            height:115px;
        ">

        <div style="
            font-size:14px;
            color:#666;
            margin-bottom:10px;
        ">
        Market Adjustment
        </div>

        <div style="
            display:flex;
            align-items:baseline;
            gap:10px;
        ">

        <span style="
            font-size:22px;
            font-weight:700;
        ">
        ₹ {adjustment_amount:+,.2f} Cr
        </span>

        <span style="
            font-size:13px;
            color:#2F80ED;
            font-weight:600;
        ">
        ({adjustment_percent:+.2f}%)
        </span>

        </div>

        </div>
        """,
                unsafe_allow_html=True,
            )

        with col3:
            st.metric(
                "Final Adjusted Forecast",
                f"₹ {predicted_revenue:,.2f} Cr",
            )

    else:
        st.markdown(f"# ₹ {predicted_revenue:,.2f} Cr")

    delta_text = (
        f"{change_percent:+.2f}% vs {latest_actual_quarter}"
    )

    if change_percent >= 0:
        st.success(delta_text)
    else:
        st.error(delta_text)

    if approach == "Regression Based":
        st.write(
            f"**ARPU:** ₹ {float(target['Predicted ARPU']):,.2f}"
            f"  ·  **Customer Base:** "
            f"{float(target['Predicted Customer Base']):,.2f} Mn"
            f"  ·  **Model:** {model_name}"
        )
    else:
        st.write(f"**Model:** {model_name}")

    st.caption(
        f"Expected range: ₹ {lower_bound:,.2f} Cr – "
        f"₹ {upper_bound:,.2f} Cr"
    )

    st.divider()

    trend_tab, comparison_tab, data_tab = st.tabs(
        [
            "Revenue Trend",
            "Model Comparison",
            "Historical Data",
        ]
    )

    with trend_tab:
        _render_revenue_chart(
            df,
            forecast_df,
            model_name,
        )

    with comparison_tab:
        _render_model_comparison(
            comparison_df,
            backtest_results,
            model_name,
            recommended_models,
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
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    back_col, _ = st.columns([1, 3])

    with back_col:
        if st.button(
            "← Back to Intelligence",
            use_container_width=True,
            key="results_back_button",
        ):
            go_to_page("ai")
            st.rerun()


def _render_revenue_chart(
    df,
    forecast_df,
    model_name,
):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Quarter"],
            y=df["Revenue"],
            mode="lines+markers",
            name="Historical Revenue",
            line=dict(width=3),
            marker=dict(size=7),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast_df["Quarter"],
            y=forecast_df["Predicted Revenue"],
            mode="lines+markers",
            name=f"{model_name} Forecast",
            line=dict(width=3, dash="dash"),
            marker=dict(size=8, symbol="diamond"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast_df["Quarter"],
            y=forecast_df["Upper Estimate"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast_df["Quarter"],
            y=forecast_df["Lower Estimate"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            name="Prediction Range",
        )
    )

    fig.update_layout(
        title=f"Revenue Trend — {model_name}",
        xaxis_title="Quarter",
        yaxis_title="Revenue (Cr)",
        hovermode="x unified",
        height=470,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


def _render_model_comparison(
    comparison_df,
    backtest_results,
    model_name,
    recommended_models,
):
    if comparison_df.empty:
        st.info(
            "Model comparison is unavailable for this dataset."
        )
        return

    display_df = comparison_df.copy()

    for metric in [
        "Backtest R²",
        "MAE",
        "RMSE",
        "MAPE",
    ]:
        if metric in display_df.columns:
            display_df[metric] = display_df[metric].round(
                3 if metric == "Backtest R²" else 2
            )

    display_columns = [
        column
        for column in [
            "Approach",
            "Model",
            "Backtest R²",
            "MAE",
            "RMSE",
            "MAPE",
            "Test Quarters",
        ]
        if column in display_df.columns
    ]

    st.dataframe(
        display_df[display_columns],
        use_container_width=True,
        hide_index=True,
    )

    if recommended_models:
        st.success(
            "Recommended model: "
            + " + ".join(recommended_models)
            + " (lowest backtest RMSE)"
        )

    with st.expander("Understanding the Evaluation Metrics"):
        st.markdown(
            """
**Backtest R²**  
Shows how much of the variation in historical revenue is explained by the
model during backtesting. A value closer to 1 is better.

**MAE — Mean Absolute Error**  
The average absolute difference between actual and predicted revenue.
Lower values are better.

**RMSE — Root Mean Squared Error**  
Measures prediction error while giving more weight to larger mistakes.
Lower values are better.

**MAPE — Mean Absolute Percentage Error**  
The average prediction error expressed as a percentage of actual revenue.
Lower values are better.

**Test Quarters**  
The number of historical quarters used as unseen test periods.
"""
        )

    selected_backtest = backtest_results.get(
        model_name,
        pd.DataFrame(),
    )

    if not selected_backtest.empty:
        backtest_columns = [
            column
            for column in [
                "Quarter",
                "Actual Revenue",
                "Predicted Revenue",
                "Absolute Error",
                "Error %",
            ]
            if column in selected_backtest.columns
        ]

        with st.expander(f"{model_name} Backtest Results"):
            st.dataframe(
                selected_backtest[backtest_columns].round(2),
                use_container_width=True,
                hide_index=True,
            )