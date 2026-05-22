import asyncio
import time
import statistics
import httpx
from config import settings

BASE_URL = "http://localhost:8000"

async def fetch(client: httpx.AsyncClient, url: str, method: str = "GET", params: dict = None) -> float:
    start = time.time()
    if method == "GET":
        await client.get(url)
    else:
        await client.post(url, params=params)
    end = time.time()
    return end - start

async def run_benchmark(
        url: str, label: str, concurrent: bool = True, method: str = "GET", params: dict = None) -> None:
    async with httpx.AsyncClient(timeout=300.0) as client:
        wall_start = time.time()
        if concurrent:
            tasks = [fetch(client, url, method, params) for _ in range(settings.concurrent_users)]
            times = list(await asyncio.gather(*tasks))
        else:
            times = []
            for _ in range(settings.concurrent_users):
                t = await fetch(client, url, method, params)
                times.append(t)
        wall_end = time.time()
        wall_time = wall_end - wall_start

    p50 = statistics.median(times)
    p95 = statistics.quantiles(times, n=20)[18]

    print(f"\n{label} BENCHMARK ({settings.concurrent_users} requests)")
    print(f"  P50 (median):  {p50:.3f}s")
    print(f"  P95:           {p95:.3f}s")
    print(f"  Total time:    {sum(times):.3f}s")
    print(f"  Wall time:     {wall_time:.3f}s")

async def main():
    ollama_params = {"prompt": settings.test_prompt}

    print("--- FAKE ENDPOINT (proves async) ---")
    await run_benchmark(f"{BASE_URL}/fake", "SYNC FAKE", concurrent=False)
    await run_benchmark(f"{BASE_URL}/fake", "ASYNC FAKE", concurrent=True)

    print("\n--- REAL OLLAMA (for reference) ---")
    await run_benchmark(f"{BASE_URL}/sync/chat", 
                        "SYNC OLLAMA", concurrent=True, method="POST", params=ollama_params)
    await run_benchmark(f"{BASE_URL}/async/chat", 
                        "ASYNC OLLAMA", concurrent=True, method="POST", params=ollama_params)

if __name__ == "__main__":
    asyncio.run(main())