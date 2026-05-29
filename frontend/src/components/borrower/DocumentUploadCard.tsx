"use client";

import { useState, type ChangeEvent } from "react";

import { getDocument, uploadDocument, type DocumentSummary } from "@/lib/api/documents";
import { getBorrowerToken } from "@/lib/auth";

export function DocumentUploadCard({
  onUploaded,
}: {
  onUploaded?: (doc: DocumentSummary) => void;
}) {
  const [status, setStatus] = useState<string>("");
  const [busy, setBusy] = useState(false);

  async function pollUntilDone(token: string, documentId: number) {
    for (let i = 0; i < 20; i++) {
      const doc = await getDocument(token, documentId);
      if (doc.extraction_status === "succeeded" || doc.extraction_status === "failed") {
        return doc;
      }
      await new Promise((r) => setTimeout(r, 500));
    }
    return getDocument(token, documentId);
  }

  async function onFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const token = getBorrowerToken();
    if (!token) {
      setStatus("Please log in at /borrower/login first.");
      return;
    }

    setBusy(true);
    setStatus(`Uploading ${file.name}...`);
    try {
      const uploaded = await uploadDocument(token, file);
      setStatus("Processing document...");
      const finalDoc = await pollUntilDone(token, uploaded.id);
      setStatus(
        finalDoc.extraction_status === "succeeded"
          ? `Processed as ${finalDoc.predicted_type}.`
          : `Processing ended with status: ${finalDoc.extraction_status}`
      );
      onUploaded?.(finalDoc);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  return (
    <div className="rounded-lg border border-dashed border-border bg-muted/30 p-4">
      <h3 className="text-sm font-semibold text-foreground">Upload a document</h3>
      <p className="mt-1 text-xs text-muted-foreground">
        Pay stub, W-2, bank statement, or application PDF (synthetic samples for MVP).
      </p>
      <input
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.txt"
        disabled={busy}
        onChange={onFileChange}
        className="mt-3 block w-full text-sm text-muted-foreground file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-2 file:text-sm file:font-medium file:text-primary-foreground hover:file:bg-primary/90 disabled:opacity-50"
      />
      {status ? <p className="mt-2 text-xs text-muted-foreground">{status}</p> : null}
    </div>
  );
}
