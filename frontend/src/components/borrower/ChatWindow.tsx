"use client";

import { useEffect, useRef } from "react";

import type { ChatTurn } from "@/lib/api/borrowerChat";
import { ChatMessage } from "@/components/borrower/ChatMessage";

export function ChatWindow({ turns, loading }: { turns: ChatTurn[]; loading?: boolean }) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, loading]);

  return (
    <div className="flex h-[460px] flex-col gap-4 overflow-y-auto rounded-lg border border-border bg-surface p-4">
      {turns.length === 0 && !loading ? (
        <div className="flex flex-1 flex-col items-center justify-center text-center text-sm text-muted-foreground">
          <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-muted text-base font-semibold">
            AI
          </div>
          <p className="font-medium text-foreground">Let&rsquo;s get started</p>
          <p>Introduce yourself and we&rsquo;ll guide you through the application.</p>
        </div>
      ) : (
        turns.map((turn) => <ChatMessage key={turn.id} turn={turn} />)
      )}
      {loading ? <TypingIndicator /> : null}
      <div ref={endRef} />
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-semibold text-muted-foreground">
        AI
      </div>
      <div className="inline-flex items-center gap-1 rounded-2xl rounded-bl-sm bg-muted px-4 py-3">
        <span className="h-2 w-2 animate-blink rounded-full bg-muted-foreground [animation-delay:0ms]" />
        <span className="h-2 w-2 animate-blink rounded-full bg-muted-foreground [animation-delay:200ms]" />
        <span className="h-2 w-2 animate-blink rounded-full bg-muted-foreground [animation-delay:400ms]" />
      </div>
    </div>
  );
}
