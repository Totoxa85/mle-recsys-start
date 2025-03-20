import requests

# Укажите URL для вашего сервиса рекомендаций
recommendations_url = "http://127.0.0.1:8000"
events_store_url = "http://127.0.0.1:8020"


headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
params = {"user_id": 1291250, 'k': 10}
resp_offline = requests.post(recommendations_url + "/recommendations_offline", headers=headers, params=params)
resp_online = requests.post(recommendations_url + "/recommendations_online", headers=headers, params=params)
resp_blended = requests.post(recommendations_url + "/recommendations", headers=headers, params=params)

recs_offline = resp_offline.json()["recs"]
recs_online = resp_online.json()["recs"]
recs_blended = resp_blended.json()["recs"]

print(recs_offline)
print(recs_online)
print(recs_blended)