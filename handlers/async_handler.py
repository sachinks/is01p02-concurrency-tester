import httpx
import time
from fastapi import APIRouter, Request
from config import settings

router = APIRouter()

@router.post("/async/chat")
async def async_chat(prompt: str, request: Request) -> dict:
    client: httpx.AsyncClient = request.app.state.client
    start = time.perf_counter()
    response = await client.post(
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