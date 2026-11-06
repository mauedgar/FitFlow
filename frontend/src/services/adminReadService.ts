import apiClient from './api';

/** Restricted to the safe public/operational projections of existing API endpoints. */
export interface AdminTeacherSummary {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  bio?: string | null;
  profile_image_url?: string | null;
}

export interface AdminGymClassSummary {
  id: string;
  name: string;
  description: string;
  duration_minutes: number;
  default_capacity: number;
  difficulty?: string | null;
  activity_type: string;
  image_url?: string | null;
}

export const getAdminTeacherSummaries = async (signal?: AbortSignal): Promise<AdminTeacherSummary[]> => {
  // This public teacher projection contains display-only fields.
  const { data } = await apiClient.get<AdminTeacherSummary[]>('/teachers/public', { signal });
  return data;
};

export const getAdminGymClassSummaries = async (signal?: AbortSignal): Promise<AdminGymClassSummary[]> => {
  const { data } = await apiClient.get<AdminGymClassSummary[]>('/gym-classes/public', { signal });
  return data;
};
