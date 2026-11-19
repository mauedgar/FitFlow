/** One HttpOnly cookie per origin: serialize login/logout across tabs.
 *
 * No bearer, CSRF, refresh token or session secret is exchanged via locks.
 * Cross-tab browser API failures fail closed: no uncoordinated cookie write.
 */
export async function withExclusiveBrowserCookie<T>(
  operation: () => Promise<T>,
): Promise<T> {
  if (typeof navigator === 'undefined' || !navigator.locks?.request) {
    throw new Error('Este navegador no permite coordinar sesiones seguras.');
  }
  return navigator.locks.request('fitflow-auth-cookie-write', { mode: 'exclusive' }, operation);
}
