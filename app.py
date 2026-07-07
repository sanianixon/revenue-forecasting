import re
import streamlit as st
import pandas as pd
from sklearn.linear_model import Ridge
import matplotlib.pyplot as plt

st.set_page_config(page_title="Subscription Revenue Forecasting", layout="wide")

st.title("Subscription Revenue Forecasting")

st.write(
    "Select a company and forecast period. The app forecasts ARPU and customer base, "
    "then predicts revenue using a Ridge Regression model."
)


def quarter_to_number(quarter_text):
    match = re.search(r"Q([1-4])\s*FY(\d{2})", str(quarter_text))
    if not match:
        return None

    quarter = int(match.group(1))
    year = int(match.group(2))
    return ((year - 19) * 4) + quarter

def load_company_data(company):
    if company == "Airtel":
        return pd.read_csv("data/airtel_auto_training_data.csv"), "Automated"

    if company == "Jio":
        return pd.read_csv("data/jio_data.csv"), "Manual"

    uploaded_file = st.file_uploader("Upload Company CSV", type=["csv"])

    if uploaded_file is not None:
        return pd.read_csv(uploaded_file), "Uploaded"

    return None, None


def forecast_using_recent_growth(df, column, target_quarter_no, periods=4):
    temp = df.sort_values("Quarter No").tail(periods + 1)

    latest_value = temp[column].iloc[-1]
    latest_quarter_no = temp["Quarter No"].iloc[-1]

    avg_growth = temp[column].diff().dropna().mean()

    quarters_ahead = target_quarter_no - latest_quarter_no

    return latest_value + (avg_growth * quarters_ahead)


company = st.selectbox("Select Company", ["Airtel", "Jio", "Custom Company"])

df, dataset_status = load_company_data(company)

if df is not None:
    df = df.copy()

    if "Quarter No" not in df.columns:
        df["Quarter No"] = df["Quarter"].apply(quarter_to_number)

    df = df.dropna(subset=["Quarter No", "Revenue", "ARPU", "Customer Base"])
    df = df[df["Quarter"] != "Q4 FY19"]
    df = df.sort_values("Quarter No")

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
        st.write("**Algorithm:** Ridge Regression")
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
        predicted_arpu = forecast_using_recent_growth(df, "ARPU", target_quarter_no)
        predicted_customers = forecast_using_recent_growth(df, "Customer Base", target_quarter_no)

        df["Revenue Driver"] = df["ARPU"] * df["Customer Base"]

        X = df[["Revenue Driver"]]
        y = df["Revenue"]

        revenue_model = Ridge(alpha=1.0)
        revenue_model.fit(X, y)

        predicted_driver = predicted_arpu * predicted_customers

        input_data = pd.DataFrame(
            {
                "Revenue Driver": [predicted_driver]
            }
        )

        base_revenue = revenue_model.predict(input_data)[0]

        predicted_revenue = (
            base_revenue
            - (596.87 * inflation)
            + (1366.22 * tariff)
        )

        st.subheader("Forecast Result")

        r1, r2, r3 = st.columns(3)

        with r1:
            st.metric(
                label=f"Predicted Revenue for {target_period}",
                value=f"₹ {predicted_revenue:,.2f} Cr"
            )

        with r2:
            st.metric("Predicted ARPU", f"₹ {predicted_arpu:.2f}")

        with r3:
            st.metric("Predicted Customer Base", f"{predicted_customers:.2f} Mn")

        st.subheader("Model Details")

        m1, m2 = st.columns(2)

        with m1:
            st.write("R² Score:", round(revenue_model.score(X, y), 4))

        with m2:
            st.write("Model Feature:", "ARPU × Customer Base")

        st.subheader("Revenue Trend")

        chart_df = df.copy()

        fig, ax = plt.subplots(figsize=(10, 4))

        ax.plot(
            chart_df["Quarter"],
            chart_df["Revenue"],
            marker="o",
            label="Historical Revenue"
        )

        ax.scatter(
            [target_period],
            [predicted_revenue],
            marker="o",
            s=120,
            label="Forecast"
        )

        ax.set_xlabel("Quarter")
        ax.set_ylabel("Revenue (Cr)")
        ax.set_title("Historical Revenue vs Forecast")
        ax.tick_params(axis="x", rotation=45)
        ax.legend()

        st.pyplot(fig)


st.divider()

show_data = st.checkbox("View Training Data")

if show_data and df is not None and not df.empty:
    st.subheader(f"{company} Historical Training Data")
    st.dataframe(df, use_container_width=True)