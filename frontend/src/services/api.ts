// src/services/api.ts
import axios from 'axios';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// 1. Creamos una instancia de Axios con configuración base
const apiClient = axios.create({
  baseURL: API_BASE_URL, // La URL base de tu backend FastAPI
  withCredentials: true, // HttpOnly refresh scoped to /auth/browser/*
  headers: {
    'Content-Type': 'application/json',
  },
});

// Browser sign-in is exclusively through classService.login (Web Lock).
// This module only provides the shared Axios client and account registration.

// Aquí añadiremos más funciones en el futuro (ej. registerUser)
export const registerUser = async (firstName: string, lastName: string, email: string, password: string) => {
  // Conservamos íntegramente los apellidos compuestos.
  const payload = {
    first_name: firstName,
    last_name: lastName,
    email: email,
    password: password,
  };

  try {
    // A diferencia del login, el registro sí espera un JSON normal.
    const response = await apiClient.post('/users/register-client', payload);
    return response.data; // Devuelve los datos del usuario creado (sin la contraseña)
  } catch (error) {
    // Manejo de errores robusto, igual que en el login
    if (axios.isAxiosError(error) && error.response) {
      // El backend devuelve un error 400 si el email ya existe.
      // Extraemos el mensaje de 'detail'.
      const detail = error.response.data?.detail;
      const message = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? 'Revisá el nombre, apellido, correo y contraseña ingresados.'
          : 'Error al registrar la cuenta.';
      throw new Error(message);
    }
    throw new Error('Ocurrió un error de red inesperado.');
  }
};


export default apiClient;