from fastapi import FastAPI

from app.api.routes import deals, portfolio
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

app.include_router(portfolio.router)
app.include_router(deals.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    with SessionLocal() as db:
        seed_portfolio_if_empty(db)


@app.get("/", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return HealthResponse()
