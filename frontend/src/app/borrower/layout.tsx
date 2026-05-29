"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { clearBorrowerToken, getBorrowerToken } from "@/lib/auth";
import { Button } from "@/components/ui/Button";

export default function BorrowerLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLogin = pathname === "/borrower/login";
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (isLogin) {
      setChecked(true);
      return;
    }
    if (!getBorrowerToken()) {
      router.replace("/borrower/login");
      return;
    }
    setChecked(true);
  }, [isLogin, pathname, router]);

  function onLogout() {
    clearBorrowerToken();
    router.push("/borrower/login");
  }

  if (isLogin) {
    return <>{children}</>;
  }

  if (!checked) {
    return null;
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 md:px-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Mortgage application</h1>
          <p className="text-sm text-muted-foreground">
            Answer a few questions and upload your documents.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/borrower/chat">
            <Button variant="ghost" size="sm">
              Chat
            </Button>
          </Link>
          <Button variant="secondary" size="sm" onClick={onLogout}>
            Log out
          </Button>
        </div>
      </div>
      {children}
    </div>
  );
}
