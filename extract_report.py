import pdfplumber
import re
import pandas as pd
import os

pdf_path = "raw_reports/report.pdf"

# -----------------------------
# Read PDF
# -----------------------------
with pdfplumber.open(pdf_path) as pdf:
    full_text = ""

    for page in pdf.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

# -----------------------------
# Extract values
# -----------------------------
quarter_match = re.search(r"Q([1-4])[’']?(\d{2})\s+HIGHLIGHTS", full_text)

if quarter_match:
    quarter = f"Q{quarter_match.group(1)} FY{quarter_match.group(2)}"
else:
    quarter = "Unknown"

print("Quarter:", quarter)

revenue_match = re.search(r"REVENUES AT Rs ([\d,]+) CRORE", full_text)
arpu_match = re.search(r"ARPU AT Rs (\d+)", full_text)
customers_match = re.search(r"MOBILE 4G DATA CUSTOMER AT ([\d.]+) Mn", full_text)

revenue = revenue_match.group(1).replace(",", "") if revenue_match else None
arpu = arpu_match.group(1) if arpu_match else None
customers = customers_match.group(1) if customers_match else None

print("Extracted Data")
print("Revenue:", revenue)
print("ARPU:", arpu)
print("Data Customers:", customers)

# -----------------------------
# Save to CSV
# -----------------------------
new_row = {
    "Quarter": quarter,
    "Revenue": float(revenue),
    "ARPU": float(arpu),
    "Customer Base": float(customers)
}

csv_path = "data/training_data.csv"

if os.path.exists(csv_path):

    df = pd.read_csv(csv_path)

    if new_row["Quarter"] not in df["Quarter"].values:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(csv_path, index=False)
        print("✅ New quarter added to CSV!")

    else:
        print("⚠ Quarter already exists.")

else:
    pd.DataFrame([new_row]).to_csv(csv_path, index=False)
    print("✅ CSV created!")