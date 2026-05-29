import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { MessageApprovalPanel } from "@/components/console/MessageApprovalPanel";

vi.mock("@/lib/api/messages", () => ({
  getDealMessages: vi.fn().mockResolvedValue({
    deal_id: 1,
    internal_draft: "",
    borrower_draft: "",
    internal_approved: false,
    borrower_approved: false,
    approved_by_user_id: null,
    approved_at: null,
  }),
  updateDealMessages: vi.fn(),
  approveDealMessages: vi.fn(),
}));

describe("MessageApprovalPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("disables approve buttons when drafts are empty", async () => {
    render(<MessageApprovalPanel token="test-token" dealId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Approve internal")).toBeDisabled();
      expect(screen.getByText("Approve for borrower")).toBeDisabled();
    });
  });
});
