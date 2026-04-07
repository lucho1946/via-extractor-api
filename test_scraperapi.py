import requests

API_KEY = "906b6c743bc28ff15a8a2af1cd154a03"

url = "https://www.amazon.com/dp/B004MUECS0"

response = requests.get(
    "http://api.scraperapi.com",
    params={
        "api_key": API_KEY,
        "url": url,
        "country_code": "us"
    }
)

print("STATUS:", response.status_code)
print("\nHTML PREVIEW:\n")
print(response.text[:1000])