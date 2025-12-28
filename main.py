import asyncio
import random
from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
# IMPORTANTE: Garanta que 'playwright-stealth' está no requirements.txt
from playwright_stealth import stealth_async
import uvicorn

app = FastAPI()

# User-Agents rotativos
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36'
]

async def simulate_human_behavior(page):
    """Simula movimentos humanos para enganar o anti-bot"""
    try:
        # Movimentos suaves do mouse
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Scroll lento para baixo
        for _ in range(3):
            await page.mouse.wheel(0, random.randint(100, 300))
            await asyncio.sleep(random.uniform(0.2, 0.8))

        # Pequeno scroll para cima
        await page.mouse.wheel(0, -50)
    except:
        pass

@app.get("/scrape")
async def scrape(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    async with async_playwright() as p:
        browser = None
        try:
            current_ua = random.choice(USER_AGENTS)

            # --- LANÇAMENTO DO BROWSER COM PROXY ---
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
                # CONFIGURAÇÃO DA WEBSHARE (IP, Porta, User, Senha)
                proxy={
                    "server": "http://142.111.48.253:7030",
                    "username": "fernandooliveira@live.com",
                    "password": "_842JH.-!K!U"
                }
            )
            # ---------------------------------------

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
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = await context.new_page()

            # Ativa modo furtivo
            await stealth_async(page)

            print(f"Acessando via Proxy: {url}")

            # Timeout aumentado para 60s (Proxy pode ser lento)
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)

            if response.status == 403 or response.status == 503:
                return {"error": f"Bloqueio detectado. Status: {response.status}"}

            await simulate_human_behavior(page)
            await page.wait_for_timeout(3000)

            content = await page.content()

            if "suspicious-traffic" in content or "account-verification" in content:
                return {"error": "Soft Block: Verificação de segurança solicitada."}

            return {"html": content}

        except Exception as e:
            return {"error": str(e)}

        finally:
            # O ERRO ESTAVA AQUI (FALTA DE INDENTAÇÃO)
            if browser:
                await browser.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
