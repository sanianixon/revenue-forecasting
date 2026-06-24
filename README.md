# Revenue Forecasting Model

A Streamlit-based revenue forecasting application that uses Multiple Linear Regression to estimate future revenue for subscription-based telecom companies.

The project currently includes historical data from Airtel and Jio and allows users to explore training datasets, analyze trends, and generate revenue forecasts using business and market inputs.

## Features

* Revenue prediction using Multiple Linear Regression
* Historical Airtel and Jio training datasets
* Interactive Streamlit web interface
* Training data viewer with source references
* Deployed web application
* Extensible architecture for additional telecom operators

## Dataset

The current version uses publicly available quarterly financial and operational data from:

* Bharti Airtel Investor Relations
* Reliance Industries / Jio Investor Relations

The datasets contain historical values such as:

* Revenue
* ARPU (Average Revenue Per User)
* Subscriber Base
* Business Metrics used for forecasting

## Model

The forecasting engine uses Multiple Linear Regression to identify relationships between key telecom business metrics and revenue.

Example input variables include:

* ARPU
* Subscriber Base
* Inflation Rate
* Tariff Increase Percentage

The model generates estimated future revenue based on the supplied values.

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

