import { jwtDecode } from 'jwt-decode';
import type { TokenPayload } from '../types';

/** Pure, testable browser hint. The backend still verifies token signatures. */
export const adminTokenExpiryMs = (accessToken: string): number | null => {
  try {
    const payload = jwtDecode<TokenPayload>(accessToken);
    if (payload.role !== 'admin' || typeof payload.exp !== 'number' ||
        !Number.isFinite(payload.exp) || payload.exp <= 0) {
      return null;
    }
    return payload.exp * 1000;
  } catch {
    return null;
  }
};

/** Only the live interceptor generation may sign out its own token. */
export const shouldInvalidateCurrentAdminSession = (
  sessionActive: boolean,
  sentAuthorization: unknown,
  expectedToken: string,
  currentStoredToken: string | null,
): boolean => (
  sessionActive &&
  currentStoredToken === expectedToken &&
  sentAuthorization === `Bearer ${expectedToken}`
);
