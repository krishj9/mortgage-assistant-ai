import type { CapturedField } from "@/lib/api/borrowerChat";
import { Card, CardContent } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { cn } from "@/lib/cn";

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "number") return value.toLocaleString();
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string") return value.replace(/_/g, " ");
  return String(value);
}

export function StatusPanel({
  capturedFields,
  missingFields,
  currentField,
  completed,
  total,
}: {
  capturedFields: CapturedField[];
  missingFields: string[];
  currentField: string | null;
  completed: number;
  total: number;
}) {
  const complete = total > 0 && completed >= total;

  return (
    <Card className="h-fit">
      <CardContent className="space-y-5">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">Application progress</h3>
            <span className="text-xs font-medium text-muted-foreground">
              {completed}/{total}
            </span>
          </div>
          <ProgressBar value={completed} max={total} />
          <p className="text-xs text-muted-foreground">
            {complete
              ? "All required details are complete."
              : currentField
                ? `Up next: ${currentField}`
                : "Let's get started."}
          </p>
        </div>

        {capturedFields.length > 0 ? (
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Captured
            </h4>
            <ul className="space-y-1.5">
              {capturedFields.map((field) => (
                <li key={field.path} className="flex items-start gap-2 text-sm">
                  <span aria-hidden="true" className="mt-0.5 text-success">
                    &#10003;
                  </span>
                  <span className="flex-1">
                    <span className="text-muted-foreground">{field.label}: </span>
                    <span className="font-medium text-foreground">
                      {formatValue(field.value)}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {missingFields.length > 0 ? (
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Still needed
            </h4>
            <ul className="space-y-1.5">
              {missingFields.map((field) => (
                <li
                  key={field}
                  className={cn(
                    "flex items-center gap-2 text-sm",
                    field === currentField ? "font-medium text-foreground" : "text-muted-foreground"
                  )}
                >
                  <span
                    aria-hidden="true"
                    className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      field === currentField ? "bg-primary" : "bg-border"
                    )}
                  />
                  {field}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
