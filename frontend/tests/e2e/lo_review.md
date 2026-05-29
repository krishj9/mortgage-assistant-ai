# LO review E2E checklist (manual)

Prerequisites: backend `:8000` with seed (`lo@example.com` / `password`), frontend `:3000`.

1. Staff logs in at `/console/login`
2. Open a `ready_for_review` deal from `/console/deals`
3. **Documents**: save an extraction correction
4. **Eligibility**: run eligibility, then approve
5. **Messages**: approve borrower-facing draft
6. Borrower `/borrower/chat` shows the approved message as a system turn
