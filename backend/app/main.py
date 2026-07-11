"""App FastAPI: CORS, routers, manejo de errores uniforme, auto-seed y /health."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config, logging_util
from .db import get_connection, init_schema, is_empty
from .errors import error_body
from .repositories import categories as cat_repo
from .routers import (
    admin,
    budgets,
    categories,
    chat,
    goals,
    imports,
    reports,
    transactions,
)
from .services import seed as seed_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea el esquema y siembra si la BD está vacía (FR-027).
    init_schema()
    conn = get_connection()
    try:
        cat_repo.seed_system_categories(conn)
        if is_empty(conn):
            logging_util.event("startup.autoseed", empty=True)
            seed_service.generate(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="Asistente de Finanzas IA — API (Demo)", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Manejo de errores uniforme (nunca expone datos sensibles) ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        body = detail
    else:
        body = error_body("http_error", str(detail))
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Mensajes de campo sin volcar los valores enviados (privacidad).
    details = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
    logging_util.error("request.validation", "validation_error", count=len(details))
    return JSONResponse(
        status_code=422,
        content=error_body("validation_error", "Datos inválidos.", details),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging_util.error("request.unhandled", "internal_error", detail=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content=error_body("internal_error", "Ocurrió un error interno."),
    )


# --- Routers ---
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(reports.router)
app.include_router(imports.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    # Nunca expone la clave; solo si hay IA disponible.
    return {"status": "ok", "ai_available": config.ai_available()}
