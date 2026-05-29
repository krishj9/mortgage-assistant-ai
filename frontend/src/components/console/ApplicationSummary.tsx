const REQUIRED_PATHS: { path: string; label: string }[] = [
  { path: "identity.borrower_name", label: "Borrower name" },
  { path: "contact.contact_email", label: "Email" },
  { path: "employment.employment_status", label: "Employment" },
  { path: "income.income_amount", label: "Income" },
  { path: "property.property_value_or_purchase_price", label: "Property value" },
  { path: "loan_purpose.loan_purpose", label: "Loan purpose" },
];

function getAtPath(obj: Record<string, unknown>, path: string): unknown {
  let cur: unknown = obj;
  for (const part of path.split(".")) {
    if (typeof cur !== "object" || cur === null || !(part in cur)) return undefined;
    cur = (cur as Record<string, unknown>)[part];
  }
  return cur;
}

export function ApplicationSummary({ data }: { data: Record<string, unknown> }) {
  const gaps = REQUIRED_PATHS.filter(({ path }) => {
    const v = getAtPath(data, path);
    return v === undefined || v === null || v === "";
  });

  return (
    <section className="rounded-lg border border-border bg-surface p-5 shadow-card">
      <h2 className="text-lg font-semibold text-foreground">Application summary</h2>
      {gaps.length > 0 ? (
        <p className="mt-2 text-sm text-warning">
          Missing fields: {gaps.map((g) => g.label).join(", ")}
        </p>
      ) : (
        <p className="mt-2 text-sm text-success">Required intake fields look complete.</p>
      )}
      <pre className="mt-4 max-h-80 overflow-auto rounded-md bg-muted p-3 text-xs text-foreground">
        {JSON.stringify(data, null, 2)}
      </pre>
    </section>
  );
}
