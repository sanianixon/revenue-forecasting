import streamlit as st

st.set_page_config(page_title="Subscription Revenue Forecasting")

st.title("Subscription Revenue Forecasting")
st.write("Enter forecast inputs below.")

arpu = st.number_input("ARPU", value=250.0)
customers = st.number_input("Customer Base (Millions)", value=500.0)
inflation = st.number_input("Inflation (%)", value=3.0)
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