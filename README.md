# is01p02-concurrency-tester
Blocking on an LLM call is not a performance problem — it is an architectural failure. One synchronous 4-second LLM call queues every subsequent user. Async I/O solves this through cooperative suspension. The difference must be measured with real numbers, not described.
