import asyncio
import random
from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import uvicorn

app = FastAPI()

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
        browser = None

        try:
            # Configura o browser com argumentos anti-detecção mais fortes
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--use-fake-ui-for-media-stream",
                    "--use-fake-device-for-media-stream",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ]
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )

            page = await context.new_page()

            # ATIVAR STEALTH MODE IMEDIATAMENTE
            await stealth_async(page)

            # Otimização: Bloqueia imagens/fontes para economizar RAM e banda
            await page.route("**/*", lambda route: route.abort()
                if route.request.resource_type in ["image", "media", "font", "stylesheet"]
                else route.continue_())

            # Vai para a página com timeout maior
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # Comportamento humano
            await simulate_human_behavior(page)

            # Espera extra para garantir carregamento dinâmico
            await page.wait_for_timeout(2000)

            content = await page.content()
            return {"html": content}

        except Exception as e:
            # Em caso de erro, tenta retornar o erro como json
            return {"error": str(e)}

        finally:
            if browser:
                await browser.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
