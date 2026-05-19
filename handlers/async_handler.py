import httpx
import time
from fastapi import FastAPI
from contextlib import asynccontextmanager

from config import settings

_client: httpx.AsyncClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    _client = httpx.AsyncClient(timeout=30.0)
    yield
    await _client.aclose()

app = FastAPI(lifespan=lifespan)

@app.post("/async/chat")
async def async_chat(prompt: str) -> dict:
    start = time.perf_counter()

    response = await _client.post(
        f"{settings.openai_base_url}/chat/completions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json={
            "model": settings.model_name,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    response.raise_for_status()

    latency = time.perf_counter() - start
    return {
        "response": response.json()["choices"][0]["message"]["content"],
        "latency_ms": round(latency * 1000, 1),
        "handler": "async",
    }