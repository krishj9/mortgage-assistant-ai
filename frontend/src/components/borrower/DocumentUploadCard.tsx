"use client";

import { useState, type ChangeEvent } from "react";

import {
  subscribeDocumentEvents,
  uploadDocument,
  type DocumentProcessingEvent,
  type DocumentSummary,
} from "@/lib/api/documents";
import { getBorrowerToken } from "@/lib/auth";

const STAGE_LABELS: Record<string, string> = {
  queued: "queued",
  parsing: "parsing",
  classifying: "classifying",
  extracting: "extracting",
  merging: "merging",
};

function stageLabel(stage?: string): string {
  if (!stage) return "processing";
  return STAGE_LABELS[stage] ?? stage;
}

function toSummary(event: DocumentProcessingEvent, uploaded: DocumentSummary): DocumentSummary {
  return {
    ...uploaded,
    extraction_status: event.status,
    predicted_type: event.predicted_type ?? uploaded.predicted_type,
    classification_confidence:
      event.classification_confidence ?? uploaded.classification_confidence,
  };
}

export function DocumentUploadCard({
  onUploaded,
}: {
  onUploaded?: (doc: DocumentSummary) => void;
}) {
  const [status, setStatus] = useState<string>("");
  const [busy, setBusy] = useState(false);

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
    const controller = new AbortController();

    try {
      const uploaded = await uploadDocument(token, file);
      setStatus("Processing document...");

      const finalEvent = await subscribeDocumentEvents(token, uploaded.id, {
        signal: controller.signal,
        onEvent: (event) => {
          if (event.status === "running") {
            setStatus(`Processing… ${stageLabel(event.stage)}`);
          }
        },
        onError: () => {
          setStatus("Lost connection to processing stream. Check back shortly.");
        },
      });

      if (finalEvent?.status === "succeeded") {
        const finalDoc = toSummary(finalEvent, uploaded);
        setStatus(`Processed as ${finalDoc.predicted_type}.`);
        onUploaded?.(finalDoc);
      } else if (finalEvent?.status === "failed") {
        setStatus(finalEvent.error ?? "Document processing failed.");
      } else {
        setStatus("Processing ended before completion.");
      }
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
        Pay stub, W-2, or bank statement only (PDF, image, or text).
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
