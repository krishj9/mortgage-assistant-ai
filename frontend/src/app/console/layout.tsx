"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { clearStaffToken, getStaffToken } from "@/lib/auth";
import { Button } from "@/components/ui/Button";

export default function ConsoleLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLogin = pathname === "/console/login";

  useEffect(() => {
    if (isLogin) return;
    if (!getStaffToken()) {
      router.replace("/console/login");
    }
  }, [isLogin, pathname, router]);

  function onLogout() {
    clearStaffToken();
    router.push("/console/login");
  }

  if (isLogin) {
    return <>{children}</>;
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 md:px-6">
      <header className="mb-6 flex items-center justify-between border-b border-border pb-4">
        <div className="flex items-center gap-4">
          <Link href="/console/deals" className="font-semibold text-foreground">
            LO Console
          </Link>
          <Link href="/console/deals" className="text-sm text-muted-foreground hover:text-foreground">
            Deals
          </Link>
        </div>
        <Button type="button" variant="secondary" size="sm" onClick={onLogout}>
          Log out
        </Button>
      </header>
      {children}
    </div>
  );
}
