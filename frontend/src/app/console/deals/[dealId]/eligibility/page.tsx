"use client";

import { useParams } from "next/navigation";

import { EligibilityPanel } from "@/components/console/EligibilityPanel";
import { getStaffToken } from "@/lib/auth";

export default function DealEligibilityPage() {
  const params = useParams();
  const dealId = Number(params.dealId);
  const token = getStaffToken();
  if (!token) return null;
  return <EligibilityPanel token={token} dealId={dealId} />;
}
