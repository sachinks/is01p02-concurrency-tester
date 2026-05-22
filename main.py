import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from handlers.sync_handler import router as sync_router
from handlers.async_handler import router as async_router
from handlers.fake_handler import router as fake_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient(timeout=120.0)
    yield
    await app.state.client.aclose()

app = FastAPI(lifespan=lifespan)

app.include_router(sync_router)
app.include_router(async_router)
app.include_router(fake_router)
