import { apiFetch } from "@/lib/api/client";

export type DealStatus =
  | "intake_in_progress"
  | "docs_pending"
  | "extraction_in_progress"
  | "ready_for_review"
  | "lo_approved"
  | "closed";

export type DealListItem = {
  id: number;
  borrower_id: number;
  borrower_name: string;
  status: DealStatus;
  updated_at: string | null;
};

export type DealDetail = {
  deal: { id: number; borrower_id: number; status: DealStatus };
  loan_application: { deal_id: number; data: Record<string, unknown> };
  deal_context: {
    deal_id: number;
    extracted_income: Record<string, unknown>;
    extracted_assets: Record<string, unknown>;
    extracted_liabilities: Record<string, unknown>;
    computed_metrics: Record<string, unknown>;
    status_flags: Record<string, unknown>;
    eligibility: Record<string, unknown>;
    conditions: { items?: unknown[] };
  };
};

export async function listDeals(token: string, status?: DealStatus): Promise<DealListItem[]> {
  const qs = status ? `?status=${status}` : "";
  return apiFetch<DealListItem[]>(`/deals${qs}`, { token });
}

export async function getDeal(token: string, dealId: number): Promise<DealDetail> {
  return apiFetch<DealDetail>(`/deals/${dealId}`, { token });
}
