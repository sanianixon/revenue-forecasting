AI Business Forecasting Studio

AI-Powered Revenue Forecasting & Market Intelligence Platform

Automatically builds historical financial datasets from quarterly
reports, compares multiple forecasting models, and enhances predictions
using Google Gemini-powered market intelligence.

[Demo GIF] images/ai_business_forecasting_demo_fast.gif

==================================================

Overview

AI Business Forecasting Studio is an end-to-end revenue forecasting
platform that combines machine learning, time-series forecasting, and
generative AI to produce explainable business forecasts. Rather than
relying only on historical financial data, the platform also considers
current market developments using Google Gemini to estimate how recent
events may influence future revenue.

The application automatically downloads and processes Airtel quarterly
reports, extracts key financial metrics, generates structured historical
datasets, trains multiple forecasting models, and presents results
through an interactive Streamlit dashboard. Market news is retrieved
through NewsAPI and analysed by Gemini to provide sentiment,
opportunities, risks, and an estimated market impact score that
complements the statistical forecast.

==================================================

Key Features

• Automatic quarterly report extraction • Historical dataset generation
• Linear Regression • Ridge Regression • Random Forest Regression •
Prophet Time-Series Forecasting • Model comparison using MAE, RMSE, MAPE
and R² • AI-powered market intelligence • Google Gemini integration •
NewsAPI integration • Interactive Streamlit dashboard • Explainable
revenue adjustments • Modular architecture for future expansion

==================================================

Application Walkthrough

1.  Home / Forecast Configuration Image: images/homescreen.png

Users select the company, forecasting model, forecast horizon and
business assumptions before generating predictions.

------------------------------------------------------------------------

2.  Model Comparison Image: images/model_comparison.png

Compare multiple forecasting algorithms using standard evaluation
metrics to identify the best-performing model.

------------------------------------------------------------------------

3.  AI Market Intelligence Image: images/AI_Market_Intelligence.png

Recent business news is analysed by Google Gemini to generate executive
summaries, confidence scores, risks, opportunities and overall market
sentiment.

------------------------------------------------------------------------

4.  Article Analysis Image: images/article.png

Each news article receives an AI-generated relevance assessment to help
explain the market adjustment applied to the forecast.

------------------------------------------------------------------------

5.  Forecast Results Image: images/result.png

The final dashboard combines the baseline statistical forecast with
AI-generated market intelligence to produce an explainable revenue
prediction.

==================================================

Workflow

Quarterly Reports ↓ PDF Extraction ↓ Historical Dataset ↓ Forecasting
Models ↓ Baseline Forecast ↓ NewsAPI ↓ Google Gemini ↓ Market
Intelligence ↓ Final Revenue Forecast

==================================================

Tech Stack

Language: - Python

Dashboard: - Streamlit

Machine Learning: - Scikit-learn - Prophet

Artificial Intelligence: - Google Gemini

External APIs: - NewsAPI

==================================================

Project Structure

app.py config.py data/ models/ services/ ui/ utils/ images/

==================================================

Installation

git clone https://github.com/sanianixon/revenue-forecasting.git

cd revenue-forecasting

pip install -r requirements.txt

streamlit run app.py

Create a .env file:

NEWS_API_KEY=your_newsapi_key GEMINI_API_KEY=your_gemini_api_key

==================================================

Future Improvements

• Support additional companies • Cloud deployment • Export reports as
PDF • Additional forecasting models • More macroeconomic indicators •
Improved historical validation

==================================================

Author

Sania Nixon

GitHub: https://github.com/sanianixon

LinkedIn: https://linkedin.com/in/sania-nixon