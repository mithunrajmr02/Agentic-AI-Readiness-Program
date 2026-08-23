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


def seed_default_admin():
    """Create the bootstrap manager account at startup.

    `ensure_default_user` was previously invoked only from the tokenless and
    `test_token` bypass branches in `get_current_user`. Those branches are gone,
    so without this call a fresh database would hold no users and every client --
    the React app, the MCP server, both agent layers -- would have nothing to log
    in with.
    """
    db = SessionLocal()
    try:
        from src.backend.routers.auth import ensure_default_user, DEFAULT_ADMIN_EMAIL

        ensure_default_user(db)
        logger.info("default_admin_ready", user_email=DEFAULT_ADMIN_EMAIL, poc_id="POC-07", phase="P1")
    except Exception as exc:
        db.rollback()
        logger.error("default_admin_seed_error", error=str(exc), poc_id="POC-07", phase="P1")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_default_admin()
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

# `allow_origins=["*"]` with `allow_credentials=True` is not the inert
# combination it is often assumed to be. Measured against this running service:
# Starlette does not echo a literal `*` when credentials are allowed -- it
# reflects the request's own Origin back and adds `Access-Control-Allow-Credentials:
# true` plus `Vary: Origin`. A request from `https://evil.example.com` was
# answered with `access-control-allow-origin: https://evil.example.com`, and the
# preflight authorised DELETE/PATCH/POST/PUT. Any page the operator visits while
# holding a token could therefore drive the whole inventory API from their
# browser. An explicit allowlist is the fix; the default covers the two dev
# origins this repo actually serves (Vite on 3000 per vite.config.js:7, Streamlit
# on 8501).
_default_origins = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501,http://127.0.0.1:8501"
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
    # `exc.headers` must be forwarded. This handler replaces FastAPI's own, and
    # by dropping the headers it silently discarded the `WWW-Authenticate: Bearer`
    # challenge that every 401 from get_current_user sets -- leaving the API
    # non-compliant with RFC 7235 and giving clients nothing to key retry logic on.
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "poc_id": "POC-07", "phase": "P1"},
        headers=getattr(exc, "headers", None),
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

