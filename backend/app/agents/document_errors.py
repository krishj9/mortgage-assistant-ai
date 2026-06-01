from __future__ import annotations


class UnsupportedDocumentError(Exception):
    """Raised when a document is not a supported pay stub, W-2, or bank statement."""
