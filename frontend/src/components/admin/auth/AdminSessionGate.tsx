import { useEffect, type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import axios from 'axios';
import apiClient from '../../../services/api';
import { useAuth } from '../../../context/useAuth';
import { adminTokenExpiryMs } from '../../../utils/adminSession';

/**
 * This is a browser UX boundary, not a replacement for backend JWT signature
 * verification or server-side RBAC. API 401 is authoritative.
 */
const AdminSessionGate = ({ children }: { children: ReactNode }) => {
  const { token, logout } = useAuth();
  const expiresAt = token ? adminTokenExpiryMs(token) : null;
  const active = expiresAt !== null && expiresAt > Date.now();

  useEffect(() => {
    if (!token) return;
    if (expiresAt === null) {
      logout();
      return;
    }
    let timeoutId: number | undefined;
    const recheck = () => {
      const remaining = expiresAt - Date.now();
      if (remaining <= 0) {
        logout();
      } else {
        // Long-lived tokens must not be logged out prematurely due to timer clamp.
        timeoutId = window.setTimeout(recheck, Math.min(remaining, 2_147_483_647));
      }
    };
    recheck();
    return () => {
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };
  }, [token, expiresAt, logout]);

  useEffect(() => {
    if (!token) return;
    const interceptorId = apiClient.interceptors.response.use(
      (response) => response,
      (error: unknown) => {
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          // Never let a stale 401 from an old account sign out a newly logged-in one.
          const sent = error.config?.headers?.get?.('Authorization');
          if (sent === `Bearer ${token}` && localStorage.getItem('access_token') === token) {
            logout();
          }
        }
        return Promise.reject(error);
      },
    );
    return () => apiClient.interceptors.response.eject(interceptorId);
  }, [token, logout]);

  if (!active) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export default AdminSessionGate;
