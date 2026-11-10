import axios from 'axios';

/** A transport/server outage is not evidence of authorization or revocation. */
export function isRecoverableIdentityFailure(error: unknown): boolean {
  if (!axios.isAxiosError(error)) return false;
  const status = error.response?.status;
  return status === undefined || status === 429 || status >= 500;
}
