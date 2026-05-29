import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ExtractionReview } from "@/components/console/ExtractionReview";

vi.mock("@/lib/api/extractions", () => ({
  getExtraction: vi.fn().mockResolvedValue({
    id: 1,
    document_id: 10,
    raw_ocr: {},
    normalized: { income: { records: [{ gross_income: 5000 }] } },
    confidence: { income: 0.6 },
    human_corrections: {},
    status: "succeeded",
  }),
  updateExtraction: vi.fn(),
}));

describe("ExtractionReview", () => {
  it("shows low confidence hint and save button", async () => {
    render(<ExtractionReview token="t" documentId={10} />);
    await waitFor(() => {
      expect(screen.getByText(/Low confidence/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Save corrections/i })).toBeInTheDocument();
    });
  });
});
