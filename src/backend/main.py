import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from src.backend.database import engine, Base, SessionLocal
from src.backend.logging_config import configure_logging
from src.backend.routers import auth, inventory

configure_logging()
logger = structlog.get_logger()


def seed_default_suppliers():
    db = SessionLocal()
    try:
        from src.backend.models import Supplier

        if db.query(Supplier).count() == 0:
            default_suppliers = [
                Supplier(
                    name="Reliable Wholesale Ltd",
                    supplier_code="SUP-0001",
                    contact_email="orders@reliablewholesale.com",
                    payment_terms_days=30,
                    lead_time_days=7,
                    is_active=True,
                ),
                Supplier(
                    name="Apex Logistics & Supplies",
                    supplier_code="SUP-0002",
                    contact_email="contact@apexlogistics.com",
                    payment_terms_days=15,
                    lead_time_days=3,
                    is_active=True,
                ),
                Supplier(
                    name="Metro Goods Distribution",
                    supplier_code="SUP-0003",
                    contact_email="sales@metrogoods.com",
                    payment_terms_days=45,
                    lead_time_days=10,
                    is_active=True,
                ),
            ]
            db.add_all(default_suppliers)
            db.commit()
            logger.info("suppliers_seeded", count=len(default_suppliers), poc_id="POC-07", phase="P1")
    except Exception as exc:
        db.rollback()
        logger.error("seed_error", error=str(exc), poc_id="POC-07", phase="P1")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_default_suppliers()
    yield


app = FastAPI(
    title="POC-07: Inventory Management & Procurement System",
    description="Retail domain inventory management platform REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.exception(
            "request_failed",
            poc_id="POC-07",
            phase="P1",
            operation=request.url.path,
            method=request.method,
            duration_ms=duration_ms,
            error=str(exc),
        )
        raise

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "http_request_completed",
        poc_id="POC-07",
        phase="P1",
        operation=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "poc_id": "POC-07", "phase": "P1"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", poc_id="POC-07", phase="P1", operation=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "poc_id": "POC-07", "phase": "P1"})


app.include_router(auth.router)
app.include_router(inventory.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "poc_id": "POC-07", "phase": "P1"}


@app.get("/")
def root():
    return {
        "message": "Welcome to POC-07 Retail Inventory Management & Procurement System API",
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend.main:app", host="127.0.0.1", port=8000, reload=True)

