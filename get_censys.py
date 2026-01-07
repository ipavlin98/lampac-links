import requests
import json
import time
import os
import base64

CENSYS_API_TOKEN = os.getenv("CENSYS_API_TOKEN", "YOUR_CENSYS_API_TOKEN")

QUERY = 'host.services.endpoints.http.html_title="Lampa - Каталог фильмов и сериалов"'

OUTPUT_FILE = 'censys_working_online_lampa.json'
MAX_RESULTS = 200

TEST_QUERY = "/?card=1084242&media=movie&source=cub"

def get_censys_data():
    if not CENSYS_API_TOKEN or CENSYS_API_TOKEN == "YOUR_CENSYS_API_TOKEN":
        print("❌ ОШИБКА: Ты не вставил Censys API Token!")
        return

    base_url = "https://search.censys.io/api/v2/hosts/search"
    
    headers = {
        "Authorization": f"Bearer {CENSYS_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    all_hits = []
    cursor = None
    
    print(f"🔎 Начинаем поиск в Censys...\nЗапрос: {QUERY}")

    try:
        while len(all_hits) < MAX_RESULTS:
            params = {
                "q": QUERY,
                "per_page": 100, 
                "virtual_hosts": "EXCLUDE"
            }
            if cursor:
                params["cursor"] = cursor

            response = requests.get(base_url, params=params, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Ошибка API ({response.status_code}): {response.text}")
                break

            data = response.json()
            result = data.get('result', {})
            hits = result.get('hits', [])
            
            if not hits:
                print("🏁 Больше результатов нет.")
                break

            all_hits.extend(hits)
            print(f"🔹 Загружено {len(hits)} результатов (всего: {len(all_hits)})")
            
            links = result.get('links', {})
            cursor = links.get('next')
            
            if not cursor:
                break
            
            time.sleep(1) 

        formatted_servers = []
        
        for hit in all_hits[:MAX_RESULTS]:
            ip = hit.get('ip')
            services = hit.get('services', [])
            location = hit.get('location', {})
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
