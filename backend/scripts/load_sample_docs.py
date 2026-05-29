from __future__ import annotations

from pathlib import Path

from app.db.session import SessionLocal
from app.services import documents_service
from app.workers.document_pipeline import run_document_pipeline


def main() -> None:
    """
    Loads synthetic fixture files into storage for a given deal and runs extraction.
    Usage: DEAL_ID=1 uv run python -m scripts.load_sample_docs
    """
    import os

    deal_id = int(os.environ.get("DEAL_ID", "1"))
    fixtures = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "documents"
    db = SessionLocal()
    try:
        for path in fixtures.glob("*"):
            if not path.is_file():
                continue
            content = path.read_bytes()
            doc = documents_service.create_document(
                db=db,
                deal_id=deal_id,
                filename=path.name,
                mime_type="text/plain",
                content=content,
            )
            run_document_pipeline(doc.id)
            print(f"Loaded {path.name} as document {doc.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
