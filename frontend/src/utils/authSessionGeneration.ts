/** Every useAuth login/logout advances this generation before React state changes. */
/** Nonsecret cross-tab epoch; check the shared value, not just event delivery. */
export const AUTH_SYNC_KEY = 'fitflow_browser_auth_epoch';
let generation = 0;
export const getAuthSessionGeneration = (): number => generation;
export const advanceAuthSessionGeneration = (): number => ++generation;
