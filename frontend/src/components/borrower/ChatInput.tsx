"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (message: string) => Promise<void>;
  disabled?: boolean;
}) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus();
    }
  }, [disabled]);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const message = value.trim();
    if (!message || disabled) return;
    setValue("");
    await onSend(message);
    inputRef.current?.focus();
  }

  return (
    <form onSubmit={submit} className="flex items-center gap-2">
      <Input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Type your response..."
        disabled={disabled}
        autoFocus
        className="flex-1"
      />
      <Button type="submit" disabled={disabled || !value.trim()}>
        Send
      </Button>
    </form>
  );
}
