import requests
import time

def test_scrape():
    url = "http://localhost:3001/scrape"
    target_url = "https://www.mercadolivre.com.br/apple-iphone-15-128-gb-preto-distribuidor-autorizado/p/MLB1027960334"

    print(f"Testing Scraper API at {url} with target {target_url}...")
    try:
        response = requests.get(url, params={"url": target_url}, timeout=120)
        if response.status_code == 200:
            data = response.json()
            if "html" in data and len(data["html"]) > 0:
                print("SUCCESS: HTML content received.")
                print(f"Content length: {len(data['html'])}")
            else:
                print("FAILURE: Response valid but no HTML content.")
        else:
            print(f"FAILURE: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Wait a bit for server to start if running immediately after
    time.sleep(2)
    test_scrape()
