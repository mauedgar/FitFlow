import { toaster } from '../components/ui/toaster-store';
import React, { useEffect, useRef, useState } from 'react';
import { Box, Button, Heading, Input, VStack, Text, Link, Container, Field } from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query'; // ⭐ Importamos useMutation
import { useAuth } from '../context/useAuth'; // ⭐ Importamos el contexto de Auth
import classService from '../services/classService'; // ⭐ Usaremos classService para el login
import { type TokenResponse } from '../types';
import { verifiedRoleDestination } from '../utils/verifiedRoleDestination';
import { getAuthSessionGeneration } from '../utils/authSessionGeneration';
import { AxiosError } from 'axios'; // ⭐ Para un manejo de errores más específico

type LoginAttempt = {
  username: string;
  password: string;
  attemptId: number;
  generation: number;
};

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const { login, logout, token, currentUser, isAuthenticated, isLoadingAuth,
    identityRecoveryPending, retryIdentity, remoteLogoutUnconfirmed,
    dismissRemoteLogoutWarning } = useAuth();
  const navigate = useNavigate();
  const [awaitingVerifiedIdentity, setAwaitingVerifiedIdentity] = useState(false);
  const [retrySession, setRetrySession] = useState<{
    token: string; generation: number; inFlight: boolean;
  } | null>(null);
  const latestLoginAttempt = useRef(0);
  const latestIdentityRetry = useRef(0);
  const mounted = useRef(false);
  const currentToken = useRef(token);
  currentToken.current = token;
  const retryForSameSession = !!token && retrySession?.token === token &&
    retrySession.generation === getAuthSessionGeneration();
  const retryInFlight = retryForSameSession && retrySession.inFlight;
  const pendingSession = identityRecoveryPending || retryForSameSession;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      latestLoginAttempt.current += 1;
      latestIdentityRetry.current += 1;
    };
  }, []);

  // The provider fetches the signed/validated /auth/me profile. Never redirect
  // from a locally decoded JWT role before backend identity is confirmed.
  useEffect(() => {
    if (!awaitingVerifiedIdentity || isLoadingAuth) return;
    if (isAuthenticated && currentUser) {
      setAwaitingVerifiedIdentity(false);
      toaster.create({
        title: "Inicio de sesión exitoso",
        type: "success",
        duration: 3000,
        closable: true,
      });
      navigate(verifiedRoleDestination(currentUser.role), { replace: true });
      return;
    }
    if (identityRecoveryPending) {
      setAwaitingVerifiedIdentity(false);
      toaster.create({
        title: "No se pudo verificar la sesión",
        description: "Podés reintentar o cerrar la sesión pendiente.",
        type: "warning",
        duration: 5000,
        closable: true,
      });
      return;
    }
    // An invalid identity definitively removes local credentials.
    if (!token) {
      setAwaitingVerifiedIdentity(false);
      toaster.create({
        title: "No se pudo verificar la sesión",
        description: "Iniciá sesión nuevamente.",
        type: "error",
        duration: 5000,
        closable: true,
      });
    }
  }, [awaitingVerifiedIdentity, isLoadingAuth, isAuthenticated, currentUser, token,
    identityRecoveryPending, navigate]);

  // ⭐ 1. Definimos la mutación de login
  const loginMutation = useMutation<TokenResponse, AxiosError, LoginAttempt>({
    mutationFn: ({ username, password }) => classService.login({ username, password }),
    onSuccess: (data, variables) => {
      if (variables.attemptId !== latestLoginAttempt.current ||
          variables.generation !== getAuthSessionGeneration()) return;
      login(data.access_token, data.refresh_token);
      setAwaitingVerifiedIdentity(true);
    },
    onError: (error, variables) => {
      if (variables.attemptId !== latestLoginAttempt.current ||
          variables.generation !== getAuthSessionGeneration()) return;
      // El objeto AxiosError puede contener credenciales en config.data.
      // No se registra ni se muestra información arbitraria del servidor.
      const errorMessage = error.response?.status === 401
        ? "Email o contraseña incorrectos."
        : error.message === "Network Error"
          ? "Error de red. Asegúrate de que el servidor está corriendo."
          : "Ocurrió un error inesperado al iniciar sesión.";

      toaster.create({
        title: "Error al iniciar sesión",
        description: errorMessage,
        type: "error",
        duration: 5000,
        closable: true,
      });
    },
  });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // Never overwrite a recoverable session before it can be revoked.
    if (pendingSession) return;
    // A new login supersedes any identity verification still pending.
    // ⭐ 3. Disparamos la mutación con las credenciales
    loginMutation.mutate({
      username: email, password,
      attemptId: ++latestLoginAttempt.current,
      generation: getAuthSessionGeneration(),
    });
  };

  const handleRetryIdentity = () => {
    if (!token || !pendingSession || retryInFlight) return;
    const retryId = ++latestIdentityRetry.current;
    const generation = getAuthSessionGeneration();
    const retryToken = token;
    setRetrySession({ token: retryToken, generation, inFlight: true });
    const stillCurrent = () => mounted.current && retryId === latestIdentityRetry.current &&
      generation === getAuthSessionGeneration() && retryToken === currentToken.current;
    void (async () => {
      try {
        await retryIdentity();
        // TanStack refetch can resolve with an error result; the effect below
        // still requires a verified /auth/me identity before navigation.
        if (stillCurrent()) {
          setRetrySession(null);
          setAwaitingVerifiedIdentity(true);
        }
      } catch {
        // Unexpected rejection is not proof of revocation. Keep the existing
        // recoverable credentials and never expose the rejection details.
        if (stillCurrent()) {
          // A rejection may not update TanStack's error state; keep the
          // revocation controls available until retry or explicit logout.
          setRetrySession({ token: retryToken, generation, inFlight: false });
          toaster.create({
            title: "No se pudo verificar la sesión",
            description: "Podés reintentar o cerrar la sesión pendiente.",
            type: "warning",
            duration: 5000,
            closable: true,
          });
        }
      }
    })();
  };
  const handleClosePendingSession = () => {
    latestIdentityRetry.current += 1;
    setRetrySession(null);
    void logout().catch(() => toaster.create({
      title: "Sesión local cerrada",
      description: "No se pudo confirmar su revocación remota.",
      type: "warning",
    }));
  };

  return (
    <Container maxW="40rem" py={10}>
      <VStack gap={8}>
        <Heading>Iniciar Sesión</Heading>
        {remoteLogoutUnconfirmed && (
          <Box role="alert" width="100%">
            <Text>
              Cerraste la sesión local, pero no se confirmó su revocación en el servidor.
              La sesión anterior podría seguir activa hasta que expire.
            </Text>
            <Button variant="outline" onClick={dismissRemoteLogoutWarning}>
              Ocultar aviso (no revoca la sesión)
            </Button>
          </Box>
        )}
        {pendingSession && (
          <Box role="alert" width="100%">
            <Text>La identidad no pudo verificarse. El acceso permanece suspendido.</Text>
            <Button onClick={handleRetryIdentity} disabled={isLoadingAuth || retryInFlight}>
              Reintentar verificación
            </Button>
            <Button colorPalette="red" variant="outline" onClick={handleClosePendingSession}>
              Cerrar sesión pendiente
            </Button>
          </Box>
        )}

        {/* ⭐ El estado de carga lo gestiona directamente la mutación */}
        <Box w="100%" asChild><form onSubmit={handleSubmit}>
            <VStack gap={4}>
              <Field.Root required>
                <Field.Label>Email</Field.Label>
                <Input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="tu@email.com"
                  autoComplete='email'
                  disabled={loginMutation.isPending || pendingSession}
                />
              </Field.Root>

              <Field.Root required>
                <Field.Label>Contraseña</Field.Label>
                <Input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="********"
                  autoComplete="current-password"
                  disabled={loginMutation.isPending || pendingSession}
                />
              </Field.Root>

              <Button
                type="submit"
                colorPalette="teal"
                w="100%"
                loading={loginMutation.isPending}
                disabled={loginMutation.isPending || pendingSession}
              >
                Ingresar
              </Button>
            </VStack>
          </form></Box>

        <Text>
          ¿No tienes cuenta?{' '}
          <Link color="teal.500" asChild><RouterLink to="/register">Regístrate aquí
                      </RouterLink></Link>
        </Text>
      </VStack>
    </Container>
  );
};

export default LoginPage;
