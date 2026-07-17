# AI Business Forecasting Studio

An AI-powered business forecasting platform that combines machine learning, statistical forecasting, and real-time market intelligence to predict future subscription revenue.

Unlike traditional forecasting tools that rely solely on historical financial data, this application introduces an AI-assisted workflow where users review current economic, regulatory, and industry developments before generating forecasts.

---

## Highlights

- AI-assisted forecasting workflow
- Multiple machine learning and time-series forecasting models
- Real-time market intelligence integration
- Historical walk-forward backtesting
- Automatic model recommendation
- Interactive Plotly dashboards
- Streamlit Cloud deployment
- Modular Python architecture

---

## Features

### Forecast Workflow

The application guides users through a structured forecasting workflow:

1. Forecast Setup
2. AI Market Intelligence
3. Forecast Results

This separates forecast configuration, external business context, and model output into a clean decision-making process.

---

### Forecasting Models

Regression Models

- Linear Regression
- Ridge Regression
- Random Forest Regression

Time-Series Models

- Prophet

Each model is evaluated using historical walk-forward validation before being recommended.

---

### AI Market Intelligence

Before generating a forecast, the application retrieves live business news related to the Indian telecom industry.

Current News Query

```text
(India AND (telecom OR Airtel OR Jio OR "Vodafone Idea"
OR TRAI OR spectrum OR tariff))
OR
(India AND (inflation OR GDP OR economy
OR "repo rate" OR rupee OR "oil prices"))
OR
(India AND (war OR conflict OR sanctions OR geopolitical))
```

The application monitors developments across:

- Telecom industry
- Government policy
- Economic indicators
- Regulatory announcements
- Geopolitical events

This enables users to review current market conditions before generating forecasts.

---

### Forecast Controls

Users can configure:

- Forecasting approach
- Forecasting model
- Forecast quarter
- Financial year
- Expected inflation
- Tariff hike assumptions

---

### Forecast Output

For every forecast the application provides:

- Predicted Revenue
- Expected Revenue Growth
- Prediction Range
- Forecasted ARPU
- Forecasted Customer Base
- Revenue Trend Visualization

---

### Model Evaluation

Every forecasting model is validated using walk-forward backtesting.

Performance metrics include:

- Backtest R²
- RMSE
- MAE
- MAPE

The application automatically recommends the best-performing forecasting model based on historical accuracy.

---

### Interactive Dashboard

- Revenue trend visualization
- Historical vs Forecast comparison
- Prediction confidence range
- Interactive Plotly charts
- Historical data explorer

---

## Dataset

The project currently includes publicly available quarterly financial data from:

- Bharti Airtel Investor Relations
- Reliance Industries / Jio Investor Relations

Historical features include:

- Revenue
- ARPU (Average Revenue Per User)
- Customer Base
- Inflation
- Tariff Events

---

## Technology Stack

### Frontend

- Streamlit

### Backend

- Python

### Machine Learning

- Scikit-learn
- Prophet

### Data Processing

- Pandas
- NumPy

### Visualization

- Plotly

### External APIs

- NewsAPI

### Deployment

- Streamlit Community Cloud

---

## Live Demo

https://revenue-forecasting-model.streamlit.app/

---

## Future Roadmap

- AI-based news sentiment analysis
- Automatic forecast adjustment using market intelligence
- Executive summary generation
- Scenario analysis
- Monte Carlo simulation
- Export to PDF
- Export to Excel
- Multi-company forecasting
- LLM-powered business insights

---

## Why this project?

Traditional forecasting dashboards rely entirely on historical financial performance.

This project extends conventional forecasting by integrating real-time external market intelligence into the forecasting workflow, helping users consider economic, regulatory, and geopolitical developments before making business decisions.

The long-term goal is to bridge historical statistical forecasting with AI-assisted business decision support.