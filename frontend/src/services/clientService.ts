import apiClient from './api';

export interface AdminClientSummary {
  id: string;
  full_name: string;
  email: string;
  phone?: string | null;
  avatar_url?: string | null;
  created_at?: string | null;
}

/**
 * Lists up to 100 clients from the admin-only ClientPublic projection.
 * Pagination beyond this page is deliberately not implied by the UI.
 */
export const getAdminClients = async (): Promise<AdminClientSummary[]> => {
  const { data } = await apiClient.get<AdminClientSummary[]>('/clients/', {
    params: { skip: 0, limit: 100 },
  });
  return data;
};
