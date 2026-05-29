from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.borrower_application import router as borrower_application_router
from app.api.borrower_chat import router as borrower_chat_router
from app.api.deals import router as deals_router
from app.api.documents import router as documents_router
from app.api.eligibility import router as eligibility_router
from app.api.extractions import router as extractions_router
from app.api.messages import router as messages_router
from app.agents.tracing import configure_langsmith
from app.core.logging import configure_logging, request_id_middleware


def create_app() -> FastAPI:
    configure_logging()
    configure_langsmith()

    app = FastAPI(title="Loan Officer Copilot MVP")

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
        # MVP: return a generic payload. Logging is handled in middleware.
        return JSONResponse(status_code=500, content={"error": "internal_error"})

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

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

