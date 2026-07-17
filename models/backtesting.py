import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from config import REGRESSION_MODELS
from models.core import (
    PROPHET_AVAILABLE,
    create_revenue_model,
    forecast_using_recent_growth,
    predict_prophet_for_quarters,
)


def calculate_metrics(results_df, model_name):
    if results_df is None or len(results_df) < 2:
        return None

    actual = results_df["Actual Revenue"].astype(float)
    predicted = results_df["Predicted Revenue"].astype(float)

    return {
        "Model": model_name,
        "Approach": (
            "Trend Based"
            if model_name == "Prophet"
            else "Regression Based"
        ),
        "Backtest R²": r2_score(actual, predicted),
        "MAE": mean_absolute_error(actual, predicted),
        "RMSE": mean_squared_error(actual, predicted) ** 0.5,
        "MAPE": (((actual - predicted).abs() / actual).mean() * 100),
        "Test Quarters": len(results_df),
    }


def run_regression_backtest(data, model_name, min_train_rows=12):
    backtest_data = (
        data.sort_values("Quarter No").reset_index(drop=True).copy()
    )
    results = []

    for test_index in range(min_train_rows, len(backtest_data)):
        train_df = backtest_data.iloc[:test_index].copy()
        actual_row = backtest_data.iloc[test_index]
        target_quarter_no = int(actual_row["Quarter No"])

        predicted_arpu = forecast_using_recent_growth(
            train_df, "ARPU", target_quarter_no
        )
        predicted_customers = forecast_using_recent_growth(
            train_df, "Customer Base", target_quarter_no
        )

        train_df["Revenue Driver"] = (
            train_df["ARPU"] * train_df["Customer Base"]
        )

        model = create_revenue_model(model_name)
        model.fit(
            train_df[["Revenue Driver"]],
            train_df["Revenue"],
        )

        predicted_driver = predicted_arpu * predicted_customers
        predicted_revenue = float(
            model.predict(
                pd.DataFrame({"Revenue Driver": [predicted_driver]})
            )[0]
        )

        results.append(
            {
                "Quarter": actual_row["Quarter"],
                "Quarter No": target_quarter_no,
                "Actual Revenue": float(actual_row["Revenue"]),
                "Predicted Revenue": predicted_revenue,
                "Error": predicted_revenue - float(actual_row["Revenue"]),
            }
        )

    return _finish_backtest(results, model_name)


def run_prophet_backtest(data, min_train_rows=12):
    if not PROPHET_AVAILABLE:
        return pd.DataFrame(), None

    backtest_data = (
        data.sort_values("Quarter No").reset_index(drop=True).copy()
    )
    results = []

    for test_index in range(min_train_rows, len(backtest_data)):
        train_df = backtest_data.iloc[:test_index].copy()
        actual_row = backtest_data.iloc[test_index]
        target_quarter_no = int(actual_row["Quarter No"])

        forecast_df, _ = predict_prophet_for_quarters(
            train_df, [target_quarter_no]
        )

        predicted_revenue = float(
            forecast_df.iloc[0]["Predicted Revenue"]
        )

        results.append(
            {
                "Quarter": actual_row["Quarter"],
                "Quarter No": target_quarter_no,
                "Actual Revenue": float(actual_row["Revenue"]),
                "Predicted Revenue": predicted_revenue,
                "Error": predicted_revenue - float(actual_row["Revenue"]),
            }
        )

    return _finish_backtest(results, "Prophet")


def _finish_backtest(results, model_name):
    results_df = pd.DataFrame(results)

    if not results_df.empty:
        results_df["Absolute Error"] = results_df["Error"].abs()
        results_df["Error %"] = (
            results_df["Error"] / results_df["Actual Revenue"] * 100
        )

    return results_df, calculate_metrics(results_df, model_name)


def build_model_comparison(df):
    if df is None or df.empty:
        return pd.DataFrame(), {}, []

    comparison_rows = []
    backtest_results = {}

    for name in REGRESSION_MODELS:
        result_df, metrics = run_regression_backtest(df, name)
        backtest_results[name] = result_df

        if metrics is not None:
            comparison_rows.append(metrics)

    prophet_results, prophet_metrics = run_prophet_backtest(df)
    backtest_results["Prophet"] = prophet_results

    if prophet_metrics is not None:
        comparison_rows.append(prophet_metrics)

    comparison_df = pd.DataFrame(comparison_rows)

    if comparison_df.empty:
        return comparison_df, backtest_results, []

    comparison_df = comparison_df.sort_values("RMSE").reset_index(drop=True)
    lowest_rmse = comparison_df["RMSE"].min()

    recommended_models = comparison_df.loc[
        comparison_df["RMSE"].round(6) == round(lowest_rmse, 6),
        "Model",
    ].tolist()

    return comparison_df, backtest_results, recommended_models
