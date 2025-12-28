from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
import uvicorn
import random
import asyncio

app = FastAPI()

# Lista de User-Agents rotativos para parecer usuários diferentes
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0 Safari/537.36'
]

async def simulate_human_behavior(page):
    """Simula movimentos humanos básicos"""
    try:
        # Move o mouse aleatoriamente
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        # Scroll suave para baixo
        await page.mouse.wheel(0, random.randint(300, 700))
        await asyncio.sleep(random.uniform(1, 3)) # Espera aleatória
        # Scroll um pouco para cima
        await page.mouse.wheel(0, -100)
    except:
        pass

@app.get("/scrape")
async def scrape(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    async with async_playwright() as p:
        # Escolhe um User-Agent aleatório
        user_agent = random.choice(USER_AGENTS)

        # Configura o browser com argumentos anti-detecção mais fortes
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )

        # Contexto com Locale e Timezone do Brasil (Importante para ML)
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            geolocation={'latitude': -23.5505, 'longitude': -46.6333}, # SP
            permissions=['geolocation'],
            # Headers extras para fingir que veio do Google
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/',
                'sec-ch-ua-platform': '"Windows"',
                'Upgrade-Insecure-Requests': '1'
            }
        )

        # Injeta script para esconder o driver de automação
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = await context.new_page()

        try:
            # Otimização: Bloqueia imagens/fontes para economizar RAM e banda
            await page.route("**/*", lambda route: route.abort()
                if route.request.resource_type in ["image", "media", "font", "stylesheet"]
                else route.continue_())

            # Vai para a página
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)

            # Comportamento humano
            await simulate_human_behavior(page)

            # Espera extra para garantir carregamento dinâmico
            await page.wait_for_timeout(2000)

            content = await page.content()
            return {"html": content}

        except Exception as e:
            return {"error": str(e)}
        finally:
            await browser.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
