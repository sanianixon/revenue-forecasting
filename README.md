# Revenue Forecasting Model

A Streamlit-based revenue forecasting application that uses Multiple Linear Regression to estimate future revenue for subscription-based telecom companies.

The project currently includes historical data from Airtel and Jio and allows users to explore training datasets, analyze trends, and generate revenue forecasts using business and market inputs.

## Features

- Forecast quarterly subscription revenue using historical company performance.
- Supports multiple forecasting algorithms:
  - Linear Regression
  - Ridge Regression
  - Random Forest Regression
- Interactive forecasting dashboard built with Streamlit.
- Automatic ARPU and Customer Base forecasting using recent historical growth.
- Revenue Driver feature combining ARPU and Customer Base.
- Adjustable macroeconomic assumptions including inflation and tariff impact.
- Walk-forward backtesting to evaluate forecasting accuracy on unseen historical quarters.
- Model comparison using:
  - Backtest R²
  - RMSE
  - MAE
  - MAPE
- Automatic model recommendation based on backtesting performance.
- Interactive Plotly revenue trend visualization.
- Prediction range estimation using historical residual error.
- Support for Airtel, Jio and custom company datasets.

## Dataset

The current version uses publicly available quarterly financial and operational data from:

* Bharti Airtel Investor Relations
* Reliance Industries / Jio Investor Relations

The datasets contain historical values such as:

* Revenue
* ARPU (Average Revenue Per User)
* Subscriber Base
* Business Metrics used for forecasting

## Workflow

1. Select a company dataset.
2. Choose the forecasting algorithm.
3. Configure forecast assumptions:
   - Forecast quarter
   - Financial year
   - Inflation
   - Tariff impact
4. Generate revenue forecast.
5. Compare forecasting models using historical backtesting.
6. Visualize historical and predicted revenue trends.

## Model
## Forecasting Models

### Linear Regression
Provides a simple baseline model for revenue prediction.

### Ridge Regression
Uses L2 regularization to improve stability when predictor variables are highly correlated.

### Random Forest Regression
Captures non-linear relationships using an ensemble of decision trees and is included for performance comparison.

## Model Evaluation

The application evaluates forecasting performance using walk-forward backtesting.

Evaluation metrics include:

- Backtest R²
- RMSE
- MAE
- MAPE

The dashboard automatically recommends the best-performing model based on historical forecasting accuracy.

## Tech Stack

- Python
- Streamlit
- Pandas
- Scikit-learn
- Plotly

## Live Demo

Streamlit Deployment:

https://revenue-forecasting-model.streamlit.app/

## Future Improvements

* Quarter-based forecasting
* Forecasted ARPU and subscriber growth estimation
* Historical vs predicted performance charts
* Model validation metrics
* Additional telecom operators
* Export forecast results

