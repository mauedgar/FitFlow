import { jwtDecode } from "jwt-decode";
import type { TokenPayload } from "../types";

/**
 * UI-only precheck: NOT a signature verifier or an authorization boundary.
 * FastAPI must independently validate every protected request.
 */
const knownRoles = new Set(["admin", "teacher", "trainer", "client", "front_desk"]);

export function inspectLocalAccessClaims(token: string): TokenPayload {
  const payload = jwtDecode<Partial<TokenPayload>>(token);
  if (
    typeof payload.sub !== "string" ||
    payload.sub.length === 0 ||
    typeof payload.role !== "string" ||
    !knownRoles.has(payload.role) ||
    typeof payload.exp !== "number" ||
    !Number.isFinite(payload.exp) ||
    payload.exp <= Math.floor(Date.now() / 1000) ||
    (payload.token_use !== undefined && payload.token_use !== "access")
  ) {
    throw new Error("Token de acceso inválido o expirado");
  }
  return payload as TokenPayload;
}
