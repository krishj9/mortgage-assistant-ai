"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { DocumentList } from "@/components/console/DocumentList";
import { DocumentViewer } from "@/components/console/DocumentViewer";
import { ExtractionReview } from "@/components/console/ExtractionReview";
import { listDocuments, type DocumentSummary } from "@/lib/api/documents";
import { getStaffToken } from "@/lib/auth";

export default function DealDocumentsPage() {
  const params = useParams();
  const dealId = Number(params.dealId);
  const token = getStaffToken();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    if (!token) return;
    listDocuments(token, dealId).then((docs) => {
      setDocuments(docs);
      if (docs.length > 0) setSelectedId(docs[0].id);
    });
  }, [token, dealId]);

  const selected = documents.find((d) => d.id === selectedId) ?? null;

  if (!token) return null;

  return (
    <div className="grid gap-5 md:grid-cols-[280px_1fr]">
      <aside>
        <h2 className="mb-3 text-lg font-semibold text-foreground">Documents</h2>
        <DocumentList documents={documents} selectedId={selectedId} onSelect={setSelectedId} />
      </aside>
      <section>
        {selected ? (
          <>
            <h2 className="mb-3 text-lg font-semibold text-foreground">{selected.original_filename}</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="mb-2 text-sm font-medium text-muted-foreground">Preview</h3>
                <DocumentViewer
                  token={token}
                  documentId={selected.id}
                  mimeType={selected.mime_type}
                  filename={selected.original_filename}
                />
              </div>
              <div>
                <ExtractionReview token={token} documentId={selected.id} />
              </div>
            </div>
          </>
        ) : (
          <p className="text-sm text-muted-foreground">Select a document to review.</p>
        )}
      </section>
    </div>
  );
}
