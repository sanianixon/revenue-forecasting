import pandas as pd
import streamlit as st

from utils.quarters import quarter_to_number


REQUIRED_COLUMNS = {
    "Quarter",
    "Revenue",
    "ARPU",
    "Customer Base",
}


def load_company_data(company):
    if company == "Airtel":
        company_df = pd.read_csv(
            "data/airtel_auto_training_data.csv"
        )

        inflation_df = pd.read_csv(
            "data/india_quarterly_inflation.csv"
        )

        # Remove the old manually entered inflation values.
        company_df = company_df.drop(
            columns=["Inflation"],
            errors="ignore",
        )

        # Match each Airtel fiscal quarter with official inflation.
        company_df = company_df.merge(
            inflation_df[["Quarter", "Inflation"]],
            on="Quarter",
            how="left",
            validate="many_to_one",
        )

        return company_df, "Automated"

    if company == "Jio":
        return pd.read_csv("data/jio_data.csv"), "Manual"

    uploaded_file = st.file_uploader(
        "Upload Company CSV",
        type=["csv"],
        help="Required columns: Quarter, Revenue, ARPU, Customer Base.",
    )

    if uploaded_file is not None:
        return pd.read_csv(uploaded_file), "Uploaded"

    return None, None


def prepare_company_data(df):
    if df is None:
        return None, None

    df = df.copy()
    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        return None, "The dataset is missing: " + ", ".join(sorted(missing))

    if "Quarter No" not in df.columns:
        df["Quarter No"] = df["Quarter"].apply(quarter_to_number)

    numeric_columns = [
        "Quarter No",
        "Revenue",
        "ARPU",
        "Customer Base",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=numeric_columns)
    df = df[df["Quarter"] != "Q4 FY19"]

    df = (
        df.sort_values("Quarter No")
        .drop_duplicates(subset=["Quarter No"], keep="last")
        .reset_index(drop=True)
    )

    return df, None
