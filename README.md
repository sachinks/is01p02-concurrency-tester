# IS01P02 — Concurrency Tester

**Layer 01 · Information Flow Architecture · Chapter 02**

> "Blocking on an LLM call is not a performance problem — it is an architectural failure."

---

## What this project measures

When a server handles LLM API calls synchronously, every user waits behind every other user. One 4-second LLM call means the second user waits 4 seconds before their request even starts. Twenty users means the last user waits 80 seconds. This project measures the difference between that broken pattern and the correct async pattern — using real latency numbers from a running server, not theory.

---

## How the asyncio event loop works

The event loop is a single-threaded scheduler that runs in a continuous loop. On each tick it does three things: it runs all callbacks currently in the ready queue, then calls the OS selector (`epoll` on Linux) to ask which file descriptors are ready for I/O, then moves any coroutines waiting on those descriptors back into the ready queue.

When your coroutine hits an `await`, Python suspends it at that exact line — saving the stack frame, local variables, and execution position — and hands the file descriptor to the OS selector. The loop is now free to run other coroutines. When the OS signals that the response is ready, the loop resumes the suspended coroutine from exactly where it paused.

The CPU is never idle during an `await`. It is polling the OS for I/O readiness on all registered sockets simultaneously. One thread. No parallelism. Cooperative concurrency only.

---

## The two async killers

**Killer 1 — Synchronous library inside an async handler**

Using a synchronous library like `requests` or `time.sleep` inside an async handler blocks the entire Python thread for the full duration of the call. No `await` is hit, so the event loop never gets control back. Every other coroutine queues behind it — turning your concurrent server back into a serial one.

```python
# WRONG — blocks the event loop
async def bad_handler(prompt: str):
    import requests
    response = requests.post(LLM_URL, json={...})  # blocks 4s, loop frozen

# CORRECT — yields to the event loop
async def good_handler(prompt: str):
    response = await httpx_client.post(LLM_URL, json={...})  # loop is free
```

Common traps: `requests` → use `httpx.AsyncClient`. `time.sleep()` → use `await asyncio.sleep()`. `psycopg2` → use `asyncpg`.

**Killer 2 — CPU-bound work inside an async handler**

Even with fully async code, CPU-intensive work blocks the event loop because the thread is executing Python bytecode continuously — no `await` is ever hit, so the loop never gets control back. Examples: PDF parsing, numpy operations, local model inference.

The fix is `ProcessPoolExecutor` — spawns separate processes, each with their own Python interpreter and GIL. That is true parallelism.

```python
from concurrent.futures import ProcessPoolExecutor
_pool = ProcessPoolExecutor()

async def good_handler(path: str):
    loop = asyncio.get_event_loop()
    pages = await loop.run_in_executor(_pool, parse_pdf_sync, path)
```

---

## Benchmark results

Tested on WSL Ubuntu, local Ollama (llama3.2), 10 concurrent requests.

| | Wall Time | P50 | P95 |
|---|---|---|---|
| SYNC FAKE (sequential) | 20.083s | 2.005s | 2.043s |
| ASYNC FAKE (concurrent) | **1.996s** | 1.992s | 1.995s |
| SYNC OLLAMA | 29.498s | 18.690s | 30.656s |
| ASYNC OLLAMA | 25.979s | 14.680s | 27.244s |

ASYNC FAKE is **10x faster** wall time than SYNC FAKE — because all 10 requests sleep simultaneously. Ollama shows smaller gains because it is single-threaded and queues requests internally regardless.

---

## asyncio.gather results

5 LLM calls to local Ollama (llama3.2).

```
Sequential 5 calls: 6614ms
Parallel   5 calls: 2157ms
Speedup:            3.1x
```

Why not 5x? Ollama is single-threaded — it processes one request at a time internally. Parallel calls save network and queuing overhead but not inference time. With a cloud LLM provider that handles true parallel inference, speedup would be closer to 4.5–5x.

---

## sleep demo results

10 concurrent calls, 1 second sleep each.

```
10x asyncio.sleep(1): 1002ms   — all 10 ran simultaneously
10x time.sleep(1):   10005ms   — ran one by one, loop was blocked
Ratio: 10.0x slower with time.sleep
```

`time.sleep` blocks the Python thread. `asyncio.sleep` suspends the coroutine and yields to the event loop. The 10x ratio proves the event loop was completely blocked each time `time.sleep` was called.

---

## GIL and asyncio

Asyncio does not bypass the GIL. It does not need to — asyncio runs entirely within a single thread, so there is never any competition for the GIL. The GIL only matters when multiple threads compete to execute Python bytecode simultaneously.

For I/O-bound work, the GIL is irrelevant because the bottleneck is the network, not Python computation. When a coroutine hits `await`, the OS selector call (`epoll_wait` on Linux) is a C-level syscall that releases the GIL while waiting. Other coroutines run under the same GIL in the meantime.

For CPU-bound work, the GIL is a real bottleneck. `ThreadPoolExecutor` cannot achieve true parallelism for Python code because threads still compete for the GIL. `ProcessPoolExecutor` is the correct tool — separate processes, separate GILs, true parallelism.

---

## BENEATH answer

**What is the event loop doing while an `await` is suspended — is the CPU idle?**

No. When a coroutine hits `await`, the event loop suspends it and registers its file descriptor with the OS selector. On Linux this is `epoll_wait` — a C-level syscall. While waiting for I/O, the loop runs other coroutines from the ready queue. The CPU is actively polling for socket readiness and processing other requests. Nothing is idle.

**I/O-bound vs CPU-bound — the fundamental difference**

I/O-bound work spends most of its time waiting for external responses — network, disk, database. The thread is blocked at the OS level, not executing Python. Asyncio converts that OS-level block into an event loop wait, freeing the thread to handle other coroutines. Example: LLM API call. Our benchmark proves this — ASYNC FAKE wall time was 1.996s vs SYNC FAKE 20.083s for 10 concurrent requests.

CPU-bound work executes Python bytecode continuously — no waiting, no I/O, no `await` ever hit. The loop never gets control back. Example: PDF parsing, numpy matrix operations. Asyncio provides zero benefit here. `ProcessPoolExecutor` is required — separate processes bypass the GIL and achieve true parallelism.

**Does asyncio bypass the GIL?**

No. Asyncio is single-threaded — one thread, one GIL, no competition. The GIL is simply not relevant. What makes async I/O fast is not bypassing the GIL — it is cooperative suspension at `await` points, which lets one thread handle many concurrent I/O waits without blocking. Our sleep demo confirms this: 10 concurrent `asyncio.sleep(1)` calls completed in 1002ms. 10 concurrent `time.sleep(1)` calls took 10005ms — because `time.sleep` holds the thread and blocks the loop, while `asyncio.sleep` yields and lets the loop run all 10 simultaneously.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
