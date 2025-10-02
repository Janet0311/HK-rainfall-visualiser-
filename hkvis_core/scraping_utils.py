import requests
import os


# Always save the file in the same directory as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(script_dir, "monthlyElement.html")

url = "https://www.hko.gov.hk/en/cis/monthlyElement.htm?stn=HKO&ele=RF"
headers = {
    "User-Agent": "python-requests/2.0 (+https://example.com/)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

try:
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()  # raise on HTTP errors

    encoding = resp.encoding if resp.encoding else "utf-8"
    with open(output_file, "w", encoding=encoding) as f:
        f.write(resp.text)

    print(f"Saved page to {output_file} (encoding: {encoding})")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
