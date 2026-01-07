import json

INPUT_FILE = 'source.json'
OUTPUT_FILE = 'working_online_lampa.json'

TEST_QUERY = "/?card=1084242&media=movie&source=cub"

def main():
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"Файл {INPUT_FILE} не найден.")
        return

    print(f"Загружено {len(raw_data)} адресов. Форматирование...")
    print("-" * 60)
    
    valid_servers = []
    for item in raw_data:
        data = item.get('data', {})
        base_uri = data.get('uri')
        
        if not base_uri:
            ip = data.get('ip')
            port = data.get('port')
            protocol = data.get('protocol', 'http')
            if ip and port:
                base_uri = f"{protocol}://{ip}:{port}"
        
        if not base_uri:
            continue
        
        if base_uri.endswith('/'):
            base_uri = base_uri[:-1]
        
        full_url = base_uri + TEST_QUERY
        
        geo_data = data.get('geo', {})
        country_code = geo_data.get('country') if geo_data else None
        result_data = {
            "base_url": base_uri,
            "full_check_url": full_url,
            "ip": data.get('ip'),
            "port": data.get('port'),
            "country": country_code,
            "status": "not_checked"
        }
        valid_servers.append(result_data)
        print(f"Добавлен: {base_uri}")
    
    print("-" * 60)
    print(f"Готово. Добавлено серверов: {len(valid_servers)}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(valid_servers, f, indent=4, ensure_ascii=False)
        print(f"Результат сохранен в {OUTPUT_FILE}")

if __name__ == '__main__':
    main()