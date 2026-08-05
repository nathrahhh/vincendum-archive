from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import models
from app.api.routes import (
    breaches,
    client_applications,
    client_financials,
    clients,
    deals,
    forecast,
    lenders,
    parsing,
    portfolio,
    users,
)
from app.db import SessionLocal, init_db
from app.models.schemas import HealthResponse
from app.services.portfolio_store import seed_portfolio_if_empty

app = FastAPI(
    title="Credit Risk + Concentration Risk Engine",
    description=(
        "Pre-trade / pre-deal risk checks for private lending portfolios. "
        "Evaluates industry and single-name concentration against policy limits."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://204.168.230.152:5173",
    ],
    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio.router)
app.include_router(deals.router)
app.include_router(breaches.router)
app.include_router(forecast.router)
app.include_router(clients.router)
app.include_router(client_financials.router)
app.include_router(client_applications.router)
app.include_router(parsing.router)
app.include_router(lenders.router)
app.include_router(users.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return HealthResponse()
