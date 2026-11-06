import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../../context/useAuth';
import { getAdminAuthenticatedIdentity } from '../../../services/adminReadService';

/** Single verified backend identity query shared by guard and header. */
export const useAdminIdentity = (locallyValid = true) => {
  const { currentUser, sessionGeneration } = useAuth();
  return useQuery({
    queryKey: ['adminIdentity', currentUser?.email, sessionGeneration],
    queryFn: ({ signal }) => getAdminAuthenticatedIdentity(signal),
    enabled: locallyValid && currentUser?.role === 'admin',
    staleTime: 30_000,
    retry: false,
  });
};
