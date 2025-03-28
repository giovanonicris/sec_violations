import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

# Load rule numbers from CSV
rule_numbers_file_path = "rule_numbers.csv"
rule_numbers_df = pd.read_csv(rule_numbers_file_path)

# Extract File Numbers and Release Numbers
file_numbers = rule_numbers_df[rule_numbers_df["number_type"] == "file"]["rule_number"].tolist()
release_numbers = rule_numbers_df[rule_numbers_df["number_type"] == "release"]["rule_number"].tolist()

# Combine identifiers
identifiers = file_numbers + release_numbers

# SEC EDGAR Public Search URL (not the JSON API)
EDGAR_BASE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

# Get SEC User-Agent from environment variable (GitHub Secret)
user_agent = os.getenv("SEC_USER_AGENT")

if not user_agent:
    raise ValueError("Set SEC_USER_AGENT in GitHub Secrets.")

print(f"Using SEC_USER_AGENT: {user_agent[:3]}***")

headers = {
    "User-Agent": user_agent
}

def scrape_edgar(identifier):
    params = {
        "action": "getcompany",
        "company": identifier,  # use text-based search instead of CIK
        "match": "contains",
        "owner": "exclude",
        "count": 100
    }
    try:
        response = requests.get(EDGAR_BASE_URL, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching {identifier}: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.tableFile2 tr")
        filings = []

        for row in rows[1:]:  # Skip header row
            cols = row.find_all("td")
            if len(cols) >= 4:
                form_type = cols[0].text.strip()
                title = cols[1].text.strip()
                filed_date = cols[3].text.strip()
                link_tag = cols[1].find("a")
                link = f"https://www.sec.gov{link_tag['href']}" if link_tag else "N/A"

                filings.append({
                    "identifier": identifier,
                    "form_type": form_type,
                    "title": title,
                    "filed_date": filed_date,
                    "link": link
                })
        return filings

    except Exception as e:
        print(f"Exception while fetching {identifier}: {e}")
        return []

# Collect results
results = []

for identifier in identifiers:
    print(f"Fetching data for {identifier}...")
    filings = scrape_edgar(identifier)
    results.extend(filings)
    time.sleep(1)  # Be polite to SEC servers

# Save results
df_results = pd.DataFrame(results)
csv_filename = "edgar_results.csv"
df_results.to_csv(csv_filename, index=False)

print(f"Results saved to {csv_filename}")
