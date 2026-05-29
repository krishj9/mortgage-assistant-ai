import { apiFetch } from "@/lib/api/client";

export type DealMessages = {
  deal_id: number;
  internal_draft: string;
  borrower_draft: string;
  internal_approved: boolean;
  borrower_approved: boolean;
  approved_by_user_id: number | null;
  approved_at: string | null;
};

export async function getDealMessages(token: string, dealId: number): Promise<DealMessages> {
  return apiFetch<DealMessages>(`/deals/${dealId}/messages`, { token });
}

export async function updateDealMessages(
  token: string,
  dealId: number,
  body: { internal_draft?: string; borrower_draft?: string }
): Promise<DealMessages> {
  return apiFetch<DealMessages>(`/deals/${dealId}/messages`, {
    method: "PUT",
    token,
    body: JSON.stringify(body),
  });
}

export async function approveDealMessages(
  token: string,
  dealId: number,
  channel: "internal" | "borrower",
  approved = true
): Promise<DealMessages> {
  return apiFetch<DealMessages>(`/deals/${dealId}/messages/approve`, {
    method: "POST",
    token,
    body: JSON.stringify({ channel, approved }),
  });
}
