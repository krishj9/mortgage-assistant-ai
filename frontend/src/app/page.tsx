import Link from "next/link";

import { PageShell } from "@/components/ui/PageShell";
import { Card, CardContent } from "@/components/ui/Card";

const ENTRIES = [
  {
    href: "/borrower/login",
    title: "Borrower portal",
    description: "Apply through a guided chat, upload documents, and track your progress.",
    cta: "Start your application",
  },
  {
    href: "/console/login",
    title: "LO / Processor console",
    description: "Review applications, extractions, eligibility, and approve borrower messages.",
    cta: "Open the console",
  },
];

export default function HomePage() {
  return (
    <PageShell>
      <section className="mx-auto max-w-3xl py-10 text-center">
        <span className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          Mortgage copilot
        </span>
        <h1 className="mt-4 text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
          Loan Officer &amp; Borrower Copilot
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-lg text-muted-foreground">
          A guided, document-aware intake experience for borrowers and a review console for
          loan officers and processors.
        </p>
      </section>

      <div className="mx-auto grid max-w-4xl gap-5 sm:grid-cols-2">
        {ENTRIES.map((entry) => (
          <Link key={entry.href} href={entry.href} className="group block">
            <Card className="h-full transition-shadow hover:shadow-soft">
              <CardContent className="flex h-full flex-col">
                <h2 className="text-lg font-semibold text-foreground">{entry.title}</h2>
                <p className="mt-2 flex-1 text-sm text-muted-foreground">{entry.description}</p>
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary">
                  {entry.cta}
                  <span aria-hidden="true" className="transition-transform group-hover:translate-x-0.5">
                    &rarr;
                  </span>
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </PageShell>
  );
}
