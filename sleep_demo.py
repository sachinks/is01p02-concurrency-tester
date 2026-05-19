import asyncio
import time

async def blocking_sleep():
    start = time.perf_counter()
    time.sleep(1)
    return (time.perf_counter() - start) * 1000

async def nonblocking_sleep():
    start = time.perf_counter()
    await asyncio.sleep(1)
    return (time.perf_counter() - start) * 1000

async def run_10_concurrent(fn):
    start = time.perf_counter()
    await asyncio.gather(*[fn() for _ in range(10)])
    return (time.perf_counter() - start) * 1000

async def main():
    nonblocking_ms = await run_10_concurrent(nonblocking_sleep)
    print(f"10x asyncio.sleep(1): {nonblocking_ms:.0f}ms")

    blocking_ms = await run_10_concurrent(blocking_sleep)
    print(f"10x time.sleep(1)   : {blocking_ms:.0f}ms")

    print(f"Ratio: {blocking_ms/nonblocking_ms:.1f}x slower with time.sleep")

asyncio.run(main())