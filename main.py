import asyncio
import random
from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
# Certifique-se que 'playwright-stealth' está no requirements.txt
from playwright_stealth import stealth_async
import uvicorn

app = FastAPI()

# User-Agents rotativos (Desktop Windows/Mac)
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

        # Scroll lento para baixo (como alguém lendo)
        for _ in range(3):
            await page.mouse.wheel(0, random.randint(100, 300))
            await asyncio.sleep(random.uniform(0.2, 0.8))

        # Pequeno scroll para cima (comportamento de re-leitura)
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
            # Seleciona UA aleatório
            current_ua = random.choice(USER_AGENTS)

            # Lança o navegador com Proxy e Argumentos Anti-Detecção
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--headless=new", # Modo headless indetectável
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certificate-errors",
                    "--ignore-certificate-errors-spki-list",
                ],
                # --- CONFIGURAÇÃO DO PROXY (Obrigatório para VPS) ---
                proxy={
                    "server": "http://142.111.48.253:7030", # Verifique se a porta é 80 ou 8000
                    "username": "fernandooliveira@live.com",      # <--- TROQUE AQUI
                    "password": "_842JH.-!K!U"         # <--- TROQUE AQUI
                }
                # -----------------------------------------------------
            )

            # Cria contexto ultra-realista
            context = await browser.new_context(
                user_agent=current_ua,
                viewport={'width': 1920, 'height': 1080},
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                # Headers extras para fingir que veio do Google
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Referer': 'https://www.google.com/',
                    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'Upgrade-Insecure-Requests': '1'
                }
            )

            # Script para apagar rastros do webdriver
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = await context.new_page()

            # Ativa a biblioteca de camuflagem
            await stealth_async(page)

            print(f"Acessando via Proxy: {url}")

            # Navegação (Timeout aumentado para 60s por causa do Proxy)
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # Verifica bloqueios HTTP
            if response.status == 403 or response.status == 503:
                return {"error": f"Bloqueio detectado. Status: {response.status}. Troque o Proxy."}

            # Simula comportamento humano
            await simulate_human_behavior(page)

            # Aguarda carregamento final
            await page.wait_for_timeout(3000)

            content = await page.content()

            # Validação simples de segurança do ML
            if "suspicious-traffic" in content or "account-verification" in content:
                return {"error": "Soft Block: O Mercado Livre pediu verificação. O Proxy pode estar sujo."}

            return {"html": content}

        except Exception as e:
            return {"error": str(e)}

        finally:
