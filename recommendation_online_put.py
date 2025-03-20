import requests

# Укажите URL для вашего сервиса рекомендаций
events_store_url = "http://127.0.0.1:8020"

headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
params = {"user_id": 1291248, "item_id": 17245}

# Поскольку параметры передаются в теле запроса, используем json=params
resp = requests.post(events_store_url + "/put", headers=headers, params=params)

if resp.status_code == 200:
    result = resp.json()
else:
    result = None
    print(f"status code: {resp.status_code}")
    
print(result)