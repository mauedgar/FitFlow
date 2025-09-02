/* eslint-disable @typescript-eslint/no-unused-vars */

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
import { useAuth, isUserRole } from '../context/AuthContext'; // Importamos el type guard
import { loginUser } from '../services/api'; // ⭐ 1. Importamos nuestra nueva función
import { jwtDecode } from 'jwt-decode'; // ⭐ 2. Importamos el decodificador de JWT

// Creamos un tipo para la información que esperamos del token
type DecodedToken = {
  sub: string; // "subject", que en nuestro caso es el email
  role: string; // el rol que añadimos en el backend
  exp: number; // fecha de expiración
};

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false); // Para feedback visual
  const { login } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // ⭐ 3. Reemplazamos la lógica falsa con la llamada real a la API
      const data = await loginUser(email, password);
      
      const token = data.access_token;
      
      // Decodificamos el token para obtener el rol
      const decodedToken = jwtDecode<DecodedToken>(token);
      const rol = decodedToken.role;

      if (token && isUserRole(rol)) {
        // Dentro de este bloque, TypeScript entiende que 'rol' es 'admin' | 'client' | 'trainer'
        login(token, rol);
        console.log(rol)
        toast({
          title: "Inicio de sesión exitoso",
          status: "success",
          duration: 3000,
          isClosable: true,
        });

        // Redirigimos basado en el rol obtenido del token
        if (rol === 'admin') {
          navigate('/admin');
        } else {
          navigate('/home');
        }
      } else {
        // Si el rol no es 'admin' o 'cliente', o no hay token, lanzamos un error

        throw new Error('Datos de autenticación inválidos desde el servidor.');
      }

    } catch (error) {
      toast({
        title: "Error al iniciar sesión",
        description: error instanceof Error ? error.message : "Ocurrió un error inesperado.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      console.error('Error de login:', error);
    } finally {
      setIsLoading(false); // Detenemos la carga, ya sea éxito o error
    }
  };
  
  return (
    <Container maxW="container.sm" py={10}>
      <VStack spacing={8}>
        <Heading>Iniciar Sesión</Heading>
        
        <Box as="form" onSubmit={handleSubmit} w="100%">
          <VStack spacing={4}>
            <FormControl isRequired>
              <FormLabel>Email</FormLabel>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@email.com"
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Contraseña</FormLabel>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="********"
              />
            </FormControl>

            <Button type="submit" colorScheme="teal" w="100%">
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