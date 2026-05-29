"use client";

import { useEffect, useState } from "react";

import type { DealMessages } from "@/lib/api/messages";
import { approveDealMessages, getDealMessages, updateDealMessages } from "@/lib/api/messages";
import { Button } from "@/components/ui/Button";

export function MessageApprovalPanel({ token, dealId }: { token: string; dealId: number }) {
  const [messages, setMessages] = useState<DealMessages | null>(null);
  const [internalDraft, setInternalDraft] = useState("");
  const [borrowerDraft, setBorrowerDraft] = useState("");
  const [status, setStatus] = useState("");

  async function load() {
    const data = await getDealMessages(token, dealId);
    setMessages(data);
    setInternalDraft(data.internal_draft);
    setBorrowerDraft(data.borrower_draft);
  }

  useEffect(() => {
    load().catch((e) => setStatus(e instanceof Error ? e.message : "Load failed"));
  }, [token, dealId]);

  async function onSave() {
    setStatus("Saving…");
    try {
      const data = await updateDealMessages(token, dealId, {
        internal_draft: internalDraft,
        borrower_draft: borrowerDraft,
      });
      setMessages(data);
      setStatus("Drafts saved.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Save failed");
    }
  }

  async function onApprove(channel: "internal" | "borrower") {
    setStatus("");
    try {
      const data = await approveDealMessages(token, dealId, channel, true);
      setMessages(data);
      setStatus(`${channel} message approved.`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Approve failed");
    }
  }

  if (!messages && !status) return <p className="text-sm text-muted-foreground">Loading messages…</p>;

  return (
    <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
      <section>
        <h3 className="mb-2 text-base font-semibold text-foreground">Internal notes</h3>
        <textarea
          value={internalDraft}
          onChange={(e) => setInternalDraft(e.target.value)}
          rows={12}
          className="w-full rounded-md border border-input bg-surface p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="mt-2"
          disabled={!internalDraft.trim()}
          onClick={() => onApprove("internal")}
        >
          {messages?.internal_approved ? "Internal approved ✓" : "Approve internal"}
        </Button>
      </section>
      <section>
        <h3 className="mb-2 text-base font-semibold text-foreground">Borrower-facing message</h3>
        <textarea
          value={borrowerDraft}
          onChange={(e) => setBorrowerDraft(e.target.value)}
          rows={12}
          className="w-full rounded-md border border-input bg-surface p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <Button
          type="button"
          size="sm"
          className="mt-2"
          disabled={!borrowerDraft.trim()}
          onClick={() => onApprove("borrower")}
        >
          {messages?.borrower_approved ? "Borrower approved ✓" : "Approve for borrower"}
        </Button>
      </section>
      <div className="md:col-span-2 flex items-center gap-3">
        <Button type="button" variant="secondary" size="sm" onClick={onSave}>
          Save drafts
        </Button>
        {status ? <span className="text-sm text-muted-foreground">{status}</span> : null}
      </div>
    </div>
  );
}
