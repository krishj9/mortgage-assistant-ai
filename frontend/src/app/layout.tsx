import type { Metadata } from "next";
import type React from "react";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "Loan Officer Copilot",
  description: "Mortgage loan officer and borrower copilot",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-foreground antialiased">
        <header className="sticky top-0 z-10 border-b border-border bg-surface/80 backdrop-blur">
          <div className="mx-auto flex h-14 w-full max-w-6xl items-center gap-2 px-4 md:px-6">
            <Link href="/" className="flex items-center gap-2 font-semibold text-foreground">
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
                LC
              </span>
              <span>Loan Copilot</span>
            </Link>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
