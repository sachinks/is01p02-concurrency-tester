import asyncio
import time
import statistics
import httpx
from config import settings

BASE_URL = "http://localhost:8000"

async def fetch(client: httpx.AsyncClient, url: str) -> float:
    start = time.time()
    await client.post(
        url,
        params={"prompt": settings.test_prompt}
    )
    end = time.time()
    return end - start

async def run_benchmark(url: str, label: str) -> None:
    async with httpx.AsyncClient(timeout=300.0) as client:
        tasks = [fetch(client, url) for _ in range(settings.concurrent_users)]
        times = await asyncio.gather(*tasks)

    times = list(times)
    p50 = statistics.median(times)
    p95 = statistics.quantiles(times, n=20)[18]

    print(f"\n{label} BENCHMARK ({settings.concurrent_users} requests)")
    print(f"  P50 (median):  {p50:.3f}s")
    print(f"  P95:           {p95:.3f}s")
    print(f"  Total time:    {sum(times):.3f}s")

async def main():
    await run_benchmark(f"{BASE_URL}/sync/chat", "SYNC")
    await run_benchmark(f"{BASE_URL}/async/chat", "ASYNC")

if __name__ == "__main__":
    asyncio.run(main())