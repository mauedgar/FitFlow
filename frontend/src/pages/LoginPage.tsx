
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

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
      const fakeResponse = {
        ok: true,
        json: async () => ({
          token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwicm9sIjoiYWRtaW4ifQ.fakeTokenForAdmin',
          rol: 'admin', // Puedes cambiar a 'cliente' para probar
        }),
      };

      if (!fakeResponse.ok) {
        throw new Error('Credenciales incorrectas');
      }

      const data = await fakeResponse.json();
      const { token, rol } = data;

      // Verificamos que los datos son correctos y el rol es válido antes de proceder
      if (token && isUserRole(rol)) {
        // Dentro de este bloque, TypeScript entiende que 'rol' es 'admin' | 'cliente'
        login(token, rol);

        toast({
          title: "Inicio de sesión exitoso",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
        if (rol === 'admin'){
          navigate('/admin')
        }else{
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