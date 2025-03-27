import os
import requests
import pandas as pd

# load rule numbers
rule_numbers_file_path = "rule_numbers.csv"
rule_numbers_df = pd.read_csv(rule_numbers_file_path)
file_numbers = rule_numbers_df[rule_numbers_df["number_type"] == "file"]["rule_number"].tolist()
release_numbers = rule_numbers_df[rule_numbers_df["number_type"] == "release"]["rule_number"].tolist()

# SEC EDGAR API URL
EDGAR_SEARCH_API = "https://efts.sec.gov/LATEST/search-index"

# Get SEC User-Agent from GitHub Secret
user_agent = os.getenv("SEC_USER_AGENT")
if not user_agent:
    raise ValueError("Set SEC_USER_AGENT it in GitHub Secrets.")

headers = {
    "User-Agent": user_agent
}

def search_edgar(identifier):
    query = {
        "q": identifier,
        "dateRange": "all",
        "start": 0,
        "count": 10,
        "category": "filings"
    }
    
    response = requests.post(EDGAR_SEARCH_API, json=query, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 403:
        print(f"403 Forbidden for {identifier} - SEC may be blocking automation.")
    else:
        print(f"Error fetching results for {identifier}: {response.status_code}")
    return None

# collect results
results = []

# search EDGAR
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

# write to data frame
df_results = pd.DataFrame(results)
csv_filename = "edgar_results.csv"
df_results.to_csv(csv_filename, index=False)

print(f"Results saved to {csv_filename}")
