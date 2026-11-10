const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const filename = path.resolve(__dirname, '../src/pages/LoginPage.tsx');
const source = fs.readFileSync(filename, 'utf8');
const result = ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.CommonJS,
    jsx: ts.JsxEmit.ReactJSX,
    esModuleInterop: true,
  },
  reportDiagnostics: true,
});
assert.deepEqual(result.diagnostics.filter(d => d.category === ts.DiagnosticCategory.Error), []);

function harness() {
  const states = [];
  let cursor = 0;
  let effects = [];
  let mutation;
  let formSubmit;
  let retryClick;
  let closeClick;
  const ui = {};
  const effectSlots = [];
  const requests = [];
  const routes = [];
  const toasts = [];
  const auth = {
    generation: 0,
    identityRecoveryPending: false,
    retryIdentity: async () => {},
    logout: async () => {},
    token: null,
    currentUser: null,
    isAuthenticated: false,
    isLoadingAuth: false,
    login(access, refresh) {
      assert.ok(access && refresh);
      auth.token = access;
      auth.generation += 1;
      auth.isLoadingAuth = true;
    },
  };
  const react = {
    useState(initial) {
      const slot = cursor++;
      if (!(slot in states)) states[slot] = typeof initial === 'function' ? initial() : initial;
      return [states[slot], value => { states[slot] = value; }];
    },
    useEffect(effect, deps) { effects.push({ slot: cursor++, effect, deps }); },
    useRef(initial) {
      const slot = cursor++;
      if (!(slot in states)) states[slot] = { current: initial };
      return states[slot];
    },
  };
  const load = name => {
    if (name === 'react') return { ...react, default: react };
    if (name === 'react/jsx-runtime') {
      const jsx = (type, props) => {
        if (type === 'form') formSubmit = props.onSubmit;
        if (props?.children === 'Reintentar verificación') retryClick = props.onClick;
        if (props?.children === 'Cerrar sesión pendiente') closeClick = props.onClick;
        if (props?.children === 'Ingresar') ui.loginDisabled = props.disabled;
        if (props?.children === 'Reintentar verificación') ui.retryDisabled = props.disabled;
        if (props?.role === 'alert') ui.pendingAlert = true;
        return null;
      };
      return { jsx, jsxs: jsx };
    }
    if (name === '../components/ui/toaster-store') return { toaster: { create: message => toasts.push(message) } };
    if (name === '@chakra-ui/react') return { Field: { Root: () => null, Label: () => null } };
    if (name === 'react-router-dom') return {
      useNavigate: () => (to, options) => routes.push({ to, options }),
    };
    if (name === '@tanstack/react-query') return {
      useMutation: options => {
        mutation = options;
        return { isPending: false, mutate(vars) { requests.push(vars); } };
      },
    };
    if (name === '../context/useAuth') return { useAuth: () => auth };
    if (name === '../services/classService') return { __esModule: true, default: {} };
    if (name === '../types') return { UserRole: { ADMIN: 'admin' } };
    if (name === '../utils/authSessionGeneration') return { getAuthSessionGeneration: () => auth.generation };
    if (name === '../utils/verifiedRoleDestination') return { verifiedRoleDestination: role => role === 'admin' ? '/admin' : '/home' };
    if (name === 'axios') return {};
    throw new Error('Unexpected dependency ' + name);
  };
  const mod = { exports: {} };
  vm.runInNewContext(result.outputText, {
    module: mod, exports: mod.exports, require: load,
  }, { filename });
  const render = () => {
    cursor = 0;
    effects = [];
    ui.pendingAlert = false;
    mod.exports.default();
    for (const { slot, effect, deps } of effects) {
      const previous = effectSlots[slot];
      if (previous && deps && previous.deps && deps.length === previous.deps.length &&
          deps.every((value, index) => Object.is(value, previous.deps[index]))) continue;
      previous?.cleanup?.();
      effectSlots[slot] = { deps, cleanup: effect() };
    }
  };
  return {
    render, auth, toasts, routes, requests, ui,
    unmount: () => { for (const slot of effectSlots) slot?.cleanup?.(); },
    awaitingIdentity: () => states[2],
    submit: () => { assert.ok(formSubmit); formSubmit({ preventDefault() {} }); },
    retry: () => { assert.ok(retryClick); retryClick(); },
    close: () => { assert.ok(closeClick); closeClick(); },
    onSuccess: (data, vars = requests.at(-1)) => mutation.onSuccess(data, vars),
  };
}

