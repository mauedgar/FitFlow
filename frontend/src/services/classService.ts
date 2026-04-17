// src/services/classService.ts
import apiClient from './api';

import {
  type GymClass,
  type GymClassCreatePayload,
  type ClassScheduleInResponse,
  type ClassSession,
  type Booking,
  type BookingCreatePayload,
  type TokenResponse
} from '../types';

interface LoginPayload {
  username: string;
  password: string;
}

const classService = {
  // --- Autenticación ---
  async login(payload: LoginPayload): Promise<TokenResponse> {
    try {
      const formData = new URLSearchParams();
      formData.append('username', payload.username);
      formData.append('password', payload.password);

      const response = await apiClient.post<TokenResponse>('/login/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error al hacer login:', error);
      throw error;
      // throw new Error('No se pudo iniciar sesión');
    }
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
      const response = await apiClient.get<GymClass>(`/gym-classes/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error al obtener la clase con ID ${id}:`, error);
      throw error;
      // throw new Error('No se pudo cargar la clase');
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
      await apiClient.delete(`/bookings/${bookingId}`);
    } catch (error) {
      console.error(`Error al cancelar la reserva con ID ${bookingId}:`, error);
      throw error;
    }
  },
};

export default classService;