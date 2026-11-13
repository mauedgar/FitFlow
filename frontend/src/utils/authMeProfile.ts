import type { TokenPayload, User, UserRole } from "../types";

/** The only source for profile email and current role is the backend /auth/me.
 * The JWT was decoded locally for UX only; FastAPI validates its signature. */
const backendRoles = new Set(["admin", "teacher", "client", "front_desk"]);

export function projectServerAuthUser(claims: TokenPayload, response: unknown): User {
  if (!response || typeof response !== "object") {
    throw new Error("Invalid authenticated profile");
  }
  const profile = response as Record<string, unknown>;
  if (
    typeof claims.sub !== "string" ||
    typeof profile.id !== "string" ||
    profile.id !== claims.sub ||
    typeof profile.email !== "string" ||
    !profile.email.includes("@") ||
    typeof profile.role !== "string" ||
    !backendRoles.has(profile.role) ||
    profile.active !== true
  ) {
    throw new Error("Mismatched or inactive authenticated profile");
  }
  return {
    id: profile.id,
    email: profile.email,
    role: profile.role as UserRole,
    active: true,
  };
}
