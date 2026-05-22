import asyncio
from fastapi import APIRouter

router = APIRouter()

@router.get("/fake")
async def fake():
    await asyncio.sleep(2)
    return {"response": "fake"}