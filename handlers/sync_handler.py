import requests
import time
from fastapi import FastAPI

from config import settings

app = FastAPI()

@app.post("/sync/chat")
def sync_chat(prompt: str) -> dict:
    start = time.perf_counter()

    response = requests.post(
        f"{settings.openai_base_url}/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json={
            "model": settings.model_name,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )

    latency = time.perf_counter() - start
    return {
        "response": response.json()["choices"][0]["message"]["content"],
        "latency_ms": round(latency * 1000, 1),
        "handler": "sync",
    }