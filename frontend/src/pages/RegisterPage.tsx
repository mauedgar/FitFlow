import React, { useState } from 'react';
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Input,
  VStack,
  Text,
  Link,
  useToast
} from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';

const RegisterPage = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const navigate = useNavigate();
  const toast = useToast();

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast({
        title: "Error de validación",
        description: "Las contraseñas no coinciden.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    console.log('Datos de Registro:', { name, email, password });

    toast({
      title: "Cuenta creada.",
      description: "Hemos creado tu cuenta exitosamente.",
      status: "success",
      duration: 3000,
      isClosable: true,
    });
    
    navigate('/login');
  };

  return (
    <Flex minHeight="calc(100vh - 128px)" align="center" justify="center" bg="gray.50">
      {/* ===== INICIO DE LA CORRECCIÓN ===== */}
      <Box
        as="form" // El Box ahora es el formulario
        onSubmit={handleSubmit} // El handler se aplica aquí
        borderWidth={1}
        px={8}
        py={10}
        borderRadius="lg"
        boxShadow="lg"
        bg="white"
        width={{ base: '90%', sm: '450px' }}
      >
        {/* El VStack ahora solo se encarga del layout vertical */}
        <VStack spacing={6}> 
          <Heading as="h1" size="xl" textAlign="center" color="gray.700">
            Crear Cuenta
          </Heading>

          <FormControl isRequired>
            <FormLabel>Nombre</FormLabel>
            <Input
              type="text"
              placeholder="Ingresa tu nombre"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Email</FormLabel>
            <Input
              type="email"
              placeholder="tu@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Contraseña</FormLabel>
            <Input
              type="password"
              placeholder="********"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Confirmar Contraseña</FormLabel>
            <Input
              type="password"
              placeholder="********"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </FormControl>

          <Button type="submit" colorScheme="teal" width="full" size="lg">
            Registrarse
          </Button>

          <Text mt={4} textAlign="center">
            ¿Ya tienes una cuenta?{' '}
            <Link as={RouterLink} to="/login" color="teal.500" fontWeight="bold">
              Inicia Sesión
            </Link>
          </Text>
        </VStack>
      </Box>
    </Flex>
  );
};

export default RegisterPage;