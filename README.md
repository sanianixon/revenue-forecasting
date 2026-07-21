<p align="center">

# AI Business Forecasting Studio

### AI-Powered Revenue Forecasting & Market Intelligence Platform

Automatically extracts financial data from quarterly reports, compares multiple forecasting models, and enhances predictions using **Google Gemini**.

<img src="images/ai_business_forecasting_demo_fast.gif" width="100%"/>

<br>

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-F7931E?style=for-the-badge&logo=scikitlearn)
![Prophet](https://img.shields.io/badge/Prophet-Time_Series-4285F4?style=for-the-badge)
![Google Gemini](https://img.shields.io/badge/Google-Gemini_AI-34A853?style=for-the-badge)

</p>

---

## Overview

AI Business Forecasting Studio is an end-to-end forecasting application that combines **machine learning** with **AI-powered market intelligence**.

Instead of relying only on historical financial data, the platform analyses the latest business news using **Google Gemini**, allowing forecasts to be adjusted using current market conditions while remaining fully explainable.

The application automatically processes Airtel quarterly reports, builds historical datasets, trains multiple forecasting models, evaluates their performance, and presents everything through an interactive Streamlit dashboard.

You can try it out : https://revenue-forecasting-model.streamlit.app/
---

## Features

| 🚀 Feature | Description |
|------------|-------------|
|  Automated Report Processing | Extract financial metrics directly from quarterly reports |
|  Historical Dataset Generation | Build structured datasets automatically |
|  Multiple Forecasting Models | Linear Regression, Ridge, Random Forest & Prophet |
|  Model Evaluation | Compare models using MAE, RMSE, MAPE & R² |
|  AI Market Intelligence | Analyse live business news using NewsAPI & Gemini |
|  Explainable Forecasting | AI explains why forecasts increase or decrease |
|  Interactive Dashboard | Clean Streamlit interface for predictions |

---

# Dashboard

## Forecast Configuration

<img src="images/homescreen.png">

Choose the forecasting model, prediction horizon and business settings.

---

## Model Comparison

<img src="images/model_comparison.png">

Compare every forecasting model before selecting the best performer.

---

## AI Market Intelligence

<img src="images/AI_Market_Intelligence.png">

Google Gemini summarises news, identifies opportunities and risks, and estimates overall market impact.

---

## Article Analysis

<img src="images/article.png">

Every retrieved article is individually analysed with AI to determine relevance and business impact.

---

## Final Forecast

<img src="images/result.png">

The final prediction combines statistical forecasting with AI-generated market intelligence to produce an explainable revenue forecast.

---

## Workflow

```text
Quarterly Reports
        ↓
PDF Processing
        ↓
Historical Dataset
        ↓
Machine Learning Models
        ↓
Baseline Forecast
        ↓
NewsAPI
        ↓
Google Gemini
        ↓
Market Impact Analysis
        ↓
Final Revenue Prediction
```

---

## Technology Stack

| Category | Technologies |
|----------|--------------|
| Language | Python |
| Dashboard | Streamlit |
| Machine Learning | Scikit-learn, Prophet |
| AI | Google Gemini |
| APIs | NewsAPI |

---

## Project Structure

```text
AI-Business-Forecasting-Studio/
│
├── app.py
├── config.py
├── data/
├── models/
├── services/
├── ui/
├── utils/
├── images/
└── requirements.txt
```

---

## Installation

```bash
git clone https://github.com/sanianixon/revenue-forecasting.git

cd revenue-forecasting

pip install -r requirements.txt

streamlit run app.py
```

Create a `.env` file:

```env
NEWS_API_KEY=your_newsapi_key
GEMINI_API_KEY=your_gemini_api_key
```

---

## Future Improvements

- Support additional companies
- Export executive PDF reports
- Cloud deployment
- More forecasting algorithms
- Additional macroeconomic indicators

---

## Author

**Sania Nixon**

GitHub: https://github.com/sanianixon

LinkedIn: https://linkedin.com/in/sania-nixon