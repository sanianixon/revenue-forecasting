import re
import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Subscription Revenue Forecasting", layout="wide")

st.title("Subscription Revenue Forecasting")

st.write(
    "Select a company and forecast period. The app will automatically forecast ARPU "
    "and customer base, then predict revenue using a regression model."
)


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

    prediction = model.predict(
        pd.DataFrame({"Quarter No": [target_quarter_no]})
    )[0]

    return prediction


def load_company_data(company):
    if company == "Airtel":
        return pd.read_csv("data/airtel_auto_training_data.csv"), "Automated"

    if company == "Jio":
        return pd.read_csv("data/jio_data.csv"), "Manual"

    uploaded_file = st.file_uploader("Upload Company CSV", type=["csv"])

    if uploaded_file is not None:
        return pd.read_csv(uploaded_file), "Uploaded"

    return None, None


company = st.selectbox("Select Company", ["Airtel", "Jio", "Custom Company"])

df, dataset_status = load_company_data(company)

if df is not None:
    df = df.copy()

    if "Quarter No" not in df.columns:
        df["Quarter No"] = df["Quarter"].apply(quarter_to_number)

    df = df.dropna(subset=["Quarter No", "Revenue", "ARPU", "Customer Base"])

    latest_quarter = df.iloc[-1]["Quarter"] if not df.empty else "N/A"
else:
    latest_quarter = "N/A"


with st.sidebar:
    st.header("Model Information")
    st.write(f"**Company:** {company}")

    if df is not None and not df.empty:
        st.write(f"**Dataset:** {dataset_status}")
        st.write(f"**Training Samples:** {len(df)}")
        st.write(f"**Latest Quarter:** {latest_quarter}")
        st.write("**Algorithm:** Multiple Linear Regression")
        st.write("**Status:** Ready")
    else:
        st.write("Upload a valid CSV to begin.")


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

target_period = f"{forecast_quarter} FY{str(forecast_year)[-2:]}"
target_quarter_no = quarter_to_number(target_period)

st.subheader("Forecast Assumptions")

inflation = st.number_input(
    "Expected Inflation (%)",
    value=2.8,
    step=0.1
)

q2_fy25_no = quarter_to_number("Q2 FY25")
auto_tariff = 1 if target_quarter_no > q2_fy25_no else 0

use_tariff = st.checkbox(
    "Apply tariff hike impact",
    value=bool(auto_tariff),
    help="By default, tariff impact is applied for quarters after Q2 FY25."
)

tariff = 1 if use_tariff else 0

c3, c4 = st.columns(2)

with c3:
    st.metric("Inflation", f"{inflation:.1f}%")

with c4:
    st.metric("Tariff Impact", "Applied" if tariff == 1 else "Not Applied")


if df is None or df.empty:
    st.warning("Please upload a valid CSV file to continue.")

else:
    if st.button("Predict Revenue"):
        predicted_arpu = forecast_value(df, "ARPU", target_quarter_no)
        predicted_customers = forecast_value(df, "Customer Base", target_quarter_no)

        revenue_model = LinearRegression()

        X = df[["ARPU", "Customer Base"]]
        y = df["Revenue"]

        revenue_model.fit(X, y)

        input_data = pd.DataFrame(
            {
                "ARPU": [predicted_arpu],
                "Customer Base": [predicted_customers]
            }
        )

        base_revenue = revenue_model.predict(input_data)[0]

        predicted_revenue = (
            base_revenue
            - (977.0008011 * inflation)
            + (1328.559348 * tariff)
        )

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

if show_data and df is not None and not df.empty:
    st.subheader(f"{company} Historical Training Data")
    st.dataframe(df, use_container_width=True)