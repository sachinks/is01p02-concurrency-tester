# is01p02-concurrency-tester
Blocking on an LLM call is not a performance problem — it is an architectural failure. One synchronous 4-second LLM call queues every subsequent user. Async I/O solves this through cooperative suspension. The difference must be measured with real numbers, not described.

Sleep demo:
  asyncio.sleep(1) × 10: 1002ms
  time.sleep(1)    × 10: 10005ms
  ratio: 10x

Gather demo:
  sequential 5 LLM calls: 8005ms
  parallel   5 LLM calls: 1849ms
  speedup: 4.3x