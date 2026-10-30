import { toaster } from '../components/ui/toaster-store';
import React, { useState } from 'react';
import { Box, Button, Flex, Heading, Input, VStack, Text, Link, Field } from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { registerUser } from '../services/api';

const RegisterPage = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false); // ⭐ 2. Añadimos estado de carga
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true); // Empezamos la carga

    if (password !== confirmPassword) {
      toaster.create({
        title: "Error de validación",
        description: "Las contraseñas no coinciden.",
        type: "error",
        duration: 5000,
        closable: true,
      });
      setIsLoading(false); // Detenemos la carga si hay error de validación

      return;
    }
    try {
      await registerUser(name, email, password);

      toaster.create({
        title: "Cuenta creada.",
        description: "¡Registro exitoso! Ahora puedes iniciar sesión.",
        type: "success",
        duration: 3000,
        closable: true,
      });
      navigate('/login'); // Redirigimos al login tras el éxito

    } catch (error) {
      // Mostramos el error que nos llega desde el servicio de API
      toaster.create({
        title: "Error en el registro",
        description: error instanceof Error ? error.message : "Ocurrió un error inesperado.",
        type: "error",
        duration: 5000,
        closable: true,
      });
    } finally {
      setIsLoading(false); // ⭐ 5. Detenemos la carga en cualquier caso (éxito o error)
    }
  };

  return (
    <Flex minHeight="calc(100vh - 128px)" align="center" justify="center" bg="gray.50">
      <Box
        borderWidth={1}
        px={8}
        py={10}
        borderRadius="lg"
        boxShadow="lg"
        bg="white"
        width={{ base: '90%', sm: '450px' }}
        asChild><form
          // El handler se aplica aquí
          onSubmit={handleSubmit}>
          {/* El VStack ahora solo se encarga del layout vertical */}
          <VStack gap={6}>
            <Heading as="h1" size="xl" textAlign="center" color="gray.700">
              Crear Cuenta
            </Heading>

            <Field.Root required>
              <Field.Label>Nombre</Field.Label>
              <Input
                type="text"
                required
                placeholder="Ingresa tu nombre"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </Field.Root>

            <Field.Root required>
              <Field.Label>Email</Field.Label>
              <Input
                type="email"
                required
                placeholder="tu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Field.Root>

            <Field.Root required>
              <Field.Label>Contraseña</Field.Label>
              <Input
                type="password"
                required
                placeholder="********"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field.Root>

            <Field.Root required>
              <Field.Label>Confirmar Contraseña</Field.Label>
              <Input
                type="password"
                required
                placeholder="********"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </Field.Root>

            <Button type="submit" colorPalette="teal" width="full" size="lg" loading={isLoading}>
              Registrarse
            </Button>

            <Text mt={4} textAlign="center">
              ¿Ya tienes una cuenta?{' '}
              <Link color="teal.500" fontWeight="bold" asChild><RouterLink to="/login">Inicia Sesión
                            </RouterLink></Link>
            </Text>
          </VStack>
        </form></Box>
    </Flex>
  );
};

export default RegisterPage;
