import { apiFetch } from "@/lib/api/client";

export type DocumentSummary = {
  id: number;
  deal_id: number;
  original_filename: string;
  mime_type: string;
  predicted_type: string;
  classification_confidence: number;
  extraction_status: string;
};

export type DocumentProcessingEvent = {
  document_id: number;
  status: "pending" | "running" | "succeeded" | "failed";
  stage?: string;
  predicted_type?: string;
  classification_confidence?: number;
  error?: string | null;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function uploadDocument(token: string, file: File): Promise<DocumentSummary> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/documents`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new Error(data?.detail ?? `Upload failed (${res.status})`);
  }
  return data as DocumentSummary;
}

export async function getDocument(token: string, documentId: number): Promise<DocumentSummary> {
  return apiFetch<DocumentSummary>(`/documents/${documentId}`, {
    method: "GET",
    token,
  });
}

export async function listDocuments(token: string, dealId: number): Promise<DocumentSummary[]> {
  return apiFetch<DocumentSummary[]>(`/documents?deal_id=${dealId}`, { token });
}

export async function fetchDocumentFileBlob(token: string, documentId: number): Promise<Blob> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/file`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error(`Failed to load document file (${res.status})`);
  }
  return res.blob();
}

export function parseSseDataLine(line: string): DocumentProcessingEvent | null {
  if (!line.startsWith("data: ")) {
    return null;
  }
  try {
    return JSON.parse(line.slice(6)) as DocumentProcessingEvent;
  } catch {
    return null;
  }
}

export async function subscribeDocumentEvents(
  token: string,
  documentId: number,
  handlers: {
    onEvent: (event: DocumentProcessingEvent) => void;
    onError?: (error: Error) => void;
    signal?: AbortSignal;
  }
): Promise<DocumentProcessingEvent | null> {
  const { onEvent, onError, signal } = handlers;
  let lastEvent: DocumentProcessingEvent | null = null;

  try {
    const res = await fetch(`${API_BASE}/documents/${documentId}/events`, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "text/event-stream",
      },
      signal,
    });

    if (!res.ok || !res.body) {
      throw new Error(`Failed to subscribe to document events (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const chunk of parts) {
        for (const line of chunk.split("\n")) {
          const event = parseSseDataLine(line.trim());
          if (!event) {
            continue;
          }
          lastEvent = event;
          onEvent(event);
          if (event.status === "succeeded" || event.status === "failed") {
            return lastEvent;
          }
        }
      }
    }
  } catch (err) {
    if (signal?.aborted) {
      return lastEvent;
    }
    const error = err instanceof Error ? err : new Error("Document event stream failed");
    onError?.(error);
    throw error;
  }

  return lastEvent;
}
