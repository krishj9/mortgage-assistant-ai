import type { ChatTurn } from "@/lib/api/borrowerChat";
import { cn } from "@/lib/cn";

export function ChatMessage({ turn }: { turn: ChatTurn }) {
  const isBorrower = turn.role === "borrower";
  const isSystem = turn.role === "system";

  const label = isBorrower ? "You" : isSystem ? "Loan officer update" : "Assistant";
  const avatar = isBorrower ? "You" : isSystem ? "LO" : "AI";

  return (
    <div
      className={cn(
        "flex animate-fade-in items-end gap-2",
        isBorrower ? "flex-row-reverse" : "flex-row"
      )}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
          isBorrower
            ? "bg-primary text-primary-foreground"
            : isSystem
              ? "bg-success/15 text-success"
              : "bg-muted text-muted-foreground"
        )}
      >
        {avatar}
      </div>
      <div className={cn("max-w-[78%]", isBorrower ? "text-right" : "text-left")}>
        <div className="mb-1 text-xs text-muted-foreground">{label}</div>
        <div
          className={cn(
            "inline-block whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm",
            isBorrower
              ? "rounded-br-sm bg-primary text-primary-foreground"
              : isSystem
                ? "rounded-bl-sm border border-success/30 bg-success/10 text-foreground"
                : "rounded-bl-sm bg-muted text-foreground"
          )}
        >
          {turn.content}
        </div>
      </div>
    </div>
  );
}
