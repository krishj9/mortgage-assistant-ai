import { apiFetch } from "@/lib/api/client";

export type BorrowerApplication = {
  deal_id: number;
  application: Record<string, unknown>;
  approved_borrower_message: string | null;
};

export async function getBorrowerApplication(token: string): Promise<BorrowerApplication> {
  return apiFetch<BorrowerApplication>("/borrower/application", { token });
}
