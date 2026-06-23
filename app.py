import streamlit as st
import pandas as pd

st.set_page_config(page_title="Subscription Revenue Forecasting")

airtel_df = pd.read_csv("data/airtel_data.csv")
jio_df = pd.read_csv("data/jio_data.csv")

st.title("Subscription Revenue Forecasting")
st.write("This tool estimates subscription-based revenue using ARPU, customer base, inflation, and pricing change inputs.")
st.write("Enter forecast inputs below.")

arpu = st.number_input("ARPU", value=250.0)
customers = st.number_input("Customer Base (Millions)", value=500.0)
inflation = st.number_input("Inflation (%)", value=2.8)
tariff = st.selectbox("Tariff Hike / Pricing Change", [0, 1])

if st.button("Predict Revenue"):
    revenue = (
        779.8223214
        + (137.3658588 * arpu)
        + (15.72460974 * customers)
        - (977.0008011 * inflation)
        + (1328.559348 * tariff)
    )

    st.success(f"Predicted Revenue: ₹ {revenue:,.2f} Cr")

st.divider()

show_data = st.checkbox("View Training Data")

if show_data:
    company = st.selectbox("Select company", ["Airtel", "Jio"])

    if company == "Airtel":
        st.subheader("Airtel Historical Data")

        st.dataframe(airtel_df, use_container_width=True)

    elif company == "Jio":
        st.subheader("Jio Historical Data")

        st.dataframe(jio_df, use_container_width=True)