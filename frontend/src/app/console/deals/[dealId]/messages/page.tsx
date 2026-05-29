"use client";

import { useParams } from "next/navigation";

import { MessageApprovalPanel } from "@/components/console/MessageApprovalPanel";
import { getStaffToken } from "@/lib/auth";

export default function DealMessagesPage() {
  const params = useParams();
  const dealId = Number(params.dealId);
  const token = getStaffToken();
  if (!token) return null;
  return <MessageApprovalPanel token={token} dealId={dealId} />;
}
