import os
import re
import pdfplumber
import pandas as pd


RAW_DIR = "raw_reports"
OUTPUT_CSV = "data/airtel_auto_training_data.csv"
INFLATION_CSV = "data/inflation.csv"


def quarter_to_number(quarter_text):
    match = re.search(r"Q([1-4])\s*FY(\d{2})", str(quarter_text))

    if not match:
        return None

    quarter = int(match.group(1))
    year = int(match.group(2))

    return ((year - 19) * 4) + quarter


def extract_text_from_pdf(pdf_path):
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    return full_text


def extract_quarter_from_filename(filename):
    match = re.search(r"(20\d{2}[-_]\d{2}).*?(Q[1-4])", filename, re.IGNORECASE)

    if match:
        year = match.group(1).replace("_", "-")
        quarter = match.group(2).upper()
        return f"{quarter} FY{year[-2:]}"

    return None


def extract_india_revenue(text):
    india_section_match = re.search(
        r"Q[1-4][’']?\d{2}\s+HIGHLIGHTS\s*[–-]\s*INDIA(.*?)(?:Effective|Page|Q[1-4][’']?\d{2}\s+HIGHLIGHTS|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if india_section_match:
        india_section = india_section_match.group(1)

        revenue_match = re.search(
            r"REVENUES AT Rs\s*([\d,]+)\s*CRORE",
            india_section,
            re.IGNORECASE
        )

        if revenue_match:
            return revenue_match

    return re.search(
        r"REVENUES AT Rs\s*([\d,]+)\s*CRORE",
        text,
        re.IGNORECASE
    )


def extract_metrics(pdf_path):
    filename = os.path.basename(pdf_path)

    if "adtech" in filename.lower():
        return None

    text = extract_text_from_pdf(pdf_path)

    quarter = extract_quarter_from_filename(filename)

    if quarter is None:
        quarter_match = re.search(r"Q([1-4])[’']?(\d{2})", text)
        if quarter_match:
            quarter = f"Q{quarter_match.group(1)} FY{quarter_match.group(2)}"

    revenue_match = extract_india_revenue(text)

    arpu_match = re.search(
        r"ARPU AT Rs\s*([\d.]+)",
        text,
        re.IGNORECASE
    )

    customers_match = re.search(
        r"(?:MOBILE\s+4G\s+DATA\s+CUSTOMER|DATA\s+CUSTOMERS?).*?([\d.]+)\s*Mn",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not revenue_match or not arpu_match or not customers_match or not quarter:
        print("Skipped:", filename)
        return None

    return {
        "Company": "Airtel",
        "Quarter": quarter,
        "Revenue": float(revenue_match.group(1).replace(",", "")),
        "ARPU": float(arpu_match.group(1)),
        "Customer Base": float(customers_match.group(1)),
        "Source File": filename,
    }


def add_inflation_and_tariff(df):
    df["Quarter No"] = df["Quarter"].apply(quarter_to_number)

    if os.path.exists(INFLATION_CSV):
        inflation_df = pd.read_csv(INFLATION_CSV)
        df = df.merge(inflation_df, on="Quarter", how="left")
    else:
        df["Inflation"] = None

    q2_fy25_no = quarter_to_number("Q2 FY25")

    df["Tariff"] = df["Quarter No"].apply(
        lambda q: 1 if q and q > q2_fy25_no else 0
    )

    return df


def build_dataset():
    rows = []

    for filename in os.listdir(RAW_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(RAW_DIR, filename)
            result = extract_metrics(pdf_path)

            if result:
                rows.append(result)
                print(
                    "Extracted:",
                    result["Quarter"],
                    result["Revenue"],
                    result["ARPU"],
                    result["Customer Base"]
                )

    df = pd.DataFrame(rows)

    if df.empty:
        print("No valid rows extracted.")
        return

    df = df.drop_duplicates(subset=["Quarter"], keep="last")

    # Remove known bad historical extraction outlier
    df = df[df["Quarter"] != "Q4 FY19"]

    df = add_inflation_and_tariff(df)

    df = df.sort_values("Quarter No")

    df.to_csv(OUTPUT_CSV, index=False)

    print(f"\nSaved dataset to {OUTPUT_CSV}")
    print(f"Rows saved: {len(df)}")


def build_dataset():
    rows = []

    for filename in os. listdir(RAW_DIR):
        print(f"Processing file: {filename}")
        print(f"Full path:")
