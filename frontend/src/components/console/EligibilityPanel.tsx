"use client";

import { useState } from "react";

import { ConditionsEditor } from "@/components/console/ConditionsEditor";
import type { Condition, EligibilityPayload, EligibilityStatus } from "@/lib/api/eligibility";
import {
  approveEligibility,
  getEligibility,
  patchEligibility,
  runEligibility,
} from "@/lib/api/eligibility";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";

export function EligibilityPanel({ token, dealId }: { token: string; dealId: number }) {
  const [eligibility, setEligibility] = useState<EligibilityPayload | null>(null);
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [statusOverride, setStatusOverride] = useState<EligibilityStatus | "">("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const data = await getEligibility(token, dealId);
      setEligibility(data.eligibility);
      setConditions(data.conditions.items ?? []);
      setStatusOverride(data.eligibility.status);
    } catch {
      setEligibility(null);
      setConditions([]);
    }
  }

  async function onRun() {
    setBusy(true);
    setMessage("");
    try {
      const data = await runEligibility(token, dealId);
      setEligibility(data.eligibility);
      setConditions(data.conditions.items ?? []);
      setStatusOverride(data.eligibility.status);
      setMessage("Eligibility run complete. Deal is ready for review.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Run failed");
    } finally {
      setBusy(false);
    }
  }

  async function onSaveOverride() {
    if (!statusOverride) return;
    setBusy(true);
    try {
      await patchEligibility(token, dealId, {
        status: statusOverride,
        conditions: { items: conditions },
      });
      await load();
      setMessage("Overrides saved.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function onApprove() {
    setBusy(true);
    try {
      await approveEligibility(token, dealId);
      await load();
      setMessage("Eligibility approved.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Approve failed");
    } finally {
      setBusy(false);
    }
  }

  const pct = (n?: number | null) => (n != null ? `${(n * 100).toFixed(1)}%` : "—");

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        <Button type="button" variant="secondary" size="sm" onClick={onRun} disabled={busy}>
          Run eligibility
        </Button>
        <Button type="button" variant="secondary" size="sm" onClick={load} disabled={busy}>
          Refresh
        </Button>
        <Button type="button" size="sm" onClick={onApprove} disabled={busy || !eligibility}>
          Approve eligibility
        </Button>
      </div>

      {eligibility ? (
        <div className="mb-4 grid grid-cols-3 gap-3">
          <Card>
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground">Status</div>
              <div className="font-bold uppercase text-foreground">{eligibility.status}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground">DTI</div>
              <div className="font-bold text-foreground">{pct(eligibility.dti)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground">LTV</div>
              <div className="font-bold text-foreground">{pct(eligibility.ltv)}</div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          No eligibility results yet. Run eligibility to compute DTI/LTV.
        </p>
      )}

      <label className="mb-4 flex items-center gap-2 text-sm text-foreground">
        Override status
        <select
          value={statusOverride}
          onChange={(e) => setStatusOverride(e.target.value as EligibilityStatus)}
          className="h-9 rounded-md border border-input bg-surface px-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="">—</option>
          <option value="green">Green</option>
          <option value="yellow">Yellow</option>
          <option value="red">Red</option>
        </select>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={onSaveOverride}
          disabled={busy || !statusOverride}
        >
          Save override
        </Button>
      </label>

      <h3 className="mb-2 text-base font-semibold text-foreground">Conditions</h3>
      <ConditionsEditor conditions={conditions} onChange={setConditions} />

      {message ? <p className="mt-4 text-sm text-muted-foreground">{message}</p> : null}
    </div>
  );
}
