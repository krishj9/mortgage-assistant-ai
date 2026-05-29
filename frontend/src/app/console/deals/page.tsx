"use client";

import { useEffect, useState } from "react";

import { DealList } from "@/components/console/DealList";
import { listDeals, type DealListItem, type DealStatus } from "@/lib/api/deals";
import { getStaffToken } from "@/lib/auth";

export default function ConsoleDealsPage() {
  const [deals, setDeals] = useState<DealListItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<DealStatus | "">("");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getStaffToken();
    if (!token) return;
    listDeals(token, statusFilter || undefined)
      .then(setDeals)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load deals"));
  }, [statusFilter]);

  return (
    <main>
      <h1 className="mb-4 text-2xl font-semibold text-foreground">Deals</h1>
      {error ? <p className="mb-3 text-sm text-danger">{error}</p> : null}
      <DealList deals={deals} statusFilter={statusFilter} onStatusFilterChange={setStatusFilter} />
    </main>
  );
}
