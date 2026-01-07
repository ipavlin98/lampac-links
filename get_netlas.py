import requests
import json
import time
import os

API_KEY = os.getenv("NETLAS_API_KEY", "YOUR_NETLAS_API_KEY") 

QUERY = '(http.title:"Lampa")'

OUTPUT_FILE = 'source.json'

MAX_RESULTS = 200

def get_netlas_data():
    if not API_KEY or API_KEY == "YOUR_NETLAS_API_KEY":
        print("❌ ОШИБКА: Ты не вставил API Key!")
        return

    url = "https://app.netlas.io/api/responses/"
    
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    all_items = []
    start_index = 0

    print(f"🔎 Начинаем поиск в Netlas...\nЗапрос: {QUERY}")

    try:
        while len(all_items) < MAX_RESULTS:
            params = {
                "q": QUERY,
                "start": start_index,
                "indices": "",
                "cnt": 200
            }

            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"❌ Ошибка API ({response.status_code}): {response.text}")
                break

            data = response.json()
            items = data.get('items', [])
            
            if not items:
                print("🏁 Больше результатов нет.")
                break

            all_items.extend(items)
            print(f"🔹 Загружено {len(items)} результатов (всего: {len(all_items)})")
            
            start_index += len(items)
            
            time.sleep(1)

            if len(items) < 20: 
                break

        final_data = all_items[:MAX_RESULTS]

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)

        print("-" * 40)
        print(f"✅ Готово! Результаты ({len(final_data)} шт.) сохранены в '{OUTPUT_FILE}'.")

    except Exception as e:
        print(f"❌ Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    get_netlas_data()
