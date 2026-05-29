import { apiFetch } from "@/lib/api/client";

export async function staffLogin(email: string, password: string): Promise<string> {
  const data = await apiFetch<{ access_token: string }>("/auth/staff/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return data.access_token;
}
