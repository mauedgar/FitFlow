import apiClient from './api';
import { type BookingStatus } from '../types';

export interface FrontDeskSession {
  id: string;
  class_schedule_id: string;
  gym_class_id: string;
  teacher_id: string;
  starts_at: string;
  ends_at: string;
  status: string;
  gym_class_name: string;
  teacher_full_name: string;
  capacity_snapshot: number;
  current_bookings_count: number;
  available_spots: number;
  is_live: boolean;
  is_upcoming: boolean;
  is_full: boolean;
  is_empty: boolean;
}

export interface FrontDeskBooking {
  id: string;
  client_id: string;
  client_name: string;
  client_email: string;
  status: BookingStatus;
}

export interface FrontDeskDay {
  date: string;
  sessions: FrontDeskSession[];
}

const frontDeskService = {
  async getToday(): Promise<FrontDeskDay> {
    const response = await apiClient.get<FrontDeskDay>('/front-desk/sessions/today');
    return response.data;
  },

  async getSessionBookings(sessionId: string): Promise<FrontDeskBooking[]> {
    const response = await apiClient.get<FrontDeskBooking[]>(
      `/front-desk/sessions/${sessionId}/bookings`,
    );
    return response.data;
  },

  async checkIn(sessionId: string, bookingId: string): Promise<FrontDeskBooking> {
    const response = await apiClient.post<FrontDeskBooking>(
      `/front-desk/sessions/${sessionId}/bookings/${bookingId}/check-in`,
    );
    return response.data;
  },
};

export default frontDeskService;