test('token login waits for the backend profile, not the JWT role', () => {
  const h = harness();
  h.render();
  h.submit(); h.onSuccess({ access_token: 'jwt-claims-admin-untrusted', refresh_token: 'refresh' });
  assert.equal(h.routes.length, 0);
  h.render();
  assert.equal(h.routes.length, 0, 'Pending /auth/me cannot navigate');
  h.auth.isLoadingAuth = false;
  h.auth.isAuthenticated = true;
  h.auth.currentUser = { id: 'validated', active: true, role: 'client' };
  h.render();
  assert.equal(h.routes.length, 1);
  assert.equal(h.routes[0].to, '/home', 'Verified backend role overrides local JWT claims');
  assert.equal(h.routes[0].options.replace, true);
  h.render();
  assert.equal(h.routes.length, 1, 'Redirect cannot be duplicated after completion');
});

test('only verified admin identity navigates into the admin route', () => {
  const h = harness();
  h.render();
  h.submit(); h.onSuccess({ access_token: 'jwt', refresh_token: 'refresh' });
  h.render();
  h.auth.isLoadingAuth = false;
  h.auth.isAuthenticated = true;
  h.auth.currentUser = { id: 'validated', active: true, role: 'admin' };
  h.render();
  assert.equal(h.routes.length, 1);
  assert.equal(h.routes[0].to, '/admin');
});

test('failed profile validation leaves the login page visible and reports failure', () => {
  const h = harness();
  h.render();
  h.submit(); h.onSuccess({ access_token: 'jwt', refresh_token: 'refresh' });
  h.render();
  h.auth.isLoadingAuth = false;
  h.auth.token = null;
  h.render();
  assert.equal(h.routes.length, 0);
  assert.equal(h.toasts.length, 1);
  assert.equal(h.toasts[0].type, 'error');
});

test('login source contains no local-JWT role-based navigation', () => {
  assert.doesNotMatch(source, /jwtDecode|inspectLocalAccessClaims|TokenPayload/);
  assert.match(source, /isAuthenticated && currentUser/);
  assert.match(source, /!awaitingVerifiedIdentity \|\| isLoadingAuth/);
});

test('rapid re-login remains possible while earlier identity request is pending', () => {
  // Signed ADMIN E2E intentionally begins a second login while the earlier
  // /auth/me request is suspended, to prove stale response isolation.
  assert.equal(source.includes('if (awaitingVerifiedIdentity) return;'), false);
  assert.equal(source.includes('disabled={loginMutation.isPending || awaitingVerifiedIdentity}'), false);
  assert.equal(source.includes('loading={loginMutation.isPending || awaitingVerifiedIdentity}'), false);
  assert.equal(source.split('disabled={loginMutation.isPending || pendingSession}').length - 1, 3);
  assert.equal(source.split('loading={loginMutation.isPending}').length - 1, 1);
  const h = harness();
  h.render();
  h.submit(); h.onSuccess({ access_token: 'old', refresh_token: 'refresh-1' });
  h.render();
  assert.equal(h.auth.isLoadingAuth, true);
  h.submit(); h.onSuccess({ access_token: 'new', refresh_token: 'refresh-2' });
  assert.equal(h.auth.token, 'new', 'new login supersedes pending token');
  assert.equal(h.routes.length, 0, 'unverified token does not decide route');
});

test('out-of-order login responses cannot overwrite newest verified generation', () => {
  const h = harness();
  h.render();
  h.submit();
  const first = h.requests[0];
  h.submit();
  const second = h.requests[1];
  assert.ok(first.attemptId < second.attemptId);
  h.onSuccess({ access_token: 'latest-signed', refresh_token: 'latest-refresh' }, second);
  assert.equal(h.auth.token, 'latest-signed');
  h.onSuccess({ access_token: 'stale-signed', refresh_token: 'stale-refresh' }, first);
  assert.equal(h.auth.token, 'latest-signed');
  assert.equal(h.routes.length, 0);
});

test('an external auth epoch change prevents an old pending login from authenticating', () => {
  const h = harness();
  h.render();
  h.submit();
  const pending = h.requests[0];
  h.auth.generation += 1; // logout or a separate login wins the session
  h.onSuccess({ access_token: 'stale', refresh_token: 'stale-refresh' }, pending);
  assert.equal(h.auth.token, null);
  assert.equal(h.routes.length, 0);
});

test('recoverable identity outage blocks credential replacement before explicit logout', () => {
  const h = harness();
  h.auth.identityRecoveryPending = true;
  h.render();
  h.submit();
  assert.equal(h.requests.length, 0, 'pending refresh credential cannot be overwritten');
});

test('retry waits for the new identity response before navigating', async () => {
  const h = harness();
  let resolveRetry;
  h.auth.identityRecoveryPending = true;
  h.auth.token = 'pending';
  h.auth.retryIdentity = () => new Promise(resolve => { resolveRetry = resolve; });
  h.render();
  h.retry();
  h.render();
  assert.equal(h.routes.length, 0);
  assert.equal(h.toasts.length, 0, 'old 503 must not consume the retry');
  h.auth.identityRecoveryPending = false;
  h.auth.currentUser = { id: 'verified', role: 'client', active: true };
  h.auth.isAuthenticated = true;
  resolveRetry();
  await new Promise(resolve => setImmediate(resolve));
  h.render();
  assert.equal(h.routes.length, 1);
  assert.equal(h.routes[0].to, '/home');
});

const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
};
const settleRetry = () => new Promise(resolve => setImmediate(resolve));

function pendingRetry(withLogout = false) {
  const h = harness();
  h.auth.token = 'same-access';
  h.auth.identityRecoveryPending = true;
  if (withLogout) h.auth.logout = async () => {
    h.auth.generation += 1;
    h.auth.token = null;
    h.auth.identityRecoveryPending = false;
  };
  const request = deferred();
  h.auth.retryIdentity = () => request.promise;
  h.render();
  h.retry();
  return { h, request };
}

test('settled retry after logout cannot set awaiting state or navigate as a new user', async () => {
  const { h, request } = pendingRetry();
  h.auth.generation += 1;
  h.auth.token = null;
  h.auth.identityRecoveryPending = false;
  h.render();
  request.resolve();
  await settleRetry();
  assert.equal(h.awaitingIdentity(), false);
  h.auth.token = 'different-access';
  h.auth.generation += 1;
  h.auth.isAuthenticated = true;
  h.auth.currentUser = { role: 'admin' };
  h.render();
  assert.equal(h.routes.length, 0);
});

test('a pending retry keeps logout visible and prevents credential replacement', async () => {
  const { h, request } = pendingRetry(true);
  h.render();
  assert.equal(h.ui.pendingAlert, true);
  assert.equal(h.ui.loginDisabled, true);
  assert.equal(h.ui.retryDisabled, true);
  h.submit();
  assert.equal(h.requests.length, 0);
  h.close();
  h.render();
  assert.equal(h.ui.pendingAlert, false);
  assert.equal(h.ui.loginDisabled, false);
  request.resolve();
  await settleRetry();
  assert.equal(h.awaitingIdentity(), false);
});

test('same token from a new auth generation cannot inherit an older retry', async () => {
  const { h, request } = pendingRetry();
  h.auth.generation += 1;
  h.auth.identityRecoveryPending = false;
  h.auth.isAuthenticated = true;
  h.auth.currentUser = { role: 'admin' };
  h.render();
  request.resolve();
  await settleRetry();
  h.render();
  assert.equal(h.awaitingIdentity(), false);
  assert.equal(h.routes.length, 0);
});

test('a retry that settles after unmount cannot update state or emit a toast', async () => {
  const { h, request } = pendingRetry();
  h.unmount();
  request.resolve();
  await settleRetry();
  assert.equal(h.awaitingIdentity(), false);
  assert.equal(h.toasts.length, 0);
  assert.equal(h.routes.length, 0);
});

test('a rejection after logout or unmount stays silent and cannot resurrect identity', async () => {
  for (const unmount of [false, true]) {
    const { h, request } = pendingRetry();
    if (unmount) h.unmount();
    else {
      h.auth.generation += 1;
      h.auth.token = null;
      h.auth.identityRecoveryPending = false;
      h.render();
    }
    request.reject(new Error('obsolete-transport-detail'));
    await settleRetry();
    assert.equal(h.awaitingIdentity(), false);
    assert.equal(h.toasts.length, 0);
    assert.equal(h.routes.length, 0);
  }
});

test('unexpected retry rejection is handled without leaking details or changing credentials', async () => {
  const { h, request } = pendingRetry();
  request.reject(new Error('sensitive-internal-detail'));
  await settleRetry();
  h.render();
  assert.equal(h.auth.token, 'same-access');
  assert.equal(h.auth.identityRecoveryPending, true);
  assert.equal(h.awaitingIdentity(), false);
  assert.equal(h.routes.length, 0);
  assert.equal(h.toasts.length, 1);
  assert.doesNotMatch(JSON.stringify(h.toasts), /sensitive-internal-detail/);
  h.auth.identityRecoveryPending = false; // unexpected throw without TanStack error state
  h.render();
  assert.equal(h.ui.pendingAlert, true);
  assert.equal(h.ui.loginDisabled, true);
  assert.equal(h.ui.retryDisabled, false);
});

test('only the latest of interleaved retries may resume verified navigation', async () => {
  const h = harness();
  const first = deferred();
  const second = deferred();
  h.auth.token = 'same-access';
  h.auth.identityRecoveryPending = true;
  let calls = 0;
  h.auth.retryIdentity = () => ++calls === 1 ? first.promise : second.promise;
  h.render();
  h.retry();
  h.retry();
  first.resolve();
  await settleRetry();
  assert.equal(h.awaitingIdentity(), false, 'obsolete retry cannot start navigation');
  second.resolve();
  await settleRetry();
  assert.equal(h.awaitingIdentity(), true);
  h.render();
  assert.equal(h.routes.length, 0, '503 result still cannot navigate');
});
