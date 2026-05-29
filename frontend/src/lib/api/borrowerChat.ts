import { apiFetch } from "@/lib/api/client";

export type ChatTurn = {
  id: number;
  role: "borrower" | "assistant" | "system";
  content: string;
  structured_payload: Record<string, unknown>;
};

export type CapturedField = {
  path: string;
  label: string;
  value: unknown;
};

export type IntakeProgress = {
  captured_fields: CapturedField[];
  current_field: string | null;
  completed: number;
  total_required: number;
};

export type BorrowerChatResponse = IntakeProgress & {
  assistant_message: string;
  application_snapshot: Record<string, unknown>;
  missing_fields: string[];
};

export async function sendBorrowerMessage(
  token: string,
  content: string
): Promise<BorrowerChatResponse> {
  return apiFetch<BorrowerChatResponse>("/borrower/chat/messages", {
    method: "POST",
    token,
    body: JSON.stringify({ content }),
  });
}

export async function getBorrowerChatHistory(token: string): Promise<ChatTurn[]> {
  return apiFetch<ChatTurn[]>("/borrower/chat/history", {
    method: "GET",
    token,
  });
}

export async function getBorrowerApplication(token: string): Promise<{
  deal_id: number;
  application: Record<string, unknown>;
}> {
  return apiFetch("/borrower/chat/application", { method: "GET", token });
}

