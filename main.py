import asyncio
import random
from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import uvicorn

app = FastAPI()

# User-Agents rotativos de Alta Qualidade (Chrome Windows/Mac)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36'
]

async def simulate_human_behavior(page):
    """Simula comportamento humano mais natural"""
    try:
        # Movimentos suaves
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Scroll lento (como alguém lendo)
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

            browser = await p.chromium.launch(
                headless=True, # Mantém true, mas usamos o argumento 'new' abaixo
                args=[
                    "--headless=new", # O SEGREDO: Novo modo headless indetectável
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certifcate-errors",
                    "--ignore-certificate-errors-spki-list",
                ]
            )

            # Contexto ultra-realista
            context = await browser.new_context(
                user_agent=current_ua,
                viewport={'width': 1920, 'height': 1080},
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                # Headers que dizem "Eu vim do Google"
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

            page = await context.new_page()

            # Aplica stealth
            await stealth_async(page)

            # REMOVIDO: await page.route("**/*", abort...)
            # Motivo: Bloquear CSS/Imagens é o maior sinal de bot hoje em dia.
            # Deixe o site carregar completo para parecer humano.

            # Navegação
            print(f"Acessando: {url}")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # Verificação de status
            if response.status == 403 or response.status == 503:
                return {"error": "Bloqueio de IP detectado (403/503)"}

            # Simula humano
            await simulate_human_behavior(page)

            # Aguarda renderização final
            await page.wait_for_timeout(3000)

            # Extrai HTML
            content = await page.content()

            # Pequena validação se pegou a página de erro
            if "suspicious-traffic" in content or "account-verification" in content:
                return {"error": "Soft Block: Redirecionado para Verificação de Segurança"}

            return {"html": content}

        except Exception as e:
            return {"error": str(e)}

        finally:
            if browser:
                await browser.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
