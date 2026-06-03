from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.borrower_application import router as borrower_application_router
from app.api.borrower_chat import router as borrower_chat_router
from app.api.deals import router as deals_router
from app.api.documents import router as documents_router
from app.api.eligibility import router as eligibility_router
from app.api.extractions import router as extractions_router
from app.api.messages import router as messages_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger, request_id_middleware
from app.db.session import SessionLocal
from app.observability import configure_observability
from app.services.storage import get_storage


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title="Loan Officer Copilot MVP")
    configure_observability(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(request_id_middleware)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        get_logger().exception(
            "unhandled_exception",
            path=request.url.path,
            error=str(exc),
        )
        return JSONResponse(status_code=500, content={"error": "internal_error"})

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz():
        checks: dict[str, str] = {}
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"
        finally:
            db.close()

        try:
            get_storage()
            checks["storage"] = "ok"
        except Exception as exc:
            checks["storage"] = f"error: {exc}"

        if settings.effective_document_parser() == "llamaindex":
            checks["llama_cloud_key"] = (
                "ok" if settings.LLAMA_CLOUD_API_KEY.strip() else "missing"
            )

        checks["bedrock_config"] = "ok" if settings.BEDROCK_MODEL_ID else "missing"
        checks["observability_provider"] = settings.effective_observability_provider()

        critical_ok = checks["database"] == "ok" and checks["storage"] == "ok"
        if settings.effective_document_parser() == "llamaindex":
            critical_ok = critical_ok and checks.get("llama_cloud_key") == "ok"

        body = {
            "status": "ready" if critical_ok else "degraded",
            "checks": checks,
        }
        return JSONResponse(status_code=200 if critical_ok else 503, content=body)

    app.include_router(auth_router)
    app.include_router(deals_router)
    app.include_router(borrower_chat_router)
    app.include_router(borrower_application_router)
    app.include_router(documents_router)
    app.include_router(extractions_router)
    app.include_router(eligibility_router)
    app.include_router(messages_router)
    return app


app = create_app()
