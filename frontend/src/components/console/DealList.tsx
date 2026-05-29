"use client";

import Link from "next/link";

import { StatusChip } from "@/components/console/StatusChip";
import type { DealListItem, DealStatus } from "@/lib/api/deals";
import { Card } from "@/components/ui/Card";

export function DealList({
  deals,
  statusFilter,
  onStatusFilterChange,
}: {
  deals: DealListItem[];
  statusFilter: DealStatus | "";
  onStatusFilterChange: (s: DealStatus | "") => void;
}) {
  return (
    <div>
      <div className="mb-4 flex items-center gap-2">
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          Filter by status
          <select
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value as DealStatus | "")}
            className="h-9 rounded-md border border-input bg-surface px-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">All</option>
            <option value="intake_in_progress">Intake in progress</option>
            <option value="docs_pending">Docs pending</option>
            <option value="ready_for_review">Ready for review</option>
            <option value="lo_approved">LO approved</option>
            <option value="closed">Closed</option>
          </select>
        </label>
      </div>
      <Card className="overflow-hidden">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <th className="px-4 py-3 font-medium">Deal</th>
              <th className="px-4 py-3 font-medium">Borrower</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Last updated</th>
            </tr>
          </thead>
          <tbody>
            {deals.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-muted-foreground">
                  No deals found.
                </td>
              </tr>
            ) : (
              deals.map((d) => (
                <tr key={d.id} className="border-b border-border last:border-0 hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <Link href={`/console/deals/${d.id}`} className="font-medium text-primary hover:underline">
                      #{d.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-foreground">{d.borrower_name}</td>
                  <td className="px-4 py-3">
                    <StatusChip status={d.status} />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {d.updated_at ? new Date(d.updated_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
