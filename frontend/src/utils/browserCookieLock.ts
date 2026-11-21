/** Serialize all browser cookie writers across tabs; never send secrets by lock.
 *
 * The budget covers time queued AND time holding the lock. Every callback
 * must propagate the provided AbortSignal to every network request, ensuring
 * stalled network promises cancel before another tab may write the cookie.
 */
const COOKIE_OPERATION_BUDGET_MS = 12_000;

export async function withExclusiveBrowserCookie<T>(
  operation: (signal: AbortSignal) => Promise<T>,
): Promise<T> {
  if (typeof navigator === 'undefined' || !navigator.locks?.request) {
    throw new Error('Este navegador no permite coordinar sesiones seguras.');
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), COOKIE_OPERATION_BUDGET_MS);
  try {
    return await navigator.locks.request(
      'fitflow-auth-cookie-write',
      { mode: 'exclusive', signal: controller.signal },
      () => operation(controller.signal),
    );
  } finally {
    clearTimeout(timeoutId);
  }
}
