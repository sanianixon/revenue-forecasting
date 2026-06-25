import os
import re
import pdfplumber
import pandas as pd


RAW_DIR = "raw_reports"
OUTPUT_CSV = "data/airtel_auto_training_data.csv"


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

    revenue = float(revenue_match.group(1).replace(",", ""))
    arpu = float(arpu_match.group(1))
    customers = float(customers_match.group(1))

    return {
        "Company": "Airtel",
        "Quarter": quarter,
        "Revenue": revenue,
        "ARPU": arpu,
        "Customer Base": customers,
        "Source File": filename,
    }


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

    if not df.empty:
        df = df.drop_duplicates(subset=["Quarter"], keep="last")
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"\nSaved dataset to {OUTPUT_CSV}")
        print(f"Rows saved: {len(df)}")
    else:
        print("No valid rows extracted.")


if __name__ == "__main__":
    build_dataset()