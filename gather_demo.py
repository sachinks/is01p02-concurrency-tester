import asyncio
import httpx
import time
from config import settings

async def call_llm(client: httpx.AsyncClient, prompt: str) -> str:
    r = await client.post(
        f"{settings.openai_base_url}/chat/completions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json={
            "model": settings.model_name,
            "messages": [{"role": "user", "content": prompt}]
        },
    )
    return r.json()["choices"][0]["message"]["content"]

async def sequential_calls(prompts: list[str]) -> list[str]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        results = []
        for prompt in prompts:
            results.append(await call_llm(client, prompt))
        return results

async def parallel_calls(prompts: list[str]) -> list[str]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await asyncio.gather(
            *[call_llm(client, p) for p in prompts]
        )

async def main():
    prompts = [f"Reply in one word only. What is number {i}?" for i in range(5)]

    t0 = time.perf_counter()
    await sequential_calls(prompts)
    seq_time = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    await parallel_calls(prompts)
    par_time = (time.perf_counter() - t0) * 1000

    print(f"Sequential 5 calls: {seq_time:.0f}ms")
    print(f"Parallel   5 calls: {par_time:.0f}ms")
    print(f"Speedup: {seq_time/par_time:.1f}x")

asyncio.run(main())