import requests
import os

def download_xml():
    url = "https://www.hko.gov.hk/cis/individual_month/monthlyElement.xml"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "data", "monthlyElement.xml")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"已下載 XML 檔案到: {output_file}")
    except Exception as e:
        print("下載失敗:", e)

if __name__ == "__main__":
    download_xml()
