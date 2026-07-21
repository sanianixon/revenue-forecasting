<p align="center">

# AI Business Forecasting Studio

### AI-Powered Revenue Forecasting & Market Intelligence Platform

Automatically builds historical financial datasets from quarterly reports, compares multiple forecasting models, and enhances revenue predictions using real-time market intelligence powered by Google Gemini.

<img src="images/demo.gif" width="100%"/>

</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?style=for-the-badge&logo=streamlit)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-orange?style=for-the-badge&logo=scikitlearn)
![Prophet](https://img.shields.io/badge/Prophet-Time%20Series-4285F4?style=for-the-badge)
![Google Gemini](https://img.shields.io/badge/Google-Gemini%20AI-34A853?style=for-the-badge&logo=google)
![NewsAPI](https://img.shields.io/badge/NewsAPI-Real%20Time%20News-blueviolet?style=for-the-badge)

</p>

---

# Overview

ForecastIQ is an end-to-end AI-powered business forecasting platform that combines historical financial analysis, machine learning, time-series forecasting, and real-time market intelligence to generate explainable revenue forecasts.

Unlike traditional forecasting systems that rely entirely on historical financial data, ForecastIQ incorporates current business developments into the prediction pipeline. Recent news, market sentiment, regulatory changes, and industry events are analysed using Google Gemini and translated into quantitative market adjustments, allowing forecasts to adapt to the current business environment while remaining grounded in historical trends.

The platform has been designed with modularity in mind. While Airtel currently includes a fully automated financial data pipeline, the architecture allows additional companies to be integrated with minimal changes, making the system scalable beyond a single business.

---

# Why This Project?

Revenue forecasting is one of the most important problems in business analytics. Companies rely on forecasts to make strategic decisions regarding budgeting, investments, hiring, infrastructure planning, and shareholder guidance.

Most forecasting systems, however, suffer from one major limitation:

> **They only understand the past.**

Traditional machine learning models identify historical patterns extremely well but cannot react to events that occurred yesterday.

For example,

- A major tariff hike
- A new government regulation
- Competitor pricing changes
- Strong quarterly guidance
- Market-wide economic uncertainty

may significantly influence future revenue despite never appearing in historical training data.

ForecastIQ addresses this limitation by combining two complementary approaches:

### Historical Intelligence

Historical quarterly financial reports are used to identify long-term business trends using statistical forecasting models.

### Market Intelligence

Recent business news is analysed using Google Gemini to understand how current events may influence future company performance.

The final forecast combines both perspectives, producing predictions that are data-driven, explainable, and responsive to the current market.

---

# Complete Workflow

```text
                    Quarterly Reports
                           │
                           ▼
              Automatic Report Downloader
                           │
                           ▼
                  Financial PDF Extraction
                           │
                           ▼
              Historical Dataset Generation
                           │
                           ▼
                 Data Cleaning & Validation
                           │
                           ▼
               Machine Learning Models
      ┌────────────┬─────────────┬─────────────┐
      │            │             │             │
 Linear      Ridge Regression  Random Forest  Prophet
 Regression                      Regression
      └────────────┴─────────────┴─────────────┘
                           │
                           ▼
                 Baseline Revenue Forecast
                           │
                           ▼
                Latest Business News (NewsAPI)
                           │
                           ▼
          Google Gemini Market Intelligence Engine
                           │
                           ▼
          Article-Level Analysis & Market Sentiment
                           │
                           ▼
                 AI Market Impact Score
                           │
                           ▼
              Revenue Adjustment Engine
                           │
                           ▼
              Final AI-Enhanced Forecast
```

---

# System Architecture

```text
                                ┌────────────────────────────┐
                                │ Quarterly Financial Reports │
                                └──────────────┬─────────────┘
                                               │
                                               ▼
                               Automatic Report Collection
                                               │
                                               ▼
                                  PDF Data Extraction Engine
                                               │
                                               ▼
                                Historical Financial Dataset
                                               │
                                               ▼
                                Feature Engineering Pipeline
                                               │
                                               ▼
                                  Forecasting Engine
                    ┌───────────────┬──────────────┬───────────────┐
                    │               │              │               │
              Linear Regression   Ridge      Random Forest     Prophet
                    └───────────────┴──────────────┴───────────────┘
                                               │
                                      Model Evaluation
                                               │
                                               ▼
                                     Baseline Forecast
                                               ▲
                                               │
                     ┌─────────────────────────┴─────────────────────────┐
                     │                                                   │
                     ▼                                                   ▼
              NewsAPI                                          Google Gemini
                     │                                                   │
                     └────────────── Latest Market Articles ─────────────┘
                                               │
                                               ▼
                                  Market Intelligence Engine
                                               │
                                               ▼
                                  Market Impact Assessment
                                               │
                                               ▼
                                   Revenue Adjustment Engine
                                               │
                                               ▼
                                   Final Business Forecast
```

---

# Key Highlights

Automatic quarterly report download (Airtel)

Automated financial PDF extraction

Historical dataset generation

Multiple machine learning forecasting models

Time-series forecasting with Prophet

Historical backtesting & model comparison

AI-powered market intelligence

Google Gemini integration

NewsAPI integration

Explainable revenue adjustments

Interactive Streamlit dashboard

Modular architecture for future company expansion

---
# Automatic Quarterly Report Processing

One of the biggest challenges in financial forecasting is building a reliable historical dataset.

Most forecasting projects rely on publicly available datasets or manually prepared CSV files. ForecastIQ instead automates this process for Airtel by building its own dataset directly from publicly available quarterly financial reports.

## Data Pipeline

```text
Quarterly Results Published

            │

            ▼

Download Latest Report

            │

            ▼

Store Original PDF

            │

            ▼

Extract Financial Tables

            │

            ▼

Validate Required Metrics

            │

            ▼

Generate Historical CSV

            │

            ▼

Forecasting Engine
```

Instead of requiring manually prepared datasets, the application automatically downloads Airtel's quarterly reports, extracts the required financial metrics, and converts them into a structured historical dataset that can be directly consumed by the forecasting models.

The generated dataset is stored locally as a CSV, allowing subsequent forecasting operations to execute quickly without repeatedly processing historical reports.

> **Current Implementation:** Airtel includes a fully automated report extraction pipeline.
>
> The application's modular architecture allows additional companies to be integrated by implementing similar extraction logic or by providing a compatible historical dataset.

---

# Historical Dataset Generation

After extracting the financial information from quarterly reports, the application performs several preprocessing steps before model training.

The resulting dataset contains historical business metrics such as:

- Quarterly Revenue
- Average Revenue Per User (ARPU)
- Data Customers
- Inflation
- Tariff Indicator
- Additional engineered features used by the forecasting models

These features are cleaned, standardized, and validated before being passed to the machine learning pipeline.

<p align="center">

<img src="images/dataset.png" width="90%">

*Historical dataset automatically generated from quarterly financial reports.*

</p>

---

# Forecasting Engine

ForecastIQ does not rely on a single prediction model.

Instead, multiple forecasting approaches are trained and evaluated before generating the final prediction.

This allows the platform to compare different modelling techniques and select the most appropriate one based on historical performance.

---

## Linear Regression

Linear Regression provides a strong statistical baseline by modelling the relationship between historical revenue and the selected business drivers.

It is highly interpretable and serves as an excellent benchmark for comparing more advanced models.

---

## Ridge Regression

Ridge Regression extends Linear Regression by introducing regularization, helping reduce overfitting while improving generalisation on unseen data.

This model is particularly useful when predictor variables exhibit correlation.

---

## Random Forest Regression

Random Forest captures complex nonlinear relationships between financial variables that traditional linear models may fail to identify.

Because it combines multiple decision trees, it generally produces more robust predictions while reducing variance.

---

## Prophet

Unlike the regression models, Prophet approaches forecasting as a time-series problem.

It models long-term trends while accounting for seasonal behaviour and changes over time, making it valuable for forecasting revenue trajectories across multiple future quarters.

---

# Model Evaluation & Selection

Every forecasting model is evaluated using historical business data before being presented to the user.

Instead of forcing users to trust a single algorithm, ForecastIQ compares multiple models using standard regression metrics.

The dashboard presents:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Mean Absolute Percentage Error (MAPE)
- R² Score

This enables transparent model comparison and allows users to understand why a particular forecasting model performs better for the selected company.

<p align="center">

<img src="images/model-comparison.png" width="90%">

*Comparison of multiple forecasting models using historical performance metrics.*

</p>

---

# AI Market Intelligence

Historical financial data explains **what has happened.**

Market news explains **what is happening right now.**

ForecastIQ combines both.

Recent news articles are retrieved using NewsAPI before being analysed by Google Gemini.

Rather than generating a forecast directly, Gemini evaluates how current market developments are likely to influence future business performance.

Examples include:

- Tariff announcements
- Regulatory changes
- Market competition
- Expansion plans
- Product launches
- Industry trends
- Macroeconomic conditions

This creates a market intelligence layer that complements the statistical forecasting engine.

---

# Google Gemini Integration

ForecastIQ integrates Google's Gemini API to transform unstructured business news into structured forecasting insights.

The AI engine generates:

- Executive Summary
- Overall Market Sentiment
- Market Impact Score
- Confidence Score
- Key Risks
- Growth Opportunities
- Article-Level Analysis

Unlike conventional news summarisation, the AI output directly contributes to the revenue forecasting workflow.

```text
NewsAPI

        │

        ▼

Latest Articles

        │

        ▼

Google Gemini

        │

        ▼

Executive Summary

Market Sentiment

Confidence

Risk Analysis

Opportunity Analysis

Article Scores

        │

        ▼

Revenue Adjustment Engine
```

---

# Revenue Adjustment Engine

Traditional forecasting models remain responsible for generating the baseline prediction.

Google Gemini does **not** replace these models.

Instead, it evaluates the likely financial impact of current market developments and produces a controlled adjustment that is applied to the statistical forecast.

```text
Historical Forecast

        +

Market Intelligence

        =

Final AI-Enhanced Forecast
```

This hybrid approach preserves explainability while enabling forecasts to adapt to changing business conditions.

To prevent short-term news from disproportionately affecting long-term forecasts, the influence of AI-generated market adjustments gradually decreases as the forecasting horizon extends further into the future.

---

# Interactive Dashboard

ForecastIQ has been designed as an interactive decision-support platform rather than a static forecasting application.

The dashboard allows users to:

### Configure Forecasts

- Select company
- Choose forecasting model
- Set forecasting horizon
- Adjust business assumptions

---

### Explore Historical Data

Visualise historical financial performance before generating predictions.

<p align="center">

<img src="images/history.png" width="90%">

</p>

---

### Compare Models

Compare multiple forecasting algorithms side by side using historical evaluation metrics.

---

### Analyse Market Intelligence

View AI-generated:

- Executive Summary
- Market Impact Score
- Risks
- Opportunities
- Confidence
- Article-level analysis

---

### View Results

The results page combines statistical forecasts with AI market intelligence to produce an explainable business forecast.

The dashboard presents:

- Baseline Forecast
- Market Adjustment
- Final Revenue Forecast
- Revenue Trend Charts
- Historical Comparison
- Prediction Intervals

<p align="center">

<img src="images/results.png" width="90%">

*Final AI-enhanced revenue forecasting dashboard.*

</p>

# Project Structure

The project follows a modular architecture where each component has a dedicated responsibility. This makes the application easier to maintain while allowing individual modules to evolve independently.

```text
AI-Business-Forecasting-Studio/

│
├── app.py                     # Main Streamlit application
├── config.py                  # Configuration variables
├── requirements.txt
│
├── data/                      # Historical datasets & generated files
│
├── models/                    # Forecasting models
│   ├── linear_regression.py
│   ├── ridge_regression.py
│   ├── random_forest.py
│   └── prophet_model.py
│
├── services/
│   ├── report_downloader.py
│   ├── pdf_extractor.py
│   ├── dataset_builder.py
│   ├── news_fetcher.py
│   └── gemini_analysis.py
│
├── ui/
│   ├── forecast_page.py
│   ├── results_page.py
│   ├── market_intelligence.py
│   └── model_comparison.py
│
├── utils/
│
└── images/
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/yourusername/AI-Business-Forecasting-Studio.git

cd AI-Business-Forecasting-Studio
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
streamlit run app.py
```

---

# Environment Variables

Create a `.env` file inside the project directory.

```env
NEWS_API_KEY=your_newsapi_key

GEMINI_API_KEY=your_gemini_api_key
```

The application requires both APIs to enable AI Market Intelligence.

---

# Screenshots

## Home Dashboard

<p align="center">

<img src="images/home.png" width="90%">

</p>

---

## Historical Dataset

<p align="center">

<img src="images/history.png" width="90%">

</p>

---

## Model Comparison

<p align="center">

<img src="images/model-comparison.png" width="90%">

</p>

---

## AI Market Intelligence

<p align="center">

<img src="images/market-intelligence.png" width="90%">

</p>

---

## Results Dashboard

<p align="center">

<img src="images/results.png" width="90%">

</p>

---

# Technical Challenges

This project presented several engineering challenges beyond building forecasting models.

## Automating financial data collection

Quarterly reports are published as PDF documents rather than machine-readable datasets. Building a pipeline capable of automatically downloading reports, extracting structured financial metrics, and converting them into a consistent historical dataset required handling varying document layouts while ensuring the extracted values remained reliable.

---

## Combining traditional forecasting with AI

One of the primary design goals was ensuring the application remained explainable.

Instead of allowing a Large Language Model to directly generate revenue forecasts, the application keeps statistical forecasting models as the primary prediction engine. Google Gemini is used only to analyse current market developments and estimate their likely impact on future business performance.

This hybrid architecture combines the strengths of machine learning and generative AI while maintaining transparency throughout the forecasting process.

---

## Efficient AI inference

Large language model calls are computationally expensive and introduce noticeable latency.

To improve responsiveness, the application implements a fingerprint-based caching strategy. AI-generated market intelligence is stored and reused whenever the underlying news articles remain unchanged, significantly reducing unnecessary API calls and improving the overall user experience.

---

## Building a modular architecture

The application has been structured so that individual components—including report extraction, forecasting models, news retrieval, and AI analysis—remain independent. This modular design simplifies maintenance and makes it easier to extend the platform to support additional companies and forecasting approaches in the future.

---

# Future Improvements

Several enhancements are planned for future versions of the platform.

- Support automatic quarterly report extraction for additional companies
- Incorporate macroeconomic indicators such as GDP growth and interest rates
- Generate downloadable executive PDF reports
- Compare forecasts against analyst estimates
- Add support for cloud deployment
- Introduce additional forecasting algorithms
- Improve historical AI validation using past news events
- Expand support for international companies

---

# What I Learned

Building this project provided practical experience in several areas beyond traditional machine learning.

- Designing end-to-end data pipelines
- Financial data extraction from PDF reports
- Feature engineering for business forecasting
- Comparing multiple forecasting techniques
- Integrating external APIs into production workflows
- Combining traditional machine learning with generative AI
- Building interactive analytical dashboards using Streamlit
- Designing scalable and modular software architectures

---

# Acknowledgements

This project was made possible through publicly available company financial reports and market news sources.

Special thanks to:

- Airtel Investor Relations
- NewsAPI
- Google Gemini
- Streamlit
- Scikit-learn
- Prophet
- Plotly

---

# Author

### Sania Nixon

GitHub: https://github.com/sanianixon

LinkedIn: https://linkedin.com/in/sania-nixon

---

If you found this project interesting, consider giving the repository a ⭐.