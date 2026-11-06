import { useEffect, useRef, type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { Alert, Box, Button, Center, Spinner, Text } from '@chakra-ui/react';
import axios from 'axios';
import apiClient from '../../../services/api';
import { useAuth } from '../../../context/useAuth';
import { getAuthSessionGeneration } from '../../../utils/authSessionGeneration';
import { adminTokenExpiryMs, shouldInvalidateCurrentAdminSession } from '../../../utils/adminSession';
import { useAdminIdentity } from './useAdminIdentity';

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
  const identity = useAdminIdentity(active);
  const confirmedAdmin = identity.isSuccess && identity.data?.active === true &&
    identity.data?.role === 'admin' && identity.data?.id === currentUser?.email;

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

  useEffect(() => {
    if (identity.isSuccess && !confirmedAdmin && sessionGeneration === getAuthSessionGeneration()) {
      logoutRef.current();
    }
    if (identity.isError && axios.isAxiosError(identity.error) &&
        identity.error.response?.status === 401 &&
        sessionGeneration === getAuthSessionGeneration()) {
      logoutRef.current();
    }
  }, [identity.isSuccess, identity.isError, identity.error, confirmedAdmin, sessionGeneration]);

  if (!active) return <Navigate to="/login" replace />;
  if (identity.isPending) return (
    <Center minH="60vh" role="status" flexDirection="column" gap={3}>
      <Spinner size="lg" /><Text>Verificando acceso administrativo…</Text>
    </Center>
  );
  if (identity.isError) return (
    <Box maxW="480px" mx="auto" p={6}>
      <Alert.Root status="error" role="alert">
        <Alert.Indicator /><Alert.Content>
          <Alert.Title>No pudimos verificar tu sesión.</Alert.Title>
          <Alert.Description>Comprobá la conexión y volvé a intentar.</Alert.Description>
        </Alert.Content>
      </Alert.Root>
      <Button mt={3} onClick={() => void identity.refetch()}>Reintentar</Button>
    </Box>
  );
  if (!confirmedAdmin) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export default AdminSessionGate;
