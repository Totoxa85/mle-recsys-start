import requests

# Укажите URL для вашего сервиса рекомендаций
recommendations_url = "http://127.0.0.1:8000"

headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
params = {"user_id": 1291248, 'k': 3}  # Убедитесь, что параметры передаются в теле запроса

# Поскольку параметры передаются в теле запроса, используем json=params
resp = requests.post(recommendations_url + "/recommendations_online", headers=headers, params=params)

if resp.status_code == 200:
    recs = resp.json()
else:
    recs = []

print(f"status code: {resp.status_code}")
print(recs)