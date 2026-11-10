const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const filename = path.resolve(__dirname, '../src/context/AuthProvider.tsx');
const js = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
    jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
}).outputText;

function harness(initialIdentity) {
  const storage = new Map([['access_token', 'signed-access'], ['refresh_token', 'signed-refresh']]);
  const sessionStorage = {
    getItem: key => storage.has(key) ? storage.get(key) : null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: key => storage.delete(key),
  };
  const localStorage = { removeItem() {} };
  const authContextProvider = {};
  let identity = initialIdentity;
  let value;
  let cursor = 0;
  let effects = [];
  const states = [];
  const revoked = [];
  let generation = 0;
  const react = {
    useState(initial) {
      const pos = cursor++;
      if (!(pos in states)) states[pos] = typeof initial === 'function' ? initial() : initial;
      return [states[pos], next => { states[pos] = next; }];
    },
    useEffect(effect) { effects.push(effect); },
  };
  const apiClient = { defaults: { headers: { common: {} } } };
  const queryClient = { invalidateQueries() {}, clear() {} };
  const mod = { exports: {} };
  vm.runInNewContext(js, {
    module: mod,
    exports: mod.exports,
    sessionStorage,
    localStorage,
    require: name => {
      if (name === 'react') return { ...react, __esModule: true, default: react };
      if (name === 'react/jsx-runtime') return {
        jsx: (type, props) => { if (type === authContextProvider) value = props.value; return null; },
        jsxs: (type, props) => { if (type === authContextProvider) value = props.value; return null; },
      };
      if (name === '@tanstack/react-query') return {
        useQuery: options => options.queryKey[0] === 'currentUserProfile'
          ? identity : { data: [], isLoading: false },
        useQueryClient: () => queryClient,
      };
      if (name === '../services/api') return { __esModule: true, default: apiClient };
      if (name === '../services/classService') return { __esModule: true, default: {} };
      if (name === './AuthContext') return { AuthContext: { Provider: authContextProvider } };
      if (name === '../utils/accessTokenClaims') return {
        inspectLocalAccessClaims: () => ({ sub: 'synthetic-subject', token_use: 'access' }),
      };
      if (name === '../utils/verifiedAuthIdentityQuery') return {
        verifiedAuthIdentityQuery: (_token, generation) => ({
          queryKey: ['currentUserProfile', 'signed-access', generation],
        }),
      };
      if (name === '../utils/authSessionGeneration') return {
        getAuthSessionGeneration: () => generation,
        advanceAuthSessionGeneration: () => ++generation,
      };
      if (name === '../utils/revokeServerSession') return {
        revokeServerSession: async (...args) => { revoked.push(args); },
      };
      if (name === '../utils/identityFailurePolicy') return {
        isRecoverableIdentityFailure: error => error?.isAxiosError === true &&
          (error.response?.status === undefined || error.response.status >= 500 ||
           error.response.status === 429),
      };
      throw new Error('Unexpected import ' + name);
    },
  }, { filename });
  return {
    render() {
      cursor = 0;
      effects = [];
      mod.exports.AuthProvider({ children: null });
      for (const effect of effects) effect();
      return value;
    },
    replaceIdentity(next) { identity = next; },
    storage,
    revoked,
  };
}

const failed = status => ({
  isError: true, isSuccess: false, isPending: false, isFetching: false,
  data: { id: 'synthetic-subject', email: 'old@example.invalid', role: 'admin', active: true },
  error: { isAxiosError: true, response: status === undefined ? undefined : { status } },
  refetch: async () => ({}),
});
const verified = {
  isError: false, isSuccess: true, isPending: false, isFetching: false,
  data: { id: 'synthetic-subject', email: 'new@example.invalid', role: 'client', active: true },
  error: null, refetch: async () => ({}),
};

test('503 /auth/me suspends auth and preserves revocation credentials until recovery', async () => {
  const h = harness(failed(503));
  let state = h.render();
  assert.equal(state.isAuthenticated, false);
  assert.equal(state.currentUser, null, 'a failed refetch must not trust stale admin data');
  assert.equal(state.identityRecoveryPending, true);
  assert.equal(h.storage.get('access_token'), 'signed-access');
  assert.equal(h.storage.get('refresh_token'), 'signed-refresh');
  await state.retryIdentity();
  h.replaceIdentity(verified);
  state = h.render();
  assert.equal(state.isAuthenticated, true);
  assert.equal(state.currentUser.role, 'client');
  assert.equal(h.storage.get('refresh_token'), 'signed-refresh');
});

test('pending identity outage still permits explicit server logout of retained session', async () => {
  const h = harness(failed(undefined));
  const state = h.render();
  await state.logout();
  assert.equal(h.revoked.length, 1);
  assert.equal(h.revoked[0][0], 'signed-access');
  assert.equal(h.revoked[0][1], 'signed-refresh');
  assert.equal(h.storage.has('access_token'), false);
  assert.equal(h.storage.has('refresh_token'), false);
});

test('unexpected refetch rejection does not revoke a recoverable session', async () => {
  const error = failed(503);
  error.refetch = async () => { throw new Error('transport-internal-detail'); };
  const h = harness(error);
  const state = h.render();
  await assert.rejects(state.retryIdentity(), /transport-internal-detail/);
  const after = h.render();
  assert.equal(after.identityRecoveryPending, true);
  assert.equal(after.isAuthenticated, false);
  assert.equal(h.storage.get('access_token'), 'signed-access');
  assert.equal(h.storage.get('refresh_token'), 'signed-refresh');
});

test('401 /auth/me invalidates credentials and cannot authorize cached profile', () => {
  const h = harness(failed(401));
  let state = h.render();
  assert.equal(state.isAuthenticated, false);
  assert.equal(state.identityRecoveryPending, false);
  assert.equal(h.storage.has('access_token'), false);
  assert.equal(h.storage.has('refresh_token'), false);
  state = h.render();
  assert.equal(state.token, null);
  assert.equal(state.currentUser, null);
});
