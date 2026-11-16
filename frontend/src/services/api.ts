// src/services/api.ts
import axios from 'axios';
import { registrationErrorMessage } from '../utils/registrationErrors';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// 1. Creamos una instancia de Axios con configuración base
const apiClient = axios.create({
  baseURL: API_BASE_URL, // La URL base de tu backend FastAPI
  headers: {
    'Content-Type': 'application/json',
  },
});

// 2. Definimos la función de login
// Nota: Le cambiamos el nombre a loginUser para evitar confusión con el login del AuthContext
export const loginUser = async (email: string, password: string) => {
  // FastAPI con OAuth2PasswordRequestForm espera datos de formulario, no JSON.
  // Usamos URLSearchParams para formatear los datos correctamente.
  const formData = new URLSearchParams();
  formData.append('username', email); // 'username' es el campo que espera FastAPI
  formData.append('password', password);

  try {
    const response = await apiClient.post('/login/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    // La respuesta de FastAPI contiene { access_token: "...", token_type: "bearer" }
    return response.data; 
  } catch (error) {
    // Si Axios recibe un error (ej. 401 Unauthorized), lo lanzará.
    // Lo personalizamos para que sea más claro.
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Error al iniciar sesión');
    }
    throw new Error('Ocurrió un error de red inesperado.');
  }
};

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
      throw new Error(registrationErrorMessage(error.response.status, error.response.data?.detail));
    }
    throw new Error('Ocurrió un error de red inesperado.');
  }
};


export default apiClient;