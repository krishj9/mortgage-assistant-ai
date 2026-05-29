"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ApplicationSummary } from "@/components/console/ApplicationSummary";
import { getDeal, type DealDetail } from "@/lib/api/deals";
import { getStaffToken } from "@/lib/auth";

export default function DealOverviewPage() {
  const params = useParams();
  const dealId = Number(params.dealId);
  const [detail, setDetail] = useState<DealDetail | null>(null);

  useEffect(() => {
    const token = getStaffToken();
    if (!token) return;
    getDeal(token, dealId).then(setDetail);
  }, [dealId]);

  if (!detail) return <p className="text-sm text-muted-foreground">Loading…</p>;

  return (
    <ApplicationSummary data={(detail.loan_application.data ?? {}) as Record<string, unknown>} />
  );
}
