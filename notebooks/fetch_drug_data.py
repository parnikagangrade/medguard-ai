import requests
import json

def get_drug_info(drug_name):
    url = "https://api.fda.gov/drug/label.json"
    params = {
        "search": f'openfda.brand_name:"{drug_name}"',
        "limit": 1
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        return None

# Test it with a real, common drug name
result = get_drug_info("Tylenol")

if result and "results" in result:
    drug = result["results"][0]
    print("Brand name:", drug.get("openfda", {}).get("brand_name"))
    print("Purpose:", drug.get("purpose", ["Not found"]))
    print("Dosage info:", drug.get("dosage_and_administration", ["Not found"]))
    print("Warnings:", drug.get("warnings", ["Not found"]))
else:
    print("No data found")