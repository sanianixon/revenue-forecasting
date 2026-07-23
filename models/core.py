import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge

from utils.quarters import number_to_quarter, quarter_number_to_date


try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


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

    raise ValueError(f"Unsupported regression model: {model_name}")


def forecast_using_recent_growth(data, column, target_quarter_no, periods=4):
    temp = data.sort_values("Quarter No").tail(periods + 1).copy()

    latest_value = float(temp[column].iloc[-1])
    latest_quarter_no = int(temp["Quarter No"].iloc[-1])
    average_change = float(temp[column].diff().dropna().mean())
    quarters_ahead = int(target_quarter_no) - latest_quarter_no

    return latest_value + (average_change * quarters_ahead)


def create_prophet_model():
    if not PROPHET_AVAILABLE:
        raise ImportError(
            "Prophet is not installed. Add 'prophet' to requirements.txt."
        )

    return Prophet(
        growth="linear",
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        interval_width=0.95,
        changepoint_prior_scale=0.05,
    )


def prepare_prophet_data(data):
    prophet_df = data[["Quarter No", "Revenue"]].copy()
    prophet_df["ds"] = prophet_df["Quarter No"].apply(quarter_number_to_date)
    prophet_df["y"] = prophet_df["Revenue"].astype(float)
    return prophet_df[["ds", "y"]]


def predict_prophet_for_quarters(train_data, quarter_numbers):
    model = create_prophet_model()
    model.fit(prepare_prophet_data(train_data))

    future = pd.DataFrame(
        {"ds": [quarter_number_to_date(q) for q in quarter_numbers]}
    )

    forecast = model.predict(future)

    result = pd.DataFrame(
        {
            "Quarter No": list(quarter_numbers),
            "Quarter": [number_to_quarter(q) for q in quarter_numbers],
            "Predicted Revenue": forecast["yhat"].values,
            "Lower Estimate": forecast["yhat_lower"].values,
            "Upper Estimate": forecast["yhat_upper"].values,
        }
    )

    return result, model


def build_regression_forecast(
    data,
    model_name,
    target_quarter_no,
    inflation,
    arpu_adjustment=0.0,
    subscriber_adjustment=0.0,
):
    model_df = data.copy()
    model_df["Revenue Driver"] = (
        model_df["ARPU"] * model_df["Customer Base"]
    )

    X = model_df[["Revenue Driver"]]
    y = model_df["Revenue"]

    model = create_revenue_model(model_name)
    model.fit(X, y)

    latest_quarter_no = int(model_df["Quarter No"].max())
    future_quarters = list(
        range(latest_quarter_no + 1, int(target_quarter_no) + 1)
    )

    rows = []

    for quarter_no in future_quarters:
        base_arpu = forecast_using_recent_growth(
            model_df,
            "ARPU",
            quarter_no,
        )

        base_customers = forecast_using_recent_growth(
            model_df,
            "Customer Base",
            quarter_no,
        )

        adjusted_arpu = base_arpu * (
            1 + arpu_adjustment / 100
        )

        adjusted_customers = base_customers * (
            1 + subscriber_adjustment / 100
        )

        base_driver = base_arpu * base_customers

        base_revenue = float(
            model.predict(
                pd.DataFrame(
                    {"Revenue Driver": [base_driver]}
                )
            )[0]
        ) - (596.87 * inflation)

        # Isolate the effect of changing ARPU.
        arpu_adjusted_driver = (
            adjusted_arpu * base_customers
        )

        arpu_adjusted_revenue = float(
            model.predict(
                pd.DataFrame(
                    {
                        "Revenue Driver": [
                            arpu_adjusted_driver
                        ]
                    }
                )
            )[0]
        ) - (596.87 * inflation)

        # Apply both the ARPU and subscriber assumptions.
        final_driver = (
            adjusted_arpu * adjusted_customers
        )

        predicted_revenue = float(
            model.predict(
                pd.DataFrame(
                    {"Revenue Driver": [final_driver]}
                )
            )[0]
        ) - (596.87 * inflation)

        arpu_revenue_effect = (
            arpu_adjusted_revenue - base_revenue
        )

        subscriber_revenue_effect = (
            predicted_revenue - arpu_adjusted_revenue
        )

        net_assumption_effect = (
            predicted_revenue - base_revenue
        )

        assumptions_applied = (
            arpu_adjustment != 0
            or subscriber_adjustment != 0
        )

        rows.append(
            {
                "Quarter No": quarter_no,
                "Quarter": number_to_quarter(quarter_no),
                "Predicted Revenue": predicted_revenue,
                "Base Forecast Revenue": base_revenue,
                "ARPU Revenue Effect": arpu_revenue_effect,
                "Subscriber Revenue Effect": (
                    subscriber_revenue_effect
                ),
                "Net Assumption Effect": net_assumption_effect,
                "Predicted ARPU": adjusted_arpu,
                "Predicted Customer Base": adjusted_customers,
                "Assumptions Applied": assumptions_applied,
            }
        )

    forecast_df = pd.DataFrame(rows)

    residuals = y - model.predict(X)
    rmse = float((residuals.pow(2).mean()) ** 0.5)

    if not forecast_df.empty:
        forecast_df["Lower Estimate"] = (
            forecast_df["Predicted Revenue"] - (1.96 * rmse)
        )
        forecast_df["Upper Estimate"] = (
            forecast_df["Predicted Revenue"] + (1.96 * rmse)
        )

    return forecast_df, model
