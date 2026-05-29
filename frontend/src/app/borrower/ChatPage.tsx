"use client";

import { useEffect, useMemo, useState } from "react";

import { ChatInput } from "@/components/borrower/ChatInput";
import { ChatWindow } from "@/components/borrower/ChatWindow";
import { DocumentUploadCard } from "@/components/borrower/DocumentUploadCard";
import { StatusPanel } from "@/components/borrower/StatusPanel";
import {
  getBorrowerChatHistory,
  sendBorrowerMessage,
  type CapturedField,
  type ChatTurn,
} from "@/lib/api/borrowerChat";
import { getBorrowerApplication } from "@/lib/api/borrowerApplication";
import { getBorrowerToken } from "@/lib/auth";

const TOTAL_REQUIRED = 8;

export default function ChatPage() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [capturedFields, setCapturedFields] = useState<CapturedField[]>([]);
  const [currentField, setCurrentField] = useState<string | null>(null);
  const [completed, setCompleted] = useState(0);
  const [totalRequired, setTotalRequired] = useState(TOTAL_REQUIRED);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const token = useMemo(() => getBorrowerToken(), []);

  useEffect(() => {
    async function loadHistory() {
      if (!token) {
        setError("No borrower session found. Please log in first.");
        return;
      }
      try {
        const history = await getBorrowerChatHistory(token);
        setTurns(history);
        const lastAssistant = [...history].reverse().find((t) => t.role === "assistant");
        const payload = lastAssistant?.structured_payload ?? {};
        const mf = (payload.missing_fields ?? []) as string[];
        setMissingFields(Array.isArray(mf) ? mf : []);
        setCapturedFields(
          Array.isArray(payload.captured_fields)
            ? (payload.captured_fields as CapturedField[])
            : []
        );
        setCurrentField((payload.current_field as string | null) ?? (mf[0] ?? null));
        if (typeof payload.completed === "number") setCompleted(payload.completed);
        if (typeof payload.total_required === "number") setTotalRequired(payload.total_required);

        const app = await getBorrowerApplication(token);
        if (app.approved_borrower_message) {
          setTurns((prev) => {
            const hasSystem = prev.some((t) => t.role === "system");
            if (hasSystem) return prev;
            return [
              ...prev,
              {
                id: -1,
                role: "system",
                content: app.approved_borrower_message!,
                structured_payload: {},
              },
            ];
          });
        }
      } catch (e) {
        setError("Failed to load chat history.");
      }
    }
    loadHistory();
  }, [token]);

  async function onSend(message: string) {
    if (!token) {
      setError("No borrower session found. Please log in first.");
      return;
    }
    setLoading(true);
    setError("");
    const borrowerTurn: ChatTurn = {
      id: Date.now(),
      role: "borrower",
      content: message,
      structured_payload: {},
    };
    setTurns((prev) => [...prev, borrowerTurn]);
    try {
      const res = await sendBorrowerMessage(token, message);
      setMissingFields(res.missing_fields);
      setCapturedFields(res.captured_fields);
      setCurrentField(res.current_field);
      setCompleted(res.completed);
      setTotalRequired(res.total_required);
      setTurns((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: res.assistant_message,
          structured_payload: { missing_fields: res.missing_fields },
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send message.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid gap-5 lg:grid-cols-[2fr_1fr]">
      <section className="flex flex-col gap-3">
        <ChatWindow turns={turns} loading={loading} />
        <ChatInput onSend={onSend} disabled={loading} />
        <DocumentUploadCard
          onUploaded={(doc) => {
            setTurns((prev) => [
              ...prev,
              {
                id: Date.now() + 2,
                role: "assistant",
                content: `Received ${doc.original_filename} (${doc.predicted_type}, ${doc.extraction_status}).`,
                structured_payload: {},
              },
            ]);
          }}
        />
        {error ? (
          <p className="rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>
        ) : null}
      </section>
      <StatusPanel
        capturedFields={capturedFields}
        missingFields={missingFields}
        currentField={currentField}
        completed={completed}
        total={totalRequired}
      />
    </main>
  );
}
