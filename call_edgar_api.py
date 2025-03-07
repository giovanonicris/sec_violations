import requests
import pandas as pd

# load csv reference file
rule_numbers_file_path = "rule_numbers.csv"  # Update with your actual path if needed
rule_numbers_df = pd.read_csv(rule_numbers_file_path)
file_numbers = rule_numbers_df[rule_numbers_df["number_type"] == "file"]["rule_number"].tolist()
release_numbers = rule_numbers_df[rule_numbers_df["number_type"] == "release"]["rule_number"].tolist()

# edgar endpoint for search
EDGAR_SEARCH_API = "https://efts.sec.gov/LATEST/search-index"

# search EDGAR for filings related to the identifier
def search_edgar(identifier):
    query = {
        "q": identifier,
        "dateRange": "all",  # Search across all available years
        "start": 0,
        "count": 10,  # Limit results to 10
        "category": "filings"
    }
    
    headers = {
        "User-Agent": "YourName-YourEmail"
    }
    
    response = requests.post(EDGAR_SEARCH_API, json=query, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching results for {identifier}: {response.status_code}")
        return None

results = []

# search each file/release numbers
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

# prep and write data frame
df_results = pd.DataFrame(results)
csv_filename = "edgar_results.csv"
df_results.to_csv(csv_filename, index=False)

print(f"Results saved to {csv_filename}")
