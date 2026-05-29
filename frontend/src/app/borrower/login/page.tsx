"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";

import { API_BASE_URL } from "@/lib/api/client";
import { setBorrowerToken } from "@/lib/auth";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

export default function BorrowerLoginPage() {
  const router = useRouter();
  const [dealId, setDealId] = useState<number>(1);
  const [borrowerEmail, setBorrowerEmail] = useState<string>("alice@example.com");
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/auth/borrower/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ deal_id: dealId, borrower_email: borrowerEmail }),
      });

      const text = await res.text();
      let payload: unknown = null;
      try {
        payload = text ? JSON.parse(text) : null;
      } catch {
        payload = text;
      }

      if (!res.ok) {
        const detail =
          typeof payload === "object" &&
          payload !== null &&
          "detail" in payload &&
          typeof (payload as { detail?: unknown }).detail === "string"
            ? (payload as { detail: string }).detail
            : null;
        setError(detail ?? `Error (${res.status})`);
        return;
      }

      const token =
        typeof payload === "object" &&
        payload !== null &&
        "access_token" in payload &&
        typeof (payload as { access_token?: unknown }).access_token === "string"
          ? (payload as { access_token: string }).access_token
          : null;

      if (!token) {
        setError("Invalid response from backend.");
        return;
      }

      setBorrowerToken(token);
      router.push("/borrower/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md">
        <CardContent className="space-y-6">
          <div className="space-y-1 text-center">
            <h1 className="text-2xl font-semibold text-foreground">Welcome back</h1>
            <p className="text-sm text-muted-foreground">
              Start or continue your mortgage application.
            </p>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="dealId">Deal ID</Label>
              <Input
                id="dealId"
                type="number"
                value={dealId}
                onChange={(e) => setDealId(Number(e.target.value))}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={borrowerEmail}
                onChange={(e) => setBorrowerEmail(e.target.value)}
              />
            </div>
            <Button type="submit" className="w-full" loading={loading}>
              Continue
            </Button>
          </form>

          {error ? (
            <p className="rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>
          ) : null}
          <p className="text-center text-xs text-muted-foreground">
            Synthetic borrower session for the Phase-1 demo.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
