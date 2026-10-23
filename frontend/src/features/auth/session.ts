import { getCurrentUser, type UserResponse } from "../../api";

export type Session =
  | { status: "loading" }
  | { status: "anonymous" }
  | { status: "authenticated"; user: UserResponse };

export function loadSession(): Promise<Session> {
  return getCurrentUser().then(
    (user): Session => ({ status: "authenticated", user }),
    (): Session => ({ status: "anonymous" }),
  );
}
