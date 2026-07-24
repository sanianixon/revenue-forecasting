import pandas as pd
import streamlit as st

from utils.quarters import quarter_to_number


REQUIRED_COLUMNS = {
    "Quarter",
    "Revenue",
    "ARPU",
    "Customer Base",
}

MINIMUM_QUARTERS = 8


def load_india_inflation():
    inflation_df = pd.read_csv(
        "data/india_quarterly_inflation.csv"
    )

    inflation_df["Quarter"] = (
        inflation_df["Quarter"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return inflation_df[["Quarter", "Inflation"]]


def load_company_data(data_source):
    if data_source == "Airtel":
        company_df = pd.read_csv(
            "data/airtel_auto_training_data.csv"
        )

        return company_df, "Built-in verified dataset"

    if data_source == "Upload telecom data":
        uploaded_file = st.file_uploader(
            "Upload quarterly telecom data",
            type=["csv"],
            help=(
                "Required columns: Quarter, Revenue, ARPU, "
                "Customer Base."
            ),
        )

        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                return uploaded_df, "Uploaded CSV"

            except Exception as error:
                st.error(
                    "The uploaded CSV could not be read. "
                    f"Details: {error}"
                )
                return None, None

    return None, None


def prepare_company_data(df):
    if df is None:
        return None, None

    df = df.copy()

    # Remove accidental spaces from column headings.
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        missing_text = ", ".join(
            sorted(missing_columns)
        )

        return (
            None,
            "The dataset is missing the following required "
            f"columns: {missing_text}.",
        )

    if df.empty:
        return None, "The uploaded dataset does not contain any rows."

    # Standardise quarter labels.
    df["Quarter"] = (
        df["Quarter"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Preserve the existing exclusion used by the Airtel dataset.
    df = df[df["Quarter"] != "Q4 FY19"].copy()

    # Convert quarter labels safely.
    quarter_numbers = []
    invalid_quarters = []

    for quarter in df["Quarter"]:
        try:
            quarter_number = quarter_to_number(quarter)

            if quarter_number is None:
                raise ValueError

            quarter_numbers.append(quarter_number)

        except (ValueError, TypeError, IndexError):
            quarter_numbers.append(None)
            invalid_quarters.append(quarter)

    if invalid_quarters:
        invalid_text = ", ".join(
            sorted(set(invalid_quarters))
        )

        return (
            None,
            "Invalid quarter format found: "
            f"{invalid_text}. Use values such as Q1 FY23.",
        )

    df["Quarter No"] = quarter_numbers

    numeric_columns = [
        "Revenue",
        "ARPU",
        "Customer Base",
    ]

    invalid_numeric_columns = []

    for column in numeric_columns:
        converted_values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if converted_values.isna().any():
            invalid_numeric_columns.append(column)

        df[column] = converted_values

    if invalid_numeric_columns:
        invalid_text = ", ".join(
            invalid_numeric_columns
        )

        return (
            None,
            "Some values are missing or non-numeric in: "
            f"{invalid_text}.",
        )

    # Business values must be positive.
    for column in numeric_columns:
        if (df[column] <= 0).any():
            return (
                None,
                f"{column} must contain values greater than zero.",
            )

    # Duplicate quarters should be fixed by the user rather than
    # silently discarded.
    duplicate_quarters = df.loc[
        df["Quarter No"].duplicated(keep=False),
        "Quarter",
    ].unique()

    if len(duplicate_quarters) > 0:
        duplicate_text = ", ".join(
            sorted(duplicate_quarters)
        )

        return (
            None,
            "Duplicate quarters found: "
            f"{duplicate_text}. Keep one row per quarter.",
        )

    df = (
        df.sort_values("Quarter No")
        .reset_index(drop=True)
    )

    if len(df) < MINIMUM_QUARTERS:
        return (
            None,
            "At least 8 historical quarters are required. "
            f"This dataset contains only {len(df)}.",
        )

    # Always use the application's official Indian inflation data.
    # This prevents uploaded files from using inconsistent values.
    df = df.drop(
        columns=["Inflation"],
        errors="ignore",
    )

    inflation_df = load_india_inflation()

    df = df.merge(
        inflation_df,
        on="Quarter",
        how="left",
        validate="many_to_one",
    )

    missing_inflation = df.loc[
        df["Inflation"].isna(),
        "Quarter",
    ].tolist()

    if missing_inflation:
        missing_text = ", ".join(
            missing_inflation
        )

        return (
            None,
            "Official Indian inflation data is unavailable for: "
            f"{missing_text}.",
        )

    return df, None