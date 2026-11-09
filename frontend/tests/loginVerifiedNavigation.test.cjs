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
  const routes = [];
  const toasts = [];
  const auth = {
    token: null,
    currentUser: null,
    isAuthenticated: false,
    isLoadingAuth: false,
    login(access, refresh) {
      assert.ok(access && refresh);
      auth.token = access;
      auth.isLoadingAuth = true;
    },
  };
  const react = {
    useState(initial) {
      const slot = cursor++;
      if (!(slot in states)) states[slot] = typeof initial === 'function' ? initial() : initial;
      return [states[slot], value => { states[slot] = value; }];
    },
    useEffect(effect) { effects.push(effect); },
  };
  const load = name => {
    if (name === 'react') return { ...react, default: react };
    if (name === 'react/jsx-runtime') return { jsx: () => null, jsxs: () => null };
    if (name === '../components/ui/toaster-store') return { toaster: { create: message => toasts.push(message) } };
    if (name === '@chakra-ui/react') return { Field: { Root: () => null, Label: () => null } };
    if (name === 'react-router-dom') return {
      useNavigate: () => (to, options) => routes.push({ to, options }),
    };
    if (name === '@tanstack/react-query') return {
      useMutation: options => {
        mutation = options;
        return { isPending: false, mutate() {} };
      },
    };
    if (name === '../context/useAuth') return { useAuth: () => auth };
    if (name === '../services/classService') return { __esModule: true, default: {} };
    if (name === '../types') return { UserRole: { ADMIN: 'admin' } };
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
    mod.exports.default();
    for (const effect of effects) effect();
  };
  return {
    render, auth, toasts, routes,
    onSuccess: data => mutation.onSuccess(data),
  };
}

test('token login waits for the backend profile, not the JWT role', () => {
  const h = harness();
  h.render();
  h.onSuccess({ access_token: 'jwt-claims-admin-untrusted', refresh_token: 'refresh' });
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
  h.onSuccess({ access_token: 'jwt', refresh_token: 'refresh' });
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
  h.onSuccess({ access_token: 'jwt', refresh_token: 'refresh' });
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
  assert.equal(source.split('disabled={loginMutation.isPending}').length - 1, 3);
  assert.equal(source.split('loading={loginMutation.isPending}').length - 1, 1);
  const h = harness();
  h.render();
  h.onSuccess({ access_token: 'old', refresh_token: 'refresh-1' });
  h.render();
  assert.equal(h.auth.isLoadingAuth, true);
  h.onSuccess({ access_token: 'new', refresh_token: 'refresh-2' });
  assert.equal(h.auth.token, 'new', 'new login supersedes pending token');
  assert.equal(h.routes.length, 0, 'unverified token does not decide route');
});
