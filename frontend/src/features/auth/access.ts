import type { Session } from "./session";

export type Role = "user" | "admin" | "superadmin";

export type Access =
  | { kind: "public" }
  | { kind: "authenticated" }
  | { kind: "roles"; roles: readonly Role[] };

export type AccessDecision = "allow" | "pending" | "login" | "forbidden";

const AUTH_PATHS: readonly string[] = ["/login", "/register"];
const PARSE_ORIGIN = "http://app.invalid";

export function resolveAccess(access: Access, session: Session): AccessDecision {
  if (access.kind === "public") return "allow";

  switch (session.status) {
    case "loading":
      return "pending";
    case "anonymous":
      return "login";
    case "authenticated":
      if (access.kind === "authenticated") return "allow";
      return access.roles.some((role) => role === session.user.role) ? "allow" : "forbidden";
  }
}

export function canAccess(access: Access, session: Session): boolean {
  return resolveAccess(access, session) === "allow";
}

export function safeNextPath(raw: string | null): string | null {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//") || raw.startsWith("/\\")) {
    return null;
  }

  // The URL parser drops tabs and newlines and reads "\" as "/", so "/\t/evil.com"
  // passes the prefix checks but resolves to another host. Comparing origins catches it.
  const url = new URL(raw, PARSE_ORIGIN);
  if (url.origin !== PARSE_ORIGIN || AUTH_PATHS.includes(url.pathname)) {
    return null;
  }

  return url.pathname + url.search + url.hash;
}

export function buildLoginPath(path: string): string {
  return `/login?next=${encodeURIComponent(path)}`;
}
