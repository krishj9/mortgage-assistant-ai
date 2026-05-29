from __future__ import annotations

"""
Check Textract connectivity for the credentials in your environment.

Usage (from backend/):
  uv run python -m scripts.diagnose_textract
"""

import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings


def main() -> int:
    region = settings.TEXTRACT_REGION
    print(f"OCR_BACKEND={settings.OCR_BACKEND!r}")
    print(f"TEXTRACT_REGION={region!r}")
    print()

    sts = boto3.client("sts", region_name=region)
    identity = sts.get_caller_identity()
    print("Caller identity:")
    print(f"  Account: {identity['Account']}")
    print(f"  Arn:     {identity['Arn']}")
    print()

    sample = b"Employer: Acme Corp\nGross Pay: 8500.00\n"
    client = boto3.client("textract", region_name=region)
    print("Calling textract:DetectDocumentText (minimal sample)...")
    try:
        resp = client.detect_document_text(Document={"Bytes": sample})
        blocks = resp.get("Blocks", [])
        print(f"  OK — Textract responded ({len(blocks)} blocks).")
        return 0
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        msg = exc.response.get("Error", {}).get("Message", str(exc))
        print(f"  FAILED — {code}: {msg}")
        print()
        if code == "SubscriptionRequiredException":
            print("This is an AWS ACCOUNT activation issue, not IAM or app code.")
            print("Bedrock can work while Textract is still inactive — they are separate services.")
            print()
            print("Fix (root user or admin with billing access):")
            print(f"  1. Open https://{region}.console.aws.amazon.com/textract/home?region={region}")
            print("  2. Complete any 'Get started' / activation prompt")
            print("  3. Ensure account has verified payment method + phone (Account settings)")
            print("  4. Re-run: uv run python -m scripts.diagnose_textract")
            print()
            print("Until then, OCR_BACKEND=auto will fall back to local parsing for .txt uploads.")
        elif code in ("AccessDeniedException", "UnauthorizedException"):
            print("Attach AmazonTextractFullAccess (or textract:AnalyzeDocument) to your IAM user/role.")
        return 1
    except BotoCoreError as exc:
        print(f"  FAILED — {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
