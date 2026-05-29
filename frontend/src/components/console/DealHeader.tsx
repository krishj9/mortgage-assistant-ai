import { StatusChip } from "@/components/console/StatusChip";
import type { DealStatus } from "@/lib/api/deals";

export function DealHeader({
  dealId,
  borrowerName,
  status,
}: {
  dealId: number;
  borrowerName?: string;
  status: DealStatus;
}) {
  return (
    <header className="mb-5">
      <h1 className="text-2xl font-semibold text-foreground">Deal #{dealId}</h1>
      <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
        {borrowerName ? <span>{borrowerName}</span> : null}
        <StatusChip status={status} />
      </div>
    </header>
  );
}
