import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  VStack,
  Text,
  Link,
  useToast,
  Container
} from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query'; // ⭐ Importamos useMutation
import { useAuth } from '../context/useAuth'; // ⭐ Importamos el contexto de Auth
import classService from '../services/classService'; // ⭐ Usaremos classService para el login
import { UserRole, type FastAPIAuthErrorResponse, type TokenResponse } from '../types'; // ⭐ Importamos el tipo de respuesta del token
import { AxiosError } from 'axios'; // ⭐ Para un manejo de errores más específico
import { type TokenPayload } from '../types';
import {jwtDecode} from 'jwt-decode'


const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const { login } = useAuth(); // ⭐ Obtenemos la función login, y el estado del usuario/rol
  const navigate = useNavigate();
  const toast = useToast();

  // ⭐ 1. Definimos la mutación de login
  const loginMutation = useMutation<TokenResponse, AxiosError, { username: string; password: string }>({
    // La función que ejecuta la llamada a la API
    mutationFn: (credentials) => classService.login(credentials),
    
    // Callback que se ejecuta si la mutación es exitosa
    onSuccess: (data) => {
      // Llamamos a la función login del AuthContext, pasando solo el token
      // El AuthContext ya se encarga de decodificar y establecer el rol
      login(data.access_token);      
      toast({
        title: "Inicio de sesión exitoso",
        status: "success",
        duration: 3000,
        isClosable: true,
      });

      // ⭐ 2. Redirección basada en el rol, que ahora se obtiene del AuthContext
      // Esperamos que currentUser y userRole ya estén actualizados después de 'login(data.access_token)'
      // Si necesitas una redirección inmediata basada en el token, podrías decodificar aquí
      // pero el patrón ideal es que AuthContext lo maneje y tú reaccione a ello.
      // Para una redirección más segura, esperemos al siguiente ciclo de render o a que AuthContext actualice.
      // Por simplicidad, usaremos el userRole actualizado por el AuthContext
      // Decodificas YA el role antes de depender del contexto
      const payload = jwtDecode<TokenPayload>(data.access_token)      
      if (payload.role === UserRole.ADMIN) {
        navigate('/admin');
      } else {
        navigate('/home'); // O '/home' según tu estructura
      }
    },
    
    // Callback que se ejecuta si la mutación falla
    onError: (error) => {
      let errorMessage = "Ocurrió un error inesperado al iniciar sesión.";
      if (error.response?.data) {
        // Intentamos castear a un tipo de error de autenticación específico
        const errorData = error.response.data as FastAPIAuthErrorResponse; 

        if (errorData.detail) { // Ahora TypeScript sabe que 'detail' puede existir
          errorMessage = errorData.detail;
        } else {
          // Si el detalle no es un string (ej. un objeto de errores de validación, aunque raro para login)
          // Puedes intentar un casteo más general si tu API devuelve diferentes formatos
          errorMessage = JSON.stringify(error.response.data);
        }
      } else if (error.message === "Network Error") {
        errorMessage = "Error de red. Asegúrate de que el servidor está corriendo.";
      } else if (error.message) {
        errorMessage = error.message;
      }

      toast({
        title: "Error al iniciar sesión",
        description: errorMessage,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      console.error('Error de login:', error);
    },
  });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // ⭐ 3. Disparamos la mutación con las credenciales
    loginMutation.mutate({ username: email, password });    
  };
  
  return (
    <Container maxW="container.sm" py={10}>
      <VStack spacing={8}>
        <Heading>Iniciar Sesión</Heading>
        
        {/* ⭐ El estado de carga lo gestiona directamente la mutación */}
        <Box as="form" onSubmit={handleSubmit} w="100%">
          <VStack spacing={4}>
            <FormControl isRequired>
              <FormLabel>Email</FormLabel>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@email.com"
                autoComplete='email'
                isDisabled={loginMutation.isPending} // Deshabilitar mientras carga
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Contraseña</FormLabel>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="********"
                autoComplete="current-password"
                isDisabled={loginMutation.isPending} // Deshabilitar mientras carga
              />
            </FormControl>

            <Button
              type="submit"
              colorScheme="teal"
              w="100%"
              isLoading={loginMutation.isPending} // ⭐ Mostrar spinner mientras carga
              isDisabled={loginMutation.isPending} // Deshabilitar para evitar múltiples envíos
            >
              Ingresar
            </Button>
          </VStack>
        </Box>

        <Text>
          ¿No tienes cuenta?{' '}
          <Link as={RouterLink} to="/register" color="teal.500">
            Regístrate aquí
          </Link>
        </Text>
      </VStack>
    </Container>
  );
};

export default LoginPage;