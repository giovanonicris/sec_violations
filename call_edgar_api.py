import os
import requests
import pandas as pd
import time

# Load rule numbers from CSV
rule_numbers_file_path = "rule_numbers.csv"
rule_numbers_df = pd.read_csv(rule_numbers_file_path)

# Extract File Numbers and Release Numbers
file_numbers = rule_numbers_df[rule_numbers_df["number_type"] == "file"]["rule_number"].tolist()
release_numbers = rule_numbers_df[rule_numbers_df["number_type"] == "release"]["rule_number"].tolist()

# SEC EDGAR API URL
EDGAR_SEARCH_API = "https://efts.sec.gov/LATEST/search-index"

# Get SEC User-Agent from environment variable (GitHub Secret)
user_agent = os.getenv("SEC_USER_AGENT")

if not user_agent:
    raise ValueError("Set SEC_USER_AGENT in GitHub Secrets.")

print(f"Using SEC_USER_AGENT: {user_agent[:4]}***")

headers = {
    "User-Agent": user_agent
}

def search_edgar(identifier, retries=2):
    query = {
        "q": identifier,
        "dateRange": "all",
        "start": 0,
        "count": 10,
        "category": "filings"
    }

    for attempt in range(retries + 1):
        response = requests.post(EDGAR_SEARCH_API, json=query, headers=headers)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            print(f"403 Forbidden for {identifier} (attempt {attempt + 1})")
            time.sleep(2)  # Short pause before retry
        else:
            print(f"Error fetching results for {identifier}: {response.status_code}")
            break

    return None

# Collect results
results = []

# Search EDGAR
for identifier in file_numbers + release_numbers:
    data = search_edgar(identifier)
    if data and "hits" in data:
        for item in data["hits"]["hits"]:
            filing_info = {
                "identifier": identifier,
                "form_type": item["_source"].get("formType", "N/A"),
                "title": item["_source"].get("title", "N/A"),
                "filed_date": item["_source"].get("filedDate", "N/A"),
                "link": f"https://www.sec.gov/Archives/{item['_source'].get('filedHref', '')}"
            }
            results.append(filing_info)

# Save results
df_results = pd.DataFrame(results)
csv_filename = "edgar_results.csv"
df_results.to_csv(csv_filename, index=False)

print(f"Results saved to {csv_filename}")
