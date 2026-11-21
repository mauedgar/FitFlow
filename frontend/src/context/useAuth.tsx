import { useContext } from 'react';
import { AuthContext } from './AuthContext';
import { getAuthSessionGeneration } from '../utils/authSessionGeneration';

/** The single app auth entrypoint: bump the generation synchronously. */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) throw new Error('useAuth must be used within an AuthProvider');
  // The provider advances the generation ONLY after accepting login, and
  // synchronously before clearing state on logout. Wrapper pre-bumps could
  // invalidate a still-live refresh timer when a login is rejected.
  const login = (accessToken: string, csrfToken: string): boolean =>
    context.login(accessToken, csrfToken);
  const logout = (): void => context.logout();
  return { ...context, login, logout, sessionGeneration: getAuthSessionGeneration() };
}
