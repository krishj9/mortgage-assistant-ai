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

export async function uploadDocument(token: string, file: File): Promise<DocumentSummary> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/documents`, {
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
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/documents/${documentId}/file`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!res.ok) {
    throw new Error(`Failed to load document file (${res.status})`);
  }
  return res.blob();
}
