import type { DealStatus } from "@/lib/api/deals";
import { Badge } from "@/components/ui/Badge";

type Tone = "neutral" | "primary" | "success" | "warning" | "danger";

const TONES: Record<DealStatus, Tone> = {
  intake_in_progress: "primary",
  docs_pending: "warning",
  extraction_in_progress: "primary",
  ready_for_review: "primary",
  lo_approved: "success",
  closed: "neutral",
};

export function StatusChip({ status }: { status: DealStatus }) {
  const tone = TONES[status] ?? "neutral";
  const label = status.replace(/_/g, " ");
  return (
    <Badge tone={tone} className="capitalize">
      {label}
    </Badge>
  );
}
