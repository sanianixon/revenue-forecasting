import streamlit as st


def render_sidebar(company, dataset_status, df):
    with st.sidebar:
        st.subheader("Data Information")
        st.write(f"**Company:** {company}")
        st.write(f"**Dataset:** {dataset_status}")

        if df is not None and not df.empty:
            st.write(f"**Training Samples:** {len(df)}")
            st.write(f"**Latest Quarter:** {df.iloc[-1]['Quarter']}")
        else:
            st.write("**Training Samples:** 0")
            st.write("**Latest Quarter:** Unavailable")