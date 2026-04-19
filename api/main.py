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
from routes.momentum import router as momentum_router
from routes.reports import router as reports_router
from routes.valuation import router as valuation_router
from routes.revisions import router as revisions_router

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
app.include_router(momentum_router)
app.include_router(reports_router)
app.include_router(valuation_router)
app.include_router(revisions_router)


@app.get("/")
def health():
    return {"status": "ok", "app": "stock-screener"}
