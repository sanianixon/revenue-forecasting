import streamlit as st

from services.inflation import calculate_inflation_baseline


def render_sidebar(company, dataset_status, df):
    with st.sidebar:
        st.subheader("Data Information")
        st.write(f"**Company:** {company}")
        st.write(f"**Dataset:** {dataset_status}")

        if df is not None and not df.empty:
            st.write(f"**Training Samples:** {len(df)}")
            st.write(f"**Latest Quarter:** {df.iloc[-1]['Quarter']}")
            inflation_summary = calculate_inflation_baseline()

            st.write(
                f"**Inflation Baseline:** "
                f"{inflation_summary['baseline']:.2f}%"
            )

            st.caption(
                "Automatic average of the latest four "
                "official inflation quarters."
            )
        else:
            st.write("**Training Samples:** 0")
            st.write("**Latest Quarter:** Unavailable")