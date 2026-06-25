import streamlit as st
import pandas as pd

st.set_page_config(page_title="Subscription Revenue Forecasting")

company = st.selectbox(
    "Select Company",
    [
        "Airtel",
        "Jio",
        "Custom Company"
    ]
)

if company == "Airtel":
    df = pd.read_csv("data/airtel_auto_training_data.csv")
    dataset_status = "Automated"
    latest_quarter = df.iloc[-1]["Quarter"]

elif company == "Jio":
    df = pd.read_csv("data/jio_data.csv")
    dataset_status = "Manual"
    latest_quarter = df.iloc[-1]["Quarter"]

else:
    uploaded_file = st.file_uploader(
        "Upload Company CSV",
        type=["csv"]
    )

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        dataset_status = "Uploaded"
        latest_quarter = df.iloc[-1]["Quarter"]
    else:
        df = None

st.title("Subscription Revenue Forecasting")

st.write(
    "This tool estimates subscription-based revenue using ARPU, customer base, "
    "inflation, and pricing change inputs, using multiple linear regression."
)
st.write("Enter forecast inputs below.")

with st.sidebar:

    st.header(" Model Information")

    st.write(f"**Company:** {company}")

    if df is not None:

        st.write(f"**Dataset:** {dataset_status}")

        st.write(f"**Training Samples:** {len(df)}")

        st.write(f"**Latest Quarter:** {latest_quarter}")

        st.write("**Status:**  Ready")

    else:

        st.write("Upload a CSV to begin.")

col1, col2 = st.columns(2)

with col1:
    arpu = st.number_input("ARPU", value=250.0)
    inflation = st.number_input("Inflation (%)", value=2.8)

with col2:
    customers = st.number_input("Customer Base (Millions)", value=500.0)
    tariff = st.selectbox("Tariff Hike / Pricing Change", [0, 1])

if st.button("Predict Revenue"):
    revenue = (
        779.8223214
        + (137.3658588 * arpu)
        + (15.72460974 * customers)
        - (977.0008011 * inflation)
        + (1328.559348 * tariff)
    )

    st.metric(
        label="Predicted Revenue",
        value=f"₹ {revenue:,.2f} Cr"
    )

st.divider()

show_data = st.checkbox("View Training Data")

if show_data and df is not None:

    st.subheader(f"{company} Historical Training Data")

    st.dataframe(df, use_container_width=True)