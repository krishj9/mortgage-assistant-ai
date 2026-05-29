"use client";

import { useEffect, useState } from "react";

import type { DocumentExtraction } from "@/lib/api/extractions";
import { getExtraction, updateExtraction } from "@/lib/api/extractions";
import { Button } from "@/components/ui/Button";

function isLowConfidence(confidence: Record<string, unknown>, key: string): boolean {
  const v = confidence[key];
  return typeof v === "number" && v < 0.75;
}

export function ExtractionReview({
  token,
  documentId,
}: {
  token: string;
  documentId: number;
}) {
  const [extraction, setExtraction] = useState<DocumentExtraction | null>(null);
  const [editorValue, setEditorValue] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setStatus("");
      try {
        const data = await getExtraction(token, documentId);
        setExtraction(data);
        const merged = { ...data.normalized, ...data.human_corrections };
        setEditorValue(JSON.stringify(merged, null, 2));
      } catch (e) {
        setStatus(e instanceof Error ? e.message : "Failed to load extraction");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [token, documentId]);

  async function onSave() {
    if (!extraction) return;
    setStatus("Saving…");
    try {
      const parsed = JSON.parse(editorValue) as Record<string, unknown>;
      const updated = await updateExtraction(token, documentId, parsed);
      setExtraction(updated);
      setStatus("Corrections saved.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Save failed (check JSON)");
    }
  }

  if (loading) return <p className="text-sm text-muted-foreground">Loading extraction…</p>;
  if (!extraction) return <p className="text-sm text-muted-foreground">{status || "No extraction available."}</p>;

  const lowKeys = Object.keys(extraction.confidence || {}).filter((k) =>
    isLowConfidence(extraction.confidence, k)
  );

  return (
    <div>
      <h3 className="text-sm font-semibold text-foreground">Extraction review</h3>
      {lowKeys.length > 0 ? (
        <p className="mt-1 text-xs text-warning">Low confidence: {lowKeys.join(", ")}</p>
      ) : null}
      <textarea
        value={editorValue}
        onChange={(e) => setEditorValue(e.target.value)}
        rows={16}
        className="mt-2 w-full rounded-md border border-input bg-surface p-2 font-mono text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
      <div className="mt-2 flex gap-2">
        <Button type="button" size="sm" onClick={onSave}>
          Save corrections
        </Button>
      </div>
      {status ? <p className="mt-2 text-xs text-muted-foreground">{status}</p> : null}
    </div>
  );
}
