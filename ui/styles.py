import streamlit as st


def apply_global_styles():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.5rem;
            max-width: 1280px;
        }

        section[data-testid="stSidebar"] {
            background-color: #F8FAFC;
        }

        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #E5E7EB;
            border-left: 5px solid #2563EB;
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 1px 6px rgba(0, 0, 0, 0.05);
        }

        /* Common styling for all buttons */
        div.stButton > button {
            width: 100%;
            border-radius: 10px;
            height: 44px;
            font-weight: 600;
        }

        /* Primary buttons */
        div.stButton > button[kind="primary"] {
            background: #2563EB;
            color: white;
            border: none;
        }

        div.stButton > button[kind="primary"]:hover {
            background: #1D4ED8;
        }

        /* Secondary buttons */
        div.stButton > button[kind="secondary"] {
            background: white;
            color: #1F2937;
            border: 1px solid #D1D5DB;
        }

        div.stButton > button[kind="secondary"]:hover {
            background: #F8FAFC;
            border-color: #2563EB;
        }

        div[data-testid="stTabs"] button {
            font-weight: 600;
        }

        .workflow-card {
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 18px 20px;
            margin-bottom: 16px;
        }

        .muted {
            color: #6B7280;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
