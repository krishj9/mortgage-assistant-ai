import { apiFetch } from "@/lib/api/client";

export type DocumentExtraction = {
  id: number;
  document_id: number;
  raw_ocr: Record<string, unknown>;
  normalized: Record<string, unknown>;
  confidence: Record<string, unknown>;
  human_corrections: Record<string, unknown>;
  status: string;
};

export async function getExtraction(
  token: string,
  documentId: number
): Promise<DocumentExtraction> {
  return apiFetch<DocumentExtraction>(`/documents/${documentId}/extraction`, { token });
}

export async function updateExtraction(
  token: string,
  documentId: number,
  humanCorrections: Record<string, unknown>
): Promise<DocumentExtraction> {
  return apiFetch<DocumentExtraction>(`/documents/${documentId}/extraction`, {
    method: "PUT",
    token,
    body: JSON.stringify({ human_corrections: humanCorrections }),
  });
}
