import asyncio
import random
from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright, Page
from typing import Optional

app = FastAPI()

async def simulate_human_behavior(page: Page):
    """
    Simula comportamento humano para evitar detecção:
    - Move o mouse aleatoriamente
    - Espera entre 1 a 3 segundos
    - Scroll suave até a metade da página
    """
    # Movimento aleatório do mouse
    await page.mouse.move(random.randint(0, 500), random.randint(0, 500))
    await page.mouse.move(random.randint(0, 500), random.randint(0, 500))

    # Scroll suave
    # Pega a altura total da página (pode não ser precisa se for infinito, mas serve para o alvo)
    # Vamos fazer um scroll até mais ou menos o meio ou uma quantidade razoável
    viewport_size = page.viewport_size
    if viewport_size:
        height = viewport_size['height']
        # Faz um scroll de 500px a 1500px, suavemente
        await page.mouse.wheel(0, random.randint(500, 1500))

    # Espera aleatória
    await asyncio.sleep(random.uniform(1, 3))

@app.get("/scrape")
async def scrape(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL provided is empty")

    async with async_playwright() as p:
        # Argumentos para Stealth Mode
        browser = await p.chromium.launch(
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )

        try:
            # Contexto com User-Agent fixo e Viewport definido
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )

            # Otimização de recursos: Bloquear imagens, fontes, media, stylesheets
            await context.route("**/*", lambda route: route.abort()
                                if route.request.resource_type in ["image", "media", "font", "stylesheet"]
                                else route.continue_())

            page = await context.new_page()

            # Navegação
            # Tratamento específico para Shopee (SPA)
            wait_strategy = 'networkidle' if 'shopee' in url.lower() else 'domcontentloaded'

            try:
                await page.goto(url, wait_until=wait_strategy, timeout=60000) # 60s timeout
            except Exception as e:
                # Se der timeout mas carregou algo, tentamos prosseguir, ou lançamos erro
                # Nesse caso, vamos lançar erro para simplificar
                 raise HTTPException(status_code=500, detail=f"Failed to load page: {str(e)}")

            # Humanização antes de extrair HTML
            await simulate_human_behavior(page)

            content = await page.content()
            return {"html": content}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            await browser.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
