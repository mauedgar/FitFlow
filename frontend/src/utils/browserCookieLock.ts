/** Serialize all browser cookie writers across tabs; never send secrets by lock.
 *
 * The 12-second budget requests cooperative cancellation across queue and
 * execution. Every callback must pass the AbortSignal to its network calls.
 * Aborting a running callback does NOT force-release a Web Lock: it remains
 * exclusive until that callback settles. Never race it against a timeout
 * promise that could release it while a late cookie writer is still active.
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
