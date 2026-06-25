import requests
from bs4 import BeautifulSoup
import os

RESULTS_URL = "https://www.airtel.in/about-bharti/equity/results"


def get_all_reports():

    response = requests.get(RESULTS_URL)

    if response.status_code != 200:
        print("Failed to open Airtel page.")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    reports = []

    for link in soup.find_all("a", href=True):

        href = link["href"]

        href_lower = href.lower()

        if (
            "quarterly" in href_lower
            and "highlight" in href_lower
            and href_lower.endswith(".pdf")
        ):

            reports.append(href)

    return sorted(list(set(reports)))



def download_reports(reports):
    os.makedirs("raw_reports", exist_ok=True)

    downloaded_files = []

    for url in reports:
        filename = url.split("/")[-1]
        parts = url.split("/")

        year = parts[-3]
        quarter = parts[-2]

        safe_filename = f"airtel_{year}_{quarter}_{filename}"
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
    reports = get_all_reports()
    print(f"\nFound {len(reports)} reports\n")

    downloaded_files = download_reports(reports)
    print(f"\nDownloaded {len(downloaded_files)} files")

