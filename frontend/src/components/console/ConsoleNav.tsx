"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/cn";

export function ConsoleNav({ dealId }: { dealId: string }) {
  const pathname = usePathname();
  const base = `/console/deals/${dealId}`;
  const tabs = [
    { href: base, label: "Overview", exact: true },
    { href: `${base}/documents`, label: "Documents" },
    { href: `${base}/eligibility`, label: "Eligibility" },
    { href: `${base}/messages`, label: "Messages" },
  ];

  return (
    <nav className="mb-6 flex flex-wrap gap-2">
      {tabs.map((tab) => {
        const active = tab.exact ? pathname === tab.href : pathname.startsWith(tab.href);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={cn(
              "rounded-md px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-foreground hover:bg-muted/70"
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
