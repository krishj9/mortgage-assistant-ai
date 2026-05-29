"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { ConsoleNav } from "@/components/console/ConsoleNav";
import { DealHeader } from "@/components/console/DealHeader";
import { getDeal, type DealDetail } from "@/lib/api/deals";
import { getStaffToken } from "@/lib/auth";

export default function DealDetailLayout({ children }: { children: ReactNode }) {
  const params = useParams();
  const dealId = String(params.dealId);
  const [detail, setDetail] = useState<DealDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getStaffToken();
    if (!token) return;
    getDeal(token, Number(dealId))
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load deal"));
  }, [dealId]);

  const appData = (detail?.loan_application.data ?? {}) as Record<string, unknown>;
  const borrowerName =
    (appData.identity as Record<string, unknown> | undefined)?.borrower_name?.toString() ??
    `Borrower #${detail?.deal.borrower_id ?? ""}`;

  return (
    <div>
      <p className="mb-2">
        <Link href="/console/deals" className="text-sm text-primary hover:underline">
          &larr; All deals
        </Link>
      </p>
      {error ? <p className="text-sm text-danger">{error}</p> : null}
      {detail ? (
        <>
          <DealHeader dealId={detail.deal.id} borrowerName={borrowerName} status={detail.deal.status} />
          <ConsoleNav dealId={dealId} />
        </>
      ) : null}
      {children}
    </div>
  );
}
