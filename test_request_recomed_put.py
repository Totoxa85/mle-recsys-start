import requests

# Укажите URL для вашего сервиса рекомендаций
recommendations_url = "http://127.0.0.1:8000"
events_store_url = "http://127.0.0.1:8020"


headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
user_id = 1291250
event_item_ids =  [7144, 16299, 5907, 18135]

for event_item_id in event_item_ids:
    resp = requests.post(events_store_url + "/put", 
                         headers=headers, 
                         params={"user_id": user_id, "item_id": event_item_id})
    
if resp.status_code == 200:
    result = resp.json()
else:
    result = None
    print(f"status code: {resp.status_code}")
    
print(result)