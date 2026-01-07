import requests
import json
import time
import os

CENSYS_API_TOKEN = os.getenv("CENSYS_API_TOKEN", "YOUR_CENSYS_API_TOKEN")

QUERY = 'host.services.endpoints.http.html_title="Lampa - Каталог фильмов и сериалов"'
OUTPUT_FILE = 'censys_working_online_lampa.json'
MAX_RESULTS = 200
TEST_QUERY = "/?card=1084242&media=movie&source=cub"

def get_censys_data():
    if not CENSYS_API_TOKEN or CENSYS_API_TOKEN == "YOUR_CENSYS_API_TOKEN":
        print("❌ ОШИБКА: Ты не вставил Censys API Token!")
        return

    base_url = "https://api.platform.censys.io/v3/global/search/query"
    
    headers = {
        "Authorization": f"Bearer {CENSYS_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print(f"🔎 Начинаем поиск в Censys (v2 via search.censys.io)...\nЗапрос: {QUERY}")
    
    all_hits = []
    cursor = None

    try:
        while len(all_hits) < MAX_RESULTS:
            payload = {
                "query": QUERY,
                "page_size": 100
            }
            if cursor:
                payload["cursor"] = cursor

            response = requests.post(base_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 401:
                print(f"❌ Ошибка авторизации (401). Проверь токен. (Или этот эндпоинт требует ID/Secret)")
                print(f"Ответ сервера: {response.text}")
                break
            
            if response.status_code != 200:
                print(f"❌ Ошибка API ({response.status_code}): {response.text}")
                break

            data = response.json()
            hits = data.get('hits', [])
            
            if not hits:
                print("🏁 Больше результатов нет.")
                break

            all_hits.extend(hits)
            print(f"🔹 Загружено {len(hits)} результатов (всего: {len(all_hits)})")
            
            cursor = data.get('next_cursor')
            
            if not cursor:
                break
            
            time.sleep(1)

        formatted_servers = []
        
        for hit in all_hits[:MAX_RESULTS]:
            ip = hit.get('host', {}).get('ip') or hit.get('ip')
            services = hit.get('host', {}).get('services', []) or hit.get('services', [])
            location = hit.get('host', {}).get('location', {}) or hit.get('location', {})
            country_code = location.get('country_code')

            for service in services:
                service_name = service.get('service_name', '').upper()
                port = service.get('port')
                
                if service_name == 'HTTP':
                    protocol = 'http'
                    if port == 443:
                        protocol = 'https'
                    if service.get('extended_service_name') == 'HTTPS':
                         protocol = 'https'

                    base_uri = f"{protocol}://{ip}:{port}"
                    full_url = base_uri + TEST_QUERY

                    server_entry = {
                        "base_url": base_uri,
                        "full_check_url": full_url,
                        "ip": ip,
                        "port": port,
                        "country": country_code,
                        "status": "not_checked"
                    }
                    
                    formatted_servers.append(server_entry)

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(formatted_servers, f, indent=4, ensure_ascii=False)

        print("-" * 40)
        print(f"✅ Готово! Результаты ({len(formatted_servers)} шт.) сохранены в '{OUTPUT_FILE}'.")

    except Exception as e:
        print(f"❌ Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    get_censys_data()
