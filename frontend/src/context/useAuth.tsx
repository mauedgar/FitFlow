import { useContext } from 'react';
import { AuthContext } from './AuthContext';
import { advanceAuthSessionGeneration, getAuthSessionGeneration } from '../utils/authSessionGeneration';

/** The single app auth entrypoint: bump the generation synchronously. */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) throw new Error('useAuth must be used within an AuthProvider');
  const login = (accessToken: string, refreshToken: string) => {
    advanceAuthSessionGeneration();
    context.login(accessToken, refreshToken);
  };
  const logout = (): Promise<void> => {
    advanceAuthSessionGeneration();
    return context.logout();
  };
  return { ...context, login, logout, sessionGeneration: getAuthSessionGeneration() };
}
