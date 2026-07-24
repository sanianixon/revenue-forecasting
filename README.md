<p align="center">

# AI Business Forecasting Studio

### AI-Powered Revenue Forecasting & Market Intelligence Platform

Automatically extracts financial data from quarterly reports, compares multiple forecasting models, tests business scenarios, and enhances predictions using **Google Gemini**.

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

AI Business Forecasting Studio is an end-to-end forecasting application that combines **machine learning**, **business scenario analysis**, and **AI-powered market intelligence**.

Instead of relying only on historical financial data, the platform analyses the latest business news using **Google Gemini**, allowing forecasts to be adjusted using current market conditions while remaining fully explainable.

The platform currently provides a complete forecasting workspace for the **Indian telecom industry**. Airtel is available through a built-in verified dataset, while users can upload compatible quarterly data for other Indian telecom companies.

For uploaded datasets, the application uses the entered company name to retrieve company-aware news and generate market intelligence. Since uploaded company names are user-provided, the selected news sources should be reviewed before using the AI market adjustment.

The application automatically processes Airtel quarterly reports, builds historical datasets, trains multiple forecasting models, evaluates their performance, and presents everything through an interactive Streamlit dashboard.

Users can test Conservative, Base Case and Optimistic scenarios or customise the model-generated ARPU and subscriber assumptions. Inflation is calculated automatically using official quarterly CPI data derived from MoSPI rather than requiring a manual estimate.

You can try it out: https://revenue-forecasting-model.streamlit.app/

---

## Features

| 🚀 Feature | Description |
|------------|-------------|
| Automated Report Processing | Extract financial metrics directly from quarterly reports |
| Historical Dataset Generation | Build structured datasets automatically |
| Industry Workspace | Dedicated Indian telecom forecasting workflow |
| Built-In Airtel Dataset | Forecast using automatically prepared and verified Airtel quarterly data |
| Custom Telecom Uploads | Upload quarterly CSV data for another Indian telecom company |
| CSV Data Validation | Validate required columns, numeric values and quarter formatting |
| Multiple Forecasting Models | Linear Regression, Ridge, Random Forest & Prophet |
| Model Evaluation | Compare models using MAE, RMSE, MAPE & R² |
| Scenario-Based Forecasting | Test Conservative, Base Case and Optimistic assumptions |
| Analyst Adjustments | Adjust model-generated ARPU and subscriber assumptions |
| Revenue Impact Breakdown | Separate the revenue effects of ARPU and subscriber adjustments |
| Automatic Inflation Baseline | Use official MoSPI CPI data to calculate quarterly inflation |
| AI Market Intelligence | Analyse live business news using NewsAPI & Gemini |
| Company-Aware News Search | Retrieve market news using the selected or entered company name |
| Company-Specific Caching | Keep AI analysis and quota fallback isolated between companies |
| Quota-Aware AI Fallback | Continue using the last successful analysis when Gemini quota is reached |
| Explainable Forecasting | Show why forecasts increase or decrease |
| Interactive Dashboard | Clean Streamlit interface for predictions |

---

# Dashboard
## Industry Selection

<img src="images/industry_page.png">

Select an industry-specific forecasting workspace. The Indian telecom workspace is currently available, with additional industries planned for future releases.

---

## Company Data

Choose the built-in verified Airtel dataset or upload quarterly data for another Indian telecom company.

Custom CSV files must use the following structure:

| Column | Description | Example |
|--------|-------------|---------|
| Quarter | Indian financial quarter | Q1 FY23 |
| Revenue | Quarterly revenue in ₹ crore | 10410.1 |
| ARPU | Monthly blended ARPU in ₹ | 128 |
| Customer Base | End-of-quarter subscribers in millions | 240.4 |

Uploaded company names are used for company-aware market intelligence but are not independently verified.

---

## Forecast Configuration

<img src="images/homescreen.png">

Choose the forecasting model, forecast period and business scenario. ARPU and subscriber assumptions can be adjusted before generating the forecast.

---

## Model Comparison

<img src="images/model_comparison.png">

Compare every forecasting model before selecting the best performer.

---

## AI Market Intelligence

<img src="images/AI_Market_Intelligence.png">

Google Gemini summarises news, identifies opportunities and risks, and estimates overall market impact.

If a genuine Gemini quota limit is reached, the application displays a warning and continues using the last successfully generated analysis.

---

## Article Analysis

<img src="images/article.png">

Every retrieved article is individually analysed with AI to determine relevance and business impact.

---

## Final Forecast

<img src="images/result.png">

The final prediction combines statistical forecasting, ARPU and subscriber assumptions, automatic inflation data, and AI-generated market intelligence to produce an explainable revenue forecast.

The Results page also separates the revenue effect of each analyst adjustment.

---

## Workflow

```text
Airtel Quarterly Reports       Custom Telecom CSV
           ↓                           ↓
 Automated PDF Processing       Data Validation
           ↓                           ↓
           └──── Historical Dataset ──┘
                        ↓
                Machine Learning Models
                        ↓
                Base ARPU & Subscriber Forecast
                        ↓
                Business Scenario Adjustments
                        ↓
                Baseline Revenue Forecast
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
| Data Processing | Pandas |
| Machine Learning | Scikit-learn, Prophet |
| Visualisation | Plotly |
| AI | Google Gemini |
| APIs | NewsAPI |
| Inflation Data | MoSPI CPI |

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

- Add complete forecasting workspaces for aviation, retail, banking and subscription businesses
- Add more built-in verified telecom company datasets
- Add segment-level forecasting for mobile, broadband and enterprise revenue
- Export executive PDF reports
- Improve scenario calibration using historical outcomes
- Add additional macroeconomic indicators

---

## Author

**Sania Nixon**

GitHub: https://github.com/sanianixon

LinkedIn: https://linkedin.com/in/sania-nixon