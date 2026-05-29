"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { staffLogin } from "@/lib/api/staffAuth";
import { setStaffToken } from "@/lib/auth";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

export default function ConsoleLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("lo@example.com");
  const [password, setPassword] = useState("password");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const token = await staffLogin(email, password);
      setStaffToken(token);
      router.push("/console/deals");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md">
        <CardContent className="space-y-6">
          <div className="space-y-1 text-center">
            <h1 className="text-2xl font-semibold text-foreground">Staff sign in</h1>
            <p className="text-sm text-muted-foreground">Loan officer / processor console</p>
          </div>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <Button type="submit" className="w-full" loading={loading}>
              Sign in
            </Button>
          </form>
          {error ? (
            <p className="rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>
          ) : null}
        </CardContent>
      </Card>
    </main>
  );
}
