"use client";

import type { Condition } from "@/lib/api/eligibility";

export function ConditionsEditor({
  conditions,
  onChange,
}: {
  conditions: Condition[];
  onChange: (items: Condition[]) => void;
}) {
  function updateItem(index: number, field: keyof Condition, value: string) {
    const next = conditions.map((c, i) => (i === index ? { ...c, [field]: value } : c));
    onChange(next);
  }

  return (
    <div className="flex flex-col gap-3">
      {conditions.length === 0 ? (
        <p className="text-sm text-muted-foreground">No conditions.</p>
      ) : (
        conditions.map((c, i) => (
          <div key={c.id || i} className="rounded-md border border-border p-3">
            <input
              value={c.title}
              onChange={(e) => updateItem(i, "title", e.target.value)}
              placeholder="Title"
              className="mb-2 h-9 w-full rounded-md border border-input bg-surface px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <textarea
              value={c.rationale}
              onChange={(e) => updateItem(i, "rationale", e.target.value)}
              placeholder="Rationale"
              rows={2}
              className="w-full rounded-md border border-input bg-surface px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <div className="mt-1 text-xs text-muted-foreground">Code: {c.code}</div>
          </div>
        ))
      )}
    </div>
  );
}
