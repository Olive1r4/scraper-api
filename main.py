import asyncio
import random
from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import uvicorn

app = FastAPI()

# --- CONFIGURAÇÃO DE ROTAÇÃO DE PROXIES ---
# Transcrevi da sua imagem. Todos usam o mesmo usuário/senha.
PROXY_USER = "fernandooliveira@live.com"
PROXY_PASS = "_842JH.-!K!U"

PROXY_LIST = [
    "142.111.48.253:7030", # US - Los Angeles
    "31.59.20.176:6754",   # UK - London
    "23.95.150.145:6114",  # US - Buffalo
    "198.23.239.134:6540", # US - Buffalo
    "107.172.163.27:6543", # US - Bloomingdale
    "198.105.121.200:6462",# UK - City Of London
    "64.137.96.74:6641",   # Spain - Madrid
    "84.247.60.125:6095",  # Poland - Warsaw
    "216.10.27.159:6837",  # US - Dallas
    "142.111.67.146:5611"  # Japan - Tokyo
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36'
]

async def simulate_human_behavior(page):
    try:
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        await asyncio.sleep(random.uniform(0.5, 1.5))
        for _ in range(2):
            await page.mouse.wheel(0, random.randint(100, 300))
            await asyncio.sleep(random.uniform(0.2, 0.5))
    except:
        pass

@app.get("/scrape")
async def scrape(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    async with async_playwright() as p:
        browser = None
        try:
            # 1. Sorteia um Proxy e um User Agent
            selected_ip = random.choice(PROXY_LIST)
            current_ua = random.choice(USER_AGENTS)

            print(f"Tentando com Proxy: {selected_ip}")

            # 2. Lança navegador com o proxy sorteado
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--headless=new",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certificate-errors",
                    "--ignore-certificate-errors-spki-list",
                ],
                proxy={
                    "server": f"http://{selected_ip}",
                    "username": PROXY_USER,
                    "password": PROXY_PASS
                }
            )

            context = await browser.new_context(
                user_agent=current_ua,
                viewport={'width': 1920, 'height': 1080},
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Referer': 'https://www.google.com/',
                    'sec-ch-ua-platform': '"Windows"',
                    'Upgrade-Insecure-Requests': '1'
                }
            )

            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)

            page = await context.new_page()
            await stealth_async(page)

            # 3. Navegação com Timeout maior (120 segundos)
            # Proxies residenciais são lentos, precisamos ter paciência
            response = await page.goto(url, wait_until='domcontentloaded', timeout=120000)

            if response.status in [403, 503]:
                return {"error": f"Bloqueio de IP ({response.status}). Tente novamente para pegar outro proxy."}

            await simulate_human_behavior(page)

            # Espera mais curta para não estourar o tempo total
            await page.wait_for_timeout(2000)

            content = await page.content()

            if "suspicious-traffic" in content or "account-verification" in content:
                return {"error": "Soft Block: ML pediu verificação. Tente novamente."}

            return {"html": content}

        except Exception as e:
            return {"error": f"Erro técnico: {str(e)}"}

        finally:
            if browser:
                await browser.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
