import { useEffect, useRef, type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import axios from 'axios';
import apiClient from '../../../services/api';
import { useAuth } from '../../../context/useAuth';
import { getAuthSessionGeneration } from '../../../utils/authSessionGeneration';
import { adminTokenExpiryMs, shouldInvalidateCurrentAdminSession } from '../../../utils/adminSession';

/**
 * Browser-only UX guard. Real signature verification and role authorization
 * remain exclusively backend responsibilities.
 */
const AdminSessionGate = ({ children }: { children: ReactNode }) => {
  const { token, currentUser, logout, sessionGeneration } = useAuth();

  // AuthProvider currently recreates logout; keep effects stable by token/user
  // identity and call the latest action without rebinding each response handler.
  const logoutRef = useRef(logout);
  useEffect(() => {
    logoutRef.current = logout;
  }, [logout]);

  const expiresAt = token ? adminTokenExpiryMs(token) : null;
  const active = currentUser?.role === 'admin' && expiresAt !== null && expiresAt > Date.now();

  useEffect(() => {
    if (!token || !currentUser) return;
    const expectedGeneration = sessionGeneration;
    let sessionActive = true;
    if (expiresAt === null) {
      logoutRef.current();
      return;
    }
    let timeoutId: number | undefined;
    const recheck = () => {
      if (!sessionActive || expectedGeneration !== getAuthSessionGeneration()) return;
      const remaining = expiresAt - Date.now();
      if (remaining <= 0) {
        logoutRef.current();
      } else {
        timeoutId = window.setTimeout(recheck, Math.min(remaining, 2_147_483_647));
      }
    };
    recheck();
    return () => {
      sessionActive = false;
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };
  }, [token, currentUser, expiresAt, sessionGeneration]);

  useEffect(() => {
    if (!token || !currentUser) return;
    const expectedGeneration = sessionGeneration;
    let sessionActive = true;
    const interceptorId = apiClient.interceptors.response.use(
      (response) => response,
      (error: unknown) => {
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          const sent = error.config?.headers?.get?.('Authorization');
          if (shouldInvalidateCurrentAdminSession(
            sessionActive, expectedGeneration, getAuthSessionGeneration(),
            sent, token, localStorage.getItem('access_token')
          )) {
            logoutRef.current();
          }
        }
        return Promise.reject(error);
      },
    );
    return () => {
      // A pending Axios request may retain the former callback after eject.
      // Always retire its generation BEFORE it can handle a delayed 401.
      sessionActive = false;
      apiClient.interceptors.response.eject(interceptorId);
    };
  }, [token, currentUser, sessionGeneration]);

  if (!active) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export default AdminSessionGate;
