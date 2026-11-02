// src/services/api.ts
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import type { TokenPayload } from '../types';
import { registrationErrorMessage } from '../utils/registrationErrors';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// 1. Creamos una instancia de Axios con configuración base
const apiClient = axios.create({
  baseURL: API_BASE_URL, // La URL base de tu backend FastAPI
  headers: {
    'Content-Type': 'application/json',
  },
});


const ACCESS_KEY = "fitflow_access_token";
const REFRESH_KEY = "fitflow_refresh_token";
let renewalInFlight: Promise<string> | null = null;

function accessUsable(token: string | null): token is string {
  if (!token) return false;
  try {
    const payload = jwtDecode<TokenPayload>(token);
    return payload.token_use === 'access' && !!payload.sub &&
      ['admin', 'teacher', 'client', 'front_desk'].includes(payload.role) &&
      Number.isFinite(payload.exp) && payload.exp > Date.now() / 1000 + 15;
  } catch {
    return false;
  }
}

function protectedEndpoint(url: string | undefined): boolean {
  const path = url ?? '';
  return !/\/auth\/(?:token|refresh|logout)(?:\?|$)|\/users\/register(?:\?|$)/.test(path);
}

/** Single-flight refresh shared by mounted React views and Axios requests. */
export async function ensureFreshAccess(force = false): Promise<string> {
  const access = sessionStorage.getItem(ACCESS_KEY);
  if (!force && accessUsable(access)) return access;
  const refresh = sessionStorage.getItem(REFRESH_KEY);
  if (!refresh) throw new Error('No active refresh credential');
  if (!renewalInFlight) {
    const flight = (async () => {
      // Raw Axios instance avoids recursive refresh interceptors.
      const response = await axios.post<{ access_token: string }>(
        `${API_BASE_URL}/auth/refresh`, { refresh_token: refresh },
      );
      const next = response.data.access_token;
      if (!accessUsable(next) || sessionStorage.getItem(REFRESH_KEY) !== refresh) {
        throw new Error('Invalidated or malformed renewed access credential');
      }
      sessionStorage.setItem(ACCESS_KEY, next);
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${next}`;
      window.dispatchEvent(new Event('fitflow:access-renewed'));
      return next;
    })();
    renewalInFlight = flight;
    void flight.finally(() => {
      if (renewalInFlight === flight) renewalInFlight = null;
    }).catch(() => undefined);
  }
  return renewalInFlight;
}

apiClient.interceptors.request.use(async (config) => {
  if (!protectedEndpoint(config.url)) return config;
  if (!sessionStorage.getItem(REFRESH_KEY)) return config;
  // Respect a new explicit Bearer supplied by login's /auth/me verification.
  const passed = config.headers.get('Authorization');
  const stored = sessionStorage.getItem(ACCESS_KEY);
  if (passed && passed !== `Bearer ${stored}`) return config;
  try {
    const token = await ensureFreshAccess();
    config.headers.set('Authorization', `Bearer ${token}`);
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      window.dispatchEvent(new Event('fitflow:session-invalid'));
    }
    throw error;
  }
  return config;
});

// One retry for a protected 401, never for login, logout or refresh itself.
apiClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) return Promise.reject(error);
    const original = error.config;
    const retry = original as (typeof original & { _fitflowRetried?: boolean }) | undefined;
    if (error.response?.status !== 401 || !retry || retry._fitflowRetried ||
        !protectedEndpoint(retry.url) || !sessionStorage.getItem(REFRESH_KEY) ||
        (retry.headers.get('Authorization') &&
         retry.headers.get('Authorization') !==
           `Bearer ${sessionStorage.getItem(ACCESS_KEY)}`)) {
      return Promise.reject(error);
    }
    retry._fitflowRetried = true;
    try {
      const token = await ensureFreshAccess(true);
      retry.headers.set('Authorization', `Bearer ${token}`);
      return await apiClient.request(retry);
    } catch (retryError) {
      if (axios.isAxiosError(retryError) &&
          (retryError.response?.status === 401 || retryError.response?.status === 403)) {
        window.dispatchEvent(new Event('fitflow:session-invalid'));
      }
      return Promise.reject(retryError);
    }
  },
);

// 2. Definimos la función de login
// Nota: Le cambiamos el nombre a loginUser para evitar confusión con el login del AuthContext
export const loginUser = async (email: string, password: string) => {
  // FastAPI con OAuth2PasswordRequestForm espera datos de formulario, no JSON.
  // Usamos URLSearchParams para formatear los datos correctamente.
  const formData = new URLSearchParams();
  formData.append('username', email); // 'username' es el campo que espera FastAPI
  formData.append('password', password);

  try {
    const response = await apiClient.post('/auth/token', formData, {
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
export const registerUser = async (fullName: string, email: string, password: string) => {
  // El backend espera un campo 'full_name', así que mapeamos 'fullName' a él.
  const payload = {
    full_name: fullName,
    email: email,
    password: password,
  };

  try {
    // A diferencia del login, el registro sí espera un JSON normal.
    const response = await apiClient.post('/users/register', payload);
    return response.data; // Devuelve los datos del usuario creado (sin la contraseña)
  } catch (error) {
    // Manejo de errores robusto, igual que en el login
    if (axios.isAxiosError(error) && error.response) {
      // 422 Pydantic devuelve una lista; nunca mostrar "[object Object]" al usuario.
      throw new Error(registrationErrorMessage(error.response.status, error.response.data?.detail));
    }
    throw new Error('Ocurrió un error de red inesperado.');
  }
};


export default apiClient;