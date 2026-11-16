import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../../context/useAuth';
import { verifiedAuthIdentityQuery } from '../../../utils/verifiedAuthIdentityQuery';

/** Single verified backend identity query shared by guard and header. */
export const useAdminIdentity = (locallyValid = true) => {
  const { currentUser, token, sessionGeneration } = useAuth();
  return useQuery({
    ...verifiedAuthIdentityQuery(token, sessionGeneration),
    enabled: locallyValid && currentUser?.role === 'admin',
  });
};
