"use client";

import { useEffect, useState } from "react";

import { fetchDocumentFileBlob } from "@/lib/api/documents";

export function DocumentViewer({
  token,
  documentId,
  mimeType,
  filename,
}: {
  token: string;
  documentId: number;
  mimeType: string;
  filename: string;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [textPreview, setTextPreview] = useState<string | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let objectUrl: string | null = null;
    setUrl(null);
    setTextPreview(null);
    setError("");

    async function load() {
      try {
        const blob = await fetchDocumentFileBlob(token, documentId);
        objectUrl = URL.createObjectURL(blob);
        if (mimeType.startsWith("text/") || filename.endsWith(".txt")) {
          const text = await blob.text();
          setTextPreview(text.slice(0, 8000));
          URL.revokeObjectURL(objectUrl);
        } else if (mimeType.startsWith("image/")) {
          setUrl(objectUrl);
        } else if (mimeType === "application/pdf") {
          setUrl(objectUrl);
        } else {
          setTextPreview(`Preview not available for ${mimeType}. Download via API.`);
          URL.revokeObjectURL(objectUrl);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load file");
      }
    }

    load();
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [token, documentId, mimeType, filename]);

  if (error) return <p className="text-sm text-danger">{error}</p>;
  if (textPreview !== null) {
    return (
      <pre className="max-h-[400px] overflow-auto rounded-md bg-muted p-3 text-xs text-foreground">
        {textPreview}
      </pre>
    );
  }
  if (url && mimeType === "application/pdf") {
    return <iframe src={url} title={filename} className="h-[420px] w-full rounded-md border border-border" />;
  }
  if (url) {
    return <img src={url} alt={filename} className="max-h-[420px] max-w-full rounded-md" />;
  }
  return <p className="text-sm text-muted-foreground">Loading preview…</p>;
}
