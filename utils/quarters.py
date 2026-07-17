import re
import pandas as pd


def quarter_to_number(quarter_text):
    match = re.search(r"Q([1-4])\s*FY(\d{2})", str(quarter_text))

    if not match:
        return None

    quarter = int(match.group(1))
    year = int(match.group(2))

    return ((year - 19) * 4) + quarter


def number_to_quarter(quarter_no):
    quarter_no = int(quarter_no)
    zero_based = quarter_no - 1
    year = 19 + (zero_based // 4)
    quarter = (zero_based % 4) + 1
    return f"Q{quarter} FY{year:02d}"


def quarter_number_to_date(quarter_no):
    base_date = pd.Timestamp("2018-04-01")
    return base_date + pd.DateOffset(months=3 * (int(quarter_no) - 1))
