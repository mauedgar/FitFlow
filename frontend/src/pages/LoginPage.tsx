import { toaster } from '../components/ui/toaster-store';
import React, { useEffect, useState } from 'react';
import { Box, Button, Heading, Input, VStack, Text, Link, Container, Field } from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query'; // ⭐ Importamos useMutation
import { useAuth } from '../context/useAuth'; // ⭐ Importamos el contexto de Auth
import classService from '../services/classService'; // ⭐ Usaremos classService para el login
import { type TokenResponse } from '../types';
import { verifiedRoleDestination } from '../utils/verifiedRoleDestination';
import { AxiosError } from 'axios'; // ⭐ Para un manejo de errores más específico

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const { login, token, currentUser, isAuthenticated, isLoadingAuth } = useAuth();
  const navigate = useNavigate();
  const [awaitingVerifiedIdentity, setAwaitingVerifiedIdentity] = useState(false);

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
    // If /auth/me failed, AuthProvider clears the pending token; fail closed.
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
  }, [awaitingVerifiedIdentity, isLoadingAuth, isAuthenticated, currentUser, token, navigate]);

  // ⭐ 1. Definimos la mutación de login
  const loginMutation = useMutation<TokenResponse, AxiosError, { username: string; password: string }>({
    // La función que ejecuta la llamada a la API
    mutationFn: (credentials) => classService.login(credentials),

    // Callback que se ejecuta si la mutación es exitosa
    onSuccess: (data) => {
      // Identity verification occurs in AuthProvider before any navigation.
      login(data.access_token, data.refresh_token);
      setAwaitingVerifiedIdentity(true);
    },

    // Callback que se ejecuta si la mutación falla
    onError: (error) => {
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
    // A new login supersedes any identity verification still pending.
    // ⭐ 3. Disparamos la mutación con las credenciales
    loginMutation.mutate({ username: email, password });
  };

  return (
    <Container maxW="40rem" py={10}>
      <VStack gap={8}>
        <Heading>Iniciar Sesión</Heading>

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
                  disabled={loginMutation.isPending}
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
                  disabled={loginMutation.isPending}
                />
              </Field.Root>

              <Button
                type="submit"
                colorPalette="teal"
                w="100%"
                loading={loginMutation.isPending}
                disabled={loginMutation.isPending}
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
