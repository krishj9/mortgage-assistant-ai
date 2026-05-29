import { apiFetch } from "@/lib/api/client";

export type EligibilityStatus = "green" | "yellow" | "red";

export type Condition = {
  id: string;
  code: string;
  title: string;
  rationale: string;
  required_doc_type?: string | null;
};

export type EligibilityPayload = {
  status: EligibilityStatus;
  dti?: number | null;
  ltv?: number | null;
  eligibility_approved?: boolean;
  rule_evaluations?: unknown[];
};

export async function runEligibility(token: string, dealId: number) {
  return apiFetch<{
    eligibility: EligibilityPayload;
    conditions: { items: Condition[] };
    messages: { internal_draft: string; borrower_draft: string };
    deal_status: string;
  }>(`/deals/${dealId}/eligibility/run`, { method: "POST", token });
}

export async function getEligibility(token: string, dealId: number) {
  return apiFetch<{ eligibility: EligibilityPayload; conditions: { items: Condition[] } }>(
    `/deals/${dealId}/eligibility`,
    { token }
  );
}

export async function patchEligibility(
  token: string,
  dealId: number,
  body: { status?: EligibilityStatus; conditions?: { items: Condition[] } }
) {
  return apiFetch(`/deals/${dealId}/eligibility`, {
    method: "PATCH",
    token,
    body: JSON.stringify(body),
  });
}

export async function approveEligibility(token: string, dealId: number) {
  return apiFetch(`/deals/${dealId}/eligibility/approve`, { method: "POST", token });
}
