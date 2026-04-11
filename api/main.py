"""
Stock Screener API

Run with:  cd api && uvicorn main:app --reload
Docs at:   http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.stocks import router as stocks_router
from routes.prices import router as prices_router
from routes.sync import router as sync_router

app = FastAPI(title="Stock Screener API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks_router)
app.include_router(prices_router)
app.include_router(sync_router)


@app.get("/")
def health():
    return {"status": "ok", "app": "stock-screener"}
