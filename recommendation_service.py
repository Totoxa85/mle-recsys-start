import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
import pandas as pd
import requests

logger = logging.getLogger("uvicorn.error")

features_store_url = "http://127.0.0.1:8010"
events_store_url = "http://127.0.0.1:8020"

class Recommendations:
    def __init__(self):
        self._recs = {"personal": None, "default": None}
        self._stats = {
            "request_personal_count": 0,
            "request_default_count": 0,
        }

    def load(self, type, path, **kwargs):
        """
        Загружает рекомендации из файла
        """
        logger.info(f"Loading recommendations, type: {type}")
        self._recs[type] = pd.read_parquet(path, **kwargs)
        if type == "personal":
            self._recs[type] = self._recs[type].set_index("user_id")
        logger.info(f"Loaded")

    def get(self, user_id: int, k: int = 100):
        """
        Возвращает список рекомендаций для пользователя
        """
        try:
            recs = self._recs["personal"].loc[user_id]
            recs = recs["item_id"].to_list()[:k]
            self._stats["request_personal_count"] += 1
        except KeyError:
            recs = self._recs["default"]
            recs = recs["item_id"].to_list()[:k]
            self._stats["request_default_count"] += 1
        except Exception as e:
            logger.error(f"No recommendations found: {e}")
            recs = []
        return recs

    def get_similar_items(self, item_id: int, k: int = 100):
        """
        Возвращает список похожих объектов для заданного item_id
        """
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        params = {"item_id": item_id, "k": k}
        resp = requests.post(features_store_url + "/similar_items", headers=headers, params=params)
        similar_items = resp.json()
        return similar_items

    def stats(self):
        logger.info("Stats for recommendations")
        for name, value in self._stats.items():
            logger.info(f"{name:<30} {value}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # код ниже (до yield) выполнится только один раз при запуске сервиса
    logger.info("Starting")
    rec_store = Recommendations()
    rec_store.load(
        "personal",
        "final_recommendations_feat.parquet",  # путь к файлу с персональными рекомендациями
        columns=["user_id", "item_id", "rank"],
    )
    rec_store.load(
        "default",
        "top_recs.parquet",  # путь к файлу с дефолтными рекомендациями
        columns=["item_id", "rank"],
    )
    app.state.recs = rec_store
    yield
    # этот код выполнится только один раз при остановке сервиса
    logger.info("Stopping")
    app.state.recs.stats()

# создаём приложение FastAPI
app = FastAPI(title="recommendations", lifespan=lifespan)

@app.post("/recommendations_offline")
async def recommendations_offline(user_id: int, k: int = 100):
    """
    Возвращает список офлайн-рекомендаций длиной k для пользователя user_id
    """
    recs = app.state.recs.get(user_id, k)
    return {"recs": recs}

@app.get("/second_item_for_user")
async def second_item_for_user(user_id: int = 1430468):
    recs = app.state.recs.get(user_id, 30)
    return {"recs": recs}

def dedup_ids(ids):
    """
    Дедублицирует список идентификаторов, оставляя только первое вхождение
    """
    seen = set()
    ids = [id for id in ids if not (id in seen or seen.add(id))]
    return ids

@app.post("/recommendations_online")
async def recommendations_online(user_id: int, k: int = 100):
    """
    Возвращает список онлайн-рекомендаций длиной k для пользователя user_id
    """
    headers = {"Content-type": "application/json", "Accept": "text/plain"}
    # получаем список последних событий пользователя, возьмём три последних
    params = {"user_id": user_id, "k": 3}
    resp = requests.post(events_store_url + "/get", headers=headers, params=params)
    events = resp.json()
    events = events.get("events", [])

    items = []
    scores = []

    for item_id in events:
        # для каждого item_id получаем список похожих
        similar_items_params = {"item_id": item_id, "k": k}
        similar_items_resp = requests.post(features_store_url + "/similar_items", headers=headers, params=similar_items_params)
        item_similar_items = similar_items_resp.json()

        # добавляем похожие айтемы и их оценки к общим спискам
        items += item_similar_items.get("item_id_2")
        scores += item_similar_items.get("score")

    # сортируем похожие объекты по scores в убывающем порядке
    combined = list(zip(items, scores))
    combined = sorted(combined, key=lambda x: x[1], reverse=True)
    combined = [item for item, _ in combined]

    # удаляем дубликаты, чтобы не выдавать одинаковые рекомендации
    recs = dedup_ids(combined)

    return {"recs": recs}

@app.post("/recommendations")
async def recommendations(user_id: int, k: int = 100):
    """
    Возвращает список рекомендаций длиной k для пользователя user_id
    """
    recs_offline = await recommendations_offline(user_id, k)
    recs_online = await recommendations_online(user_id, k)
    recs_offline = recs_offline["recs"]
    recs_online = recs_online["recs"]
    recs_blended = []
    min_length = min(len(recs_offline), len(recs_online))
    
    # Чередуем элементы из списков, пока позволяет минимальная длина
    for i in range(min_length):
        recs_blended.append(recs_offline[i])
        recs_blended.append(recs_online[i])
    
    # Добавляем оставшиеся элементы в конец
    recs_blended.extend(recs_offline[min_length:])
    recs_blended.extend(recs_online[min_length:])
    
    # Удаляем дубликаты
    recs_blended = dedup_ids(recs_blended)
    
    # Оставляем только первые k рекомендаций
    recs_blended = recs_blended[:k]
    
    return {"recs": recs_blended}