import re
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Subscription Revenue Forecasting", layout="wide")

st.title("Subscription Revenue Forecasting")

st.write(
    "Select a company and forecast period. The app will forecast ARPU and customer base, "
    "then predict revenue using a regression model."
)

company = st.selectbox("Select Company", ["Airtel", "Jio", "Custom Company"])

df = None
dataset_status = None

if company == "Airtel":
    df = pd.read_csv("data/airtel_auto_training_data.csv")
    dataset_status = "Automated"

elif company == "Jio":
    df = pd.read_csv("data/jio_data.csv")
    dataset_status = "Manual"

else:
    uploaded_file = st.file_uploader("Upload Company CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        dataset_status = "Uploaded"


def quarter_to_number(quarter_text):
    match = re.search(r"Q([1-4])\s*FY(\d{2})", str(quarter_text))
    if not match:
        return None

    quarter = int(match.group(1))
    year = int(match.group(2))

    return ((year - 19) * 4) + quarter


def forecast_value(df, column, target_quarter_no):
    model = LinearRegression()

    X = df[["Quarter No"]]
    y = df[column]

    model.fit(X, y)

    return model.predict([[target_quarter_no]])[0]


with st.sidebar:
    st.header("Model Information")
    st.write(f"**Company:** {company}")

    if df is not None:
        st.write(f"**Dataset:** {dataset_status}")
        st.write(f"**Training Samples:** {len(df)}")
        st.write("**Algorithm:** Multiple Linear Regression")
        st.write("**Status:** Ready")
    else:
        st.write("Upload a CSV to begin.")


st.subheader("Forecast Period")

col1, col2 = st.columns(2)

with col1:
    forecast_quarter = st.selectbox("Select Quarter", ["Q1", "Q2", "Q3", "Q4"])

with col2:
    forecast_year = st.number_input(
        "Select Financial Year",
        min_value=2026,
        max_value=2035,
        value=2027,
        step=1
    )

if df is None:
    st.warning("Please upload a CSV file to continue.")

else:
    df = df.copy()

    if "Quarter No" not in df.columns:
        df["Quarter No"] = df["Quarter"].apply(quarter_to_number)

    df = df.dropna(subset=["Quarter No", "Revenue", "ARPU", "Customer Base"])

    target_period = f"{forecast_quarter} FY{str(forecast_year)[-2:]}"
    target_quarter_no = quarter_to_number(target_period)

    if st.button("Predict Revenue"):
        predicted_arpu = forecast_value(df, "ARPU", target_quarter_no)
        predicted_customers = forecast_value(df, "Customer Base", target_quarter_no)

        X = df[["ARPU", "Customer Base"]]
        y = df["Revenue"]

        revenue_model = LinearRegression()
        revenue_model.fit(X, y)

        predicted_revenue = revenue_model.predict(
            [[predicted_arpu, predicted_customers]]
        )[0]

        st.subheader("Auto-Generated Forecast Inputs")

        c1, c2 = st.columns(2)

        with c1:
            st.metric("Predicted ARPU", f"₹ {predicted_arpu:.2f}")

        with c2:
            st.metric("Predicted Customer Base", f"{predicted_customers:.2f} Mn")

        st.metric(
            label=f"Predicted Revenue for {target_period}",
            value=f"₹ {predicted_revenue:,.2f} Cr"
        )

st.divider()

show_data = st.checkbox("View Training Data")

if show_data and df is not None:
    st.subheader(f"{company} Historical Training Data")
    st.dataframe(df, use_container_width=True)