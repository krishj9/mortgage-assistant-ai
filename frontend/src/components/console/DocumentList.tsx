"use client";

import type { DocumentSummary } from "@/lib/api/documents";
import { cn } from "@/lib/cn";

export function DocumentList({
  documents,
  selectedId,
  onSelect,
}: {
  documents: DocumentSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <ul className="m-0 list-none space-y-2 p-0">
      {documents.length === 0 ? (
        <li className="text-sm text-muted-foreground">No documents uploaded.</li>
      ) : (
        documents.map((doc) => (
          <li key={doc.id}>
            <button
              type="button"
              onClick={() => onSelect(doc.id)}
              className={cn(
                "w-full rounded-md border p-3 text-left transition-colors",
                selectedId === doc.id
                  ? "border-primary bg-primary/5"
                  : "border-border bg-surface hover:bg-muted/40"
              )}
            >
              <div className="font-medium text-foreground">{doc.original_filename}</div>
              <div className="mt-0.5 text-xs text-muted-foreground">
                {doc.predicted_type} · {doc.extraction_status}
              </div>
            </button>
          </li>
        ))
      )}
    </ul>
  );
}
