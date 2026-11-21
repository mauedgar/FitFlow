// src/services/classService.ts
import axios from 'axios';
import apiClient from './api';
import { withExclusiveBrowserCookie } from '../utils/browserCookieLock';
import { AUTH_SYNC_KEY, getAuthSessionGeneration } from '../utils/authSessionGeneration';

import {
  type GymClass,
  type GymClassCreatePayload,
  type ClassScheduleInResponse,
  type ClassScheduleWithNextSession,
  type ClassSession,
  type Booking,
  type BookingCreatePayload,
  type BrowserSessionResponse,
  type ClientWeeklyAgendaView
} from '../types';

interface LoginPayload {
  username: string;
  password: string;
}

/** Missing/expired signed cookie: no exact server revocation receipt possible. */
export class BrowserLogoutProofUnavailable extends Error {
  constructor() {
    super('La credencial del logout ya no está disponible.');
    this.name = 'BrowserLogoutProofUnavailable';
  }
}

/** Stale queued logins must not write a new cookie after a real logout. */
export class BrowserLoginSuperseded extends Error {
  constructor() {
    super('El estado de la sesión cambió antes de iniciar el login.');
    this.name = 'BrowserLoginSuperseded';
  }
}

const classService = {
  // --- Autenticación ---
  async login(
    payload: LoginPayload,
    expectedGeneration: number,
    expectedSharedEpoch: string | null,
  ): Promise<BrowserSessionResponse> {
    return withExclusiveBrowserCookie(async (signal) => {
      // Evaluate inside the Web Lock before POST/Set-Cookie. Cross-tab storage
      // events can arrive late, so compare the actual shared epoch too.
      if (getAuthSessionGeneration() !== expectedGeneration ||
          localStorage.getItem(AUTH_SYNC_KEY) !== expectedSharedEpoch ||
          sessionStorage.getItem('fitflow_logout_pending') === '1') {
        throw new BrowserLoginSuperseded();
      }
      const formData = new URLSearchParams();
      formData.append('username', payload.username);
      formData.append('password', payload.password);
      const response = await apiClient.post<BrowserSessionResponse>(
        '/auth/browser/token', formData,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, signal },
      );
      return response.data;
    });
  },

  async restoreBrowserSession(): Promise<BrowserSessionResponse> {
    const result = await apiClient.get<BrowserSessionResponse>('/auth/browser/session');
    return result.data;
  },

  async refreshBrowserSession(): Promise<BrowserSessionResponse> {
    // Acquire the lock BEFORE reading the cookie-bound CSRF proof. A token
    // captured by React before the lock wait may belong to another cookie.
    return withExclusiveBrowserCookie(async (signal) => {
      const proof = await apiClient.get<{ csrf_token: string }>(
        '/auth/browser/logout-proof', { signal },
      );
      const result = await apiClient.post<BrowserSessionResponse>(
        '/auth/browser/refresh', undefined,
        { headers: { 'X-CSRF-Token': proof.data.csrf_token }, signal },
      );
      return result.data;
    });
  },

  async recoverLogoutProof(): Promise<{ csrf_token: string }> {
    const response = await apiClient.get<{ csrf_token: string }>(
      '/auth/browser/logout-proof',
    );
    return response.data;
  },

  async logoutBrowserSession(): Promise<void> {
    // Deprecated compatibility wrapper: never trust a proof captured before
    // acquiring the Web Lock. Obtain the current proof and revoke atomically.
    await this.retryBrowserLogoutFromCookie();
  },

  async retryBrowserLogoutFromCookie(onConfirmed?: () => void): Promise<void> {
    // Lock GET proof and POST revocation as one cookie-dependent operation.
    // Only a 401 at the proof GET proves that no usable signed cookie can
    // identify the former session; a failed POST remains unconfirmed.
    await withExclusiveBrowserCookie(async (signal) => {
      let csrf: string;
      try {
        const proof = await apiClient.get<{ csrf_token: string }>(
          '/auth/browser/logout-proof', { signal },
        );
        csrf = proof.data.csrf_token;
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          throw new BrowserLogoutProofUnavailable();
        }
        throw error;
      }
      const response = await apiClient.post<void>(
        '/auth/browser/logout', undefined,
        { headers: { 'X-CSRF-Token': csrf }, signal },
      );
      if (response.status !== 204) {
        // Axios accepts any 2xx by default; only HTTP 204 is the durable
        // PostgreSQL revocation ACK. Other 2xx leave logout pending.
        throw new Error('El servidor no confirmó la revocación de la sesión.');
      }
      // Invoke ONLY after exact HTTP 204 while Web Lock is still held.
      onConfirmed?.();
    });
  },

  // --- GymClass Endpoints ---
  async getAllClasses(): Promise<GymClass[]> {
    try {
      const response = await apiClient.get<GymClass[]>('/gym-classes/');
      return response.data;
    } catch (error) {
      console.error('Error al obtener la lista de clases:', error);
      throw error;
      // throw new Error('No se pudieron cargar las clases');
    }
  },

  async getClassById(id: string): Promise<GymClass> {
    try {
      const [classResponse, schedulesResponse] = await Promise.all([
        apiClient.get<Omit<GymClass, 'class_schedules'>>(`/gym-classes/${id}/public`),
        apiClient.get<ClassScheduleInResponse[]>(`/gym-classes/${id}/schedules/public`),
      ]);

      const classSchedules: ClassScheduleWithNextSession[] = await Promise.all(
        schedulesResponse.data.map(async (schedule) => {
          const nextSessionResponse = await apiClient.get<
            ClassScheduleWithNextSession['next_upcoming_session']
          >(`/class-schedules/${schedule.id}/next-session`);

          return {
            ...schedule,
            next_upcoming_session: nextSessionResponse.data,
          };
        }),
      );

      return {
        ...classResponse.data,
        class_schedules: classSchedules,
      };
    } catch (error) {
      console.error(`Error al obtener la clase con ID ${id}:`, error);
      throw error;
    }
  },

  async createClass(payload: GymClassCreatePayload): Promise<GymClass> {
    try {
      const response = await apiClient.post<GymClass>('/gym-classes/', payload);
      return response.data;
    } catch (error) {
      console.error('Error al crear la clase:', error);
      throw error;
      // throw new Error('No se pudo crear la clase');
    }
  },

  // --- ClassSchedule Endpoints ---
  async getAllClassSchedules(gymClassId?: string): Promise<ClassScheduleInResponse[]> {
    try {
      const params = gymClassId ? { gym_class_id: gymClassId } : {};
      const response = await apiClient.get<ClassScheduleInResponse[]>('/class-schedules/', { params });
      return response.data;
    } catch (error) {
      console.error('Error al obtener los horarios de clases:', error);
      throw error;
    }
  },

  async getClassScheduleById(id: string): Promise<ClassScheduleInResponse> {
    try {
      const response = await apiClient.get<ClassScheduleInResponse>(`/class-schedules/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error al obtener el horario de clase con ID ${id}:`, error);
      throw error;
    }
  },

  // --- ClassSession Endpoints ---
  async getClassSessions(
    classScheduleId: string,
    fromDate: string,
    toDate: string,
    includeCancelled: boolean = false
  ): Promise<ClassSession[]> {
    try {
      const response = await apiClient.get<ClassSession[]>('/class-sessions/', {
        params: {
          class_schedule_id: classScheduleId,
          from_date: fromDate,
          to_date: toDate,
          include_cancelled: includeCancelled,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error al obtener las sesiones de clase:', error);
      throw error;
    }
  },

  async getClassSessionById(id: string): Promise<ClassSession> {
    try {
      const response = await apiClient.get<ClassSession>(`/class-sessions/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error al obtener la sesión de clase con ID ${id}:`, error);
      throw error;
    }
  },

  // Read-only authenticated Client projection for a seven-day local calendar window.
  async getClientWeeklyAgenda(weekStart: string): Promise<ClientWeeklyAgendaView> {
    const response = await apiClient.get<ClientWeeklyAgendaView>('/class-sessions/weekly-agenda', {
      params: { week_start: weekStart },
    });
    return response.data;
  },

  // --- Booking Endpoints ---
  async createBooking(payload: BookingCreatePayload): Promise<Booking> {
    try {
      const response = await apiClient.post<Booking>('/bookings/', payload);
      return response.data;
    } catch (error) {
      console.error('Error al crear la reserva:', error);
      throw error;
    }
  },

  async getMyBookings(): Promise<Booking[]> {
    try {      
      const response = await apiClient.get<Booking[]>('/bookings/me');
      return response.data;
    } catch (error) {
      console.error('Error al obtener tus reservas:', error);
      throw error;
    }
  },

  async cancelBooking(bookingId: string): Promise<void> {
    try {
      await apiClient.post(`/bookings/${bookingId}/cancel`);
    } catch (error) {
      console.error(`Error al cancelar la reserva con ID ${bookingId}:`, error);
      throw error;
    }
  },
};

export default classService;
