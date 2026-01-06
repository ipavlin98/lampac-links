import asyncio
import json
import re
from playwright.async_api import async_playwright

INPUT_FILE = 'source.json'
OUTPUT_FILE = 'working_online_lampa.json'

CHECK_LAMPAC_BUTTON = False

TEST_QUERY = "/?card=1084242&media=movie&source=cub"

CONCURRENCY = 10
PAGE_LOAD_TIMEOUT = 40000
SELECTOR_TIMEOUT = 10000

async def check_server(context, item):
    page = await context.new_page()
    
    data = item.get('data', {})
    base_uri = data.get('uri')
    
    if not base_uri:
        ip = data.get('ip')
        port = data.get('port')
        protocol = data.get('protocol', 'http')
        if ip and port:
            base_uri = f"{protocol}://{ip}:{port}"
    
    if not base_uri:
        await page.close()
        return None

    if base_uri.endswith('/'):
        base_uri = base_uri[:-1]

    full_url = base_uri + TEST_QUERY

    print(f"Checking: {base_uri} -> ", end="", flush=True)

    result_data = None

    try:
        await page.goto(full_url, timeout=PAGE_LOAD_TIMEOUT, wait_until='domcontentloaded')
        
        try:
            lang_button = await page.wait_for_selector(".lang__selector-item[data-code='en']", state="visible", timeout=5000)
            if lang_button:
                print("Selecting language: English...")
                await lang_button.click()
                await asyncio.sleep(3)
        except:
            pass

        await asyncio.sleep(20)
        
        buttons = page.locator(".lampac--button", has_text=re.compile(r"Online", re.I))
        button_count = await buttons.count()
        has_button = button_count > 0
        
        body_text = await page.inner_text("body")
        body_text_lower = body_text.lower()
        has_password = "passw" in body_text_lower or "парол" in body_text_lower
        
        if CHECK_LAMPAC_BUTTON:
            if has_button and not has_password:
                print(f"✅ FOUND! {button_count} 'lampac--button' element(s) found.")
                result_data = {
                    "base_url": base_uri,
                    "full_check_url": full_url,
                    "ip": data.get('ip'),
                    "port": data.get('port'),
                    "status": "lampac_button_found"
                }
            elif has_password:
                print("🔑 Server requires a password (skipping).")
            else:
                print("⛔ No '.lampac--button' found on the page.")
        else:
            if not has_password:
                print(f"✅ FOUND! No password required.")
                result_data = {
                    "base_url": base_uri,
                    "full_check_url": full_url,
                    "ip": data.get('ip'),
                    "port": data.get('port'),
                    "status": "no_password"
                }
            else:
                print("🔑 Server requires a password (skipping).")
        
    except Exception as e:
        print(f"❌ Ошибка при проверке: {str(e)}")
        
    finally:
        await page.close()

    return result_data

async def main():
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"Файл {INPUT_FILE} не найден.")
        return

    if CHECK_LAMPAC_BUTTON:
        print(f"Loaded {len(raw_data)} addresses. Mode: checking '.lampac--button' + no password (passw/парол).")
    else:
        print(f"Loaded {len(raw_data)} addresses. Mode: checking ONLY no password (passw/парол).")
    print(f"Timeouts reduced for faster checking.")
    print(f"Test query: {TEST_QUERY}")
    print("-" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True
        )

        tasks = []
        sem = asyncio.Semaphore(CONCURRENCY)

        async def sem_task(item):
            async with sem:
                return await check_server(context, item)

        for item in raw_data:
            tasks.append(sem_task(item))

        results = await asyncio.gather(*tasks)
        
        valid_servers = [r for r in results if r is not None]

        print("-" * 60)
        print(f"Готово. Найдено полноценных серверов: {len(valid_servers)}")
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(valid_servers, f, indent=4, ensure_ascii=False)
            print(f"Результат сохранен в {OUTPUT_FILE}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())