import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def clear_company_reports(company):
    folder = "raw_reports"

    if not os.path.exists(folder):
        return

    company = company.lower()

    for file in os.listdir(folder):
        if file.lower().startswith(company) and file.lower().endswith(".pdf"):
            os.remove(os.path.join(folder, file))

    print(f"Old {company} reports deleted.")

COMPANY_CONFIG = {
    "airtel": {
        "results_url": "https://www.airtel.in/about-bharti/equity/results",
        "required_keywords": ["quarterly", "highlight"],
        "file_prefix": "airtel",
    },
    "jio": {
        "results_url": "https://www.ril.com/investors/financial-reporting",
        "required_keywords": ["financial", "performance"],
        "file_prefix": "jio",
    },
}


def get_all_reports(company):
    company = company.lower()

    if company not in COMPANY_CONFIG:
        print("Company not supported.")
        return []

    config = COMPANY_CONFIG[company]

    response = requests.get(config["results_url"])

    if response.status_code != 200:
        print(f"Failed to open {company} page.")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    reports = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        href_lower = href.lower()

        if all(keyword in href_lower for keyword in config["required_keywords"]):
            full_url = urljoin(config["results_url"], href)
            reports.append(full_url)

    return sorted(list(set(reports)))


def download_reports(company, reports):
    company = company.lower()

    if company not in COMPANY_CONFIG:
        print("Company not supported.")
        return []

    os.makedirs("raw_reports", exist_ok=True)

    file_prefix = COMPANY_CONFIG[company]["file_prefix"]
    downloaded_files = []

    for index, url in enumerate(reports, start=1):
        filename = url.split("/")[-1].split("?")[0]

        if not filename:
            filename = f"report_{index}.pdf"

        safe_filename = f"{file_prefix}_{filename}"
        file_path = os.path.join("raw_reports", safe_filename)

        response = requests.get(url)

        if response.status_code == 200:
            with open(file_path, "wb") as file:
                file.write(response.content)

            downloaded_files.append(file_path)
            print("Downloaded:", file_path)
        else:
            print("Failed:", url)

    return downloaded_files


if __name__ == "__main__":
    company = "jio"  # change to "airtel" when needed

    reports = get_all_reports(company)
    print(f"\nFound {len(reports)} reports for {company}\n")

    for report in reports:
        print(report)

    clear_company_reports(company)

    downloaded_files = download_reports(company, reports)

    print("CSV/extraction step should run here later.")

    # Delete temporary PDFs only after extraction works
    # clear_company_reports(company)ts)
    print(f"\nDownloaded {len(downloaded_files)} files")