const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');
const load = (p) => fs.readFileSync(path.join(__dirname, '..', 'src', p), 'utf8');

test('Login errors never log the AxiosError or stringify arbitrary response data', () => {
  const page = load('pages/LoginPage.tsx');
  const service = load('services/classService.ts').split('// --- GymClass Endpoints ---')[0];
  assert.doesNotMatch(page, /console\.(log|error|debug|warn|info)\s*\(/);
  assert.doesNotMatch(page, /JSON\.stringify\(error\.response\.data\)/);
  assert.match(page, /error\.response\?\.status === 401/);
  assert.doesNotMatch(page, /error\.response\.data/);
  assert.doesNotMatch(service, /console\.(log|error|debug|warn|info)\s*\(/);
  assert.match(service, /await apiClient\.post<BrowserSessionResponse>\(/);
  assert.match(service, /'\/auth\/browser\/token'/);
  assert.match(service, /withExclusiveBrowserCookie/);
  assert.doesNotMatch(service, /localStorage\.setItem\(/);
});

test('Mobile navigation uses semantic RouterLink destinations rather than inert anchors', () => {
  const source = load('components/layout/Navbar.tsx');
  for (const route of ['/', '/home', '/classes']) {
    assert.ok(source.includes('to="' + route + '" onClick={onClose}'), 'missing semantic route ' + route);
  }
  assert.doesNotMatch(source, /<Link onClick=\{/);
});

test('Carousel pauses autoplay on pointer or focus and respects reduced motion', () => {
  const source = load('components/landing/InfiniteCarousel.tsx');
  for (const token of ['useReducedMotion', 'onMouseEnter', 'onMouseLeave',
      'onFocusCapture', 'onBlurCapture', 'setIsHovered', 'setIsFocusWithin', 'isHovered || isFocusWithin || shouldReduceMotion',
      'shouldReduceMotion ? { duration: 0 }']) {
    assert.ok(source.includes(token), 'missing ' + token);
  }
});


test('Browser login blocks while durable logout is pending and synchronizes tabs without bearer storage', () => {
  const page = load('pages/LoginPage.tsx');
  const provider = load('context/AuthProvider.tsx');
  assert.match(page, /logoutConfirmation === ['"]pending['"]/);
  assert.match(page, /disabled=\{loginMutation\.isPending \|\| logoutConfirmation === ['"]pending['"]\}/);
  assert.match(provider, /window\.addEventListener\("storage", onSharedSession\)/);
  assert.match(provider, /advanceAuthSessionGeneration\(\)/);
  assert.match(provider, /notifyOtherTabs\("logout-pending", operation\)/);
  assert.match(provider, /notifyOtherTabs\("logout-confirmed"\)/);
  assert.match(provider, /\[2000, 5000, 10000\]/);
  assert.doesNotMatch(provider, /localStorage\.setItem\(LEGACY_ACCESS, accessToken\)\s*;\s*\/\/.*modern/);
});


test('Browser refresh participates in the exclusive login/logout cookie lock', () => {
  const service = load('services/classService.ts');
  const login = service.split('async login(')[1].split('async restoreBrowserSession')[0];
  const refresh = service.split('async refreshBrowserSession')[1].split('async recoverLogoutProof')[0];
  const logout = service.split('async retryBrowserLogoutFromCookie')[1].split('// --- GymClass Endpoints ---')[0];
  for (const op of [login, refresh, logout]) {
    assert.ok(op.includes('withExclusiveBrowserCookie(async (signal) => {'));
  }
  assert.ok(refresh.includes("'/auth/browser/refresh'"));
  assert.ok(!refresh.includes('localStorage.'));
});


test('Missing signed logout cookie unblocks login without inventing PostgreSQL ACK', () => {
  const provider = load('context/AuthProvider.tsx');
  const service = load('services/classService.ts');
  const page = load('pages/LoginPage.tsx');
  assert.ok(provider.includes("error instanceof BrowserLogoutProofUnavailable"));
  assert.ok(provider.includes("setLogoutConfirmation('expired-unconfirmed')"));
  assert.ok(provider.includes('notifyOtherTabs("logout-expired-unconfirmed", operation ?? undefined)'));
  assert.ok(provider.includes('classService.retryBrowserLogoutFromCookie(() => {'));
  assert.ok(service.includes('async retryBrowserLogoutFromCookie(onConfirmed?: () => void)'));
  assert.ok(service.includes('withExclusiveBrowserCookie(async (signal) => {'));
  assert.ok(service.includes("error.response?.status === 401"));
  assert.ok(page.includes("logoutConfirmation === 'expired-unconfirmed'"));
  assert.ok(!page.includes('la revocación quedó confirmada'));
});


test('Browser provider never restores or stores legacy localStorage bearer', () => {
  const provider = load('context/AuthProvider.tsx');
  const context = load('context/AuthContext.tsx');
  const useAuth = load('context/useAuth.tsx');
  assert.ok(provider.includes('localStorage.removeItem(LEGACY_ACCESS);'));
  assert.ok(!provider.includes('localStorage.getItem(LEGACY_ACCESS)'));
  assert.ok(!provider.includes('localStorage.setItem(LEGACY_ACCESS'));
  assert.ok(!provider.includes('legacy-unconfirmed'));
  assert.ok(!provider.includes('notifyOtherTabs("legacy-logout")'));
  assert.ok(provider.includes('if (!csrf || !accessToken) return;'));
  assert.ok(provider.includes('void retryLogout();'));
  assert.ok(context.includes('csrfToken: string'));
  assert.ok(useAuth.includes('csrfToken: string'));
});

test('Login responses are rejected after newer auth generation; refresh proof is read INSIDE the cookie lock', () => {
  const page = load('pages/LoginPage.tsx');
  const service = load('services/classService.ts');
  const admin = load('components/admin/auth/AdminSessionGate.tsx');
  const provider = load('context/AuthProvider.tsx');
  assert.ok(page.includes('startedGeneration = getAuthSessionGeneration()'));
  assert.ok(page.includes('startedGeneration !== getAuthSessionGeneration()'));
  assert.ok(page.includes('const accepted = login(data.access_token, data.csrf_token);'));
  assert.ok(page.indexOf('startedGeneration !== getAuthSessionGeneration()') <
    page.indexOf('const accepted = login(data.access_token, data.csrf_token);'));
  assert.ok(page.includes('if (!accepted) return;'));
  const refresh = service.split('async refreshBrowserSession()')[1]
    .split('async recoverLogoutProof')[0];
  assert.ok(refresh.includes('withExclusiveBrowserCookie(async (signal) => {'));
  assert.ok(refresh.indexOf("'\/auth/browser/logout-proof'") <
    refresh.indexOf("'\/auth/browser/refresh'"));
  assert.ok(!refresh.includes('csrfToken: string'));
  assert.ok(provider.includes('classService.refreshBrowserSession()'));
  assert.ok(!admin.includes("localStorage.getItem('access_token')"));
});


test('Cookie Web Lock uses a finite abort budget and all auth writers propagate AbortSignal', () => {
  const lock = load('utils/browserCookieLock.ts');
  const service = load('services/classService.ts');
  assert.ok(lock.includes('COOKIE_OPERATION_BUDGET_MS = 12_000'));
  assert.ok(lock.includes('setTimeout(() => controller.abort()'));
  assert.ok(lock.includes('signal: controller.signal'));
  assert.ok(lock.includes('() => operation(controller.signal)'));
  assert.ok(lock.includes('clearTimeout(timeoutId)'));
  const login = service.split('async login(')[1]
    .split('async restoreBrowserSession')[0];
  const refresh = service.split('async refreshBrowserSession()')[1]
    .split('async recoverLogoutProof')[0];
  const retry = service.split('async retryBrowserLogoutFromCookie(onConfirmed?: () => void)')[1]
    .split('// --- GymClass Endpoints ---')[0];
  for (const op of [login, refresh, retry]) {
    assert.ok(op.includes('withExclusiveBrowserCookie(async (signal) => {'));
    assert.ok(op.includes('signal'));
  }
  const legacy = service.split('async logoutBrowserSession()')[1]
    .split('async retryBrowserLogoutFromCookie')[0];
  assert.ok(legacy.includes('this.retryBrowserLogoutFromCookie()'));
  assert.ok(!legacy.includes("X-CSRF-Token"));
});


test('No alternate browser login path may bypass the exclusive cookie Web Lock', () => {
  const srcRoot = path.join(__dirname, '..', 'src');
  const queue = [srcRoot];
  const offenders = [];
  while (queue.length) {
    const folder = queue.pop();
    if (!folder) continue;
    for (const item of fs.readdirSync(folder, { withFileTypes: true })) {
      const absolute = path.join(folder, item.name);
      if (item.isDirectory()) queue.push(absolute);
      else if (item.name.endsWith('.ts') || item.name.endsWith('.tsx')) {
        const relative = path.relative(srcRoot, absolute).split(path.sep).join('/');
        if (relative !== 'services/classService.ts' &&
            fs.readFileSync(absolute, 'utf8').includes('/auth/browser/token')) {
          offenders.push(relative);
        }
      }
    }
  }
  assert.deepEqual(offenders, [], 'Only locked classService may write the browser login cookie');
  assert.doesNotMatch(load('services/api.ts'), /export const loginUser/);
});


test('Queued browser login rechecks the cross-tab epoch inside its Web Lock', () => {
  const page = load('pages/LoginPage.tsx');
  const service = load('services/classService.ts');
  const generation = load('utils/authSessionGeneration.ts');
  const provider = load('context/AuthProvider.tsx');
  assert.ok(generation.includes("AUTH_SYNC_KEY = 'fitflow_browser_auth_epoch'"));
  assert.ok(page.includes('const startedEpoch = localStorage.getItem(AUTH_SYNC_KEY)'));
  assert.ok(page.includes('classService.login(credentials, startedGeneration, startedEpoch)'));
  const login = service.split('async login(')[1].split('async restoreBrowserSession')[0];
  assert.ok(login.indexOf('withExclusiveBrowserCookie(async (signal)') <
    login.indexOf('getAuthSessionGeneration() !== expectedGeneration'));
  assert.ok(login.indexOf('localStorage.getItem(AUTH_SYNC_KEY) !== expectedSharedEpoch') <
    login.indexOf("'/auth/browser/token'"));
  assert.ok(login.includes('throw new BrowserLoginSuperseded()'));
  assert.ok(provider.includes('retryLogoutInFlight.current'));
});

test('Same-tab logout advances generation; all SPA credential restores compare shared epoch', () => {
  const provider = load('context/AuthProvider.tsx');
  const page = load('pages/LoginPage.tsx');
  const logout = provider.split('const logout = () => {')[1]
    .split('// Bounded retries')[0];
  assert.ok(logout.indexOf('advanceAuthSessionGeneration();') <
    logout.indexOf('setToken(null);'));
  assert.ok(logout.includes("sessionStorage.setItem(PENDING_LOGOUT, '1')"));
  assert.ok(provider.includes('const eventEpoch = event.newValue'));
  assert.ok(provider.includes('localStorage.getItem(SYNC_KEY) !== eventEpoch'));
  assert.ok(provider.includes('localStorage.getItem(SYNC_KEY) !== sharedEpoch'));
  assert.ok(provider.includes("sessionStorage.getItem(PENDING_LOGOUT) === '1'"));
  assert.ok(page.includes('localStorage.getItem(AUTH_SYNC_KEY) !== startedEpoch'));
});

test('Orphaned cross-tab pending logout schedules a bounded signed recovery', () => {
  const provider = load('context/AuthProvider.tsx');
  assert.ok(provider.includes('needsOrphanRecovery.current = true;'));
  assert.ok(provider.includes('window.setTimeout(recover, 150)'));
  assert.ok(provider.includes("window.addEventListener('online', recover)"));
  assert.ok(provider.includes("window.removeEventListener('online', recover)"));
  assert.ok(provider.includes("sessionStorage.getItem(PENDING_LOGOUT) === '1'"));
  assert.ok(provider.includes('if (retryLogoutInFlight.current) return retryLogoutInFlight.current'));
  assert.ok(provider.includes('localStorage.getItem(SYNC_KEY) !== sharedEpoch'));
  assert.ok(provider.includes("sessionStorage.getItem(PENDING_LOGOUT) !== '1'"));
});

test('A real HTTP204 ACK is recorded while the exclusive cookie Web Lock remains held', () => {
  const provider = load('context/AuthProvider.tsx');
  const service = load('services/classService.ts');
  assert.ok(provider.includes('const CONFIRMED_OPERATION = "fitflow_logout_confirmed_operation"'));
  assert.ok(provider.includes('sessionStorage.setItem(PENDING_OPERATION, operation)'));
  assert.ok(provider.includes('localStorage.setItem(CONFIRMED_OPERATION, operation)'));
  assert.ok(provider.includes('recordConfirmedLogout(operation)'));
  assert.ok(provider.includes('confirmedHistory().includes(operation)'));
  assert.ok(provider.includes('isConfirmedLogout(operation)'));
  assert.ok(provider.includes('signalOperation(epoch) === operation'));
  const logout = service.split('async retryBrowserLogoutFromCookie(onConfirmed?: () => void)')[1]
    .split('// --- GymClass Endpoints ---')[0];
  assert.ok(logout.includes('withExclusiveBrowserCookie(async (signal) => {'));
  assert.ok(logout.indexOf('await apiClient.post(') < logout.indexOf('onConfirmed?.();'));
  assert.ok(logout.indexOf('onConfirmed?.();') < logout.indexOf('    });'));
});

test('Only exact HTTP204 may record a browser logout ACK, even without local pending state', () => {
  const service = load('services/classService.ts');
  const provider = load('context/AuthProvider.tsx');
  const logout = service.split('async retryBrowserLogoutFromCookie(onConfirmed?: () => void)')[1]
    .split('// --- GymClass Endpoints ---')[0];
  assert.ok(logout.includes('response.status !== 204'));
  assert.ok(logout.indexOf('response.status !== 204') < logout.indexOf('onConfirmed?.();'));
  assert.ok(provider.includes('action === "logout-confirmed" && !realAck'));
  assert.ok(provider.includes('setLogoutConfirmation(realAck ? "confirmed" : "expired-unconfirmed")'));
});

test('Rejected login never bumps generation or sends a success toast', () => {
  const hook = load('context/useAuth.tsx');
  const provider = load('context/AuthProvider.tsx');
  const ctx = load('context/AuthContext.tsx');
  const page = load('pages/LoginPage.tsx');
  assert.ok(!hook.includes('advanceAuthSessionGeneration();'));
  assert.ok(ctx.includes('login: (accessToken: string, csrfToken: string) => boolean;'));
  const section = provider.split('const login = (accessToken: string, csrf: string): boolean')[1]
    .split('const retryLogout = useCallback')[0];
  assert.ok(section.indexOf("return false;") < section.indexOf('advanceAuthSessionGeneration();'));
  assert.ok(section.includes('return true;'));
  assert.ok(page.indexOf('if (!accepted) return;') < page.indexOf('title: "Inicio de sesión exitoso"'));
});

test('Terminal logout validates pending identity before clearing a newer bearer', () => {
  const p = load('context/AuthProvider.tsx');
  const eventHandler = p.split('const onSharedSession = (event: StorageEvent) => {')[1]
    .split('window.addEventListener("storage", onSharedSession)')[0];
  assert.ok(eventHandler.indexOf('pendingOperation && pendingOperation !== operation) return') <
    eventHandler.indexOf('const generation = advanceAuthSessionGeneration();'));
  assert.ok(eventHandler.indexOf('action === "logout-confirmed" && !isConfirmedLogout(operation)') <
    eventHandler.indexOf('setToken(null);'));
  const retry = p.split('const retryLogout = useCallback')[1]
    .split("  // A peer's logout-pending signal")[0];
  assert.ok(retry.includes('recordConfirmedLogout(operation)'));
  assert.ok(retry.includes('if (activeOperation() &&'));
  assert.ok(retry.includes('sessionStorage.getItem(PENDING_OPERATION) === operation'));
  assert.ok(p.includes('const MAX_CONFIRMED_HISTORY = 128'));
  assert.ok(p.includes('confirmedHistory().includes(operation)'));
});
