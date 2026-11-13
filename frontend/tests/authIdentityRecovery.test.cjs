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

function harness(initialIdentity, options = {}) {
  const storage = new Map([['access_token', 'signed-access'], ['refresh_token', 'signed-refresh']]);
  if (options.pendingRemoteLogout) storage.set('fitflow_logout_remote_unconfirmed', '1');
  if (options.initialPendingLedger !== undefined) {
    storage.set('fitflow_logout_pending_attempts', options.initialPendingLedger);
  }
  const maybeThrow = (op, key) => {
    if (options.storageFailures?.[op]?.includes(key)) {
      throw new Error('synthetic storage ' + op + ' denied');
    }
  };
  const sessionStorage = {
    getItem: key => { maybeThrow('read', key); return storage.has(key) ? storage.get(key) : null; },
    setItem: (key, value) => { maybeThrow('write', key); return storage.set(key, value); },
    removeItem: key => { maybeThrow('remove', key); return storage.delete(key); },
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
        revokeServerSession: async (...args) => {
          revoked.push(args);
          if (options.revocation) return options.revocation(...args);
          if (options.revocationError) throw options.revocationError;
        },
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

test('verified backend teacher role is trainer, but legacy trainer alias is not', () => {
  const teacherProfile = { ...verified, data: { ...verified.data, role: 'teacher' } };
  const teacherState = harness(teacherProfile).render();
  assert.equal(teacherState.isAuthenticated, true);
  assert.equal(teacherState.isTrainer, true);
  assert.equal(teacherState.userRole, 'teacher');

  const legacyProfile = { ...verified, data: { ...verified.data, role: 'trainer' } };
  const legacyState = harness(legacyProfile).render();
  assert.equal(legacyState.isTrainer, false);
  assert.equal(legacyState.userRole, 'trainer');
  assert.equal(legacyState.isAdmin, false);
  assert.equal(legacyState.isClient, false);

  const unknownProfile = { ...verified, data: { ...verified.data, role: 'unknown' } };
  const unknownState = harness(unknownProfile).render();
  assert.equal(unknownState.isTrainer, false);
  assert.equal(unknownState.isAdmin, false);
  assert.equal(unknownState.isClient, false);
});

test('unconfirmed remote logout leaves a non-secret warning across reload', async () => {
  const h = harness(verified, { revocationError: new Error('synthetic Redis outage') });
  const before = h.render();
  await assert.rejects(before.logout(), /synthetic Redis outage/);
  assert.equal(h.storage.has('access_token'), false);
  assert.equal(h.storage.has('refresh_token'), false);
  assert.equal(h.storage.get('fitflow_logout_remote_unconfirmed'), '1');
  assert.equal(h.render().remoteLogoutUnconfirmed, true);

  const reload = harness(verified, { pendingRemoteLogout: true });
  const warning = reload.render();
  assert.equal(warning.remoteLogoutUnconfirmed, true);
  warning.dismissRemoteLogoutWarning();
  assert.equal(reload.storage.get('fitflow_logout_remote_unconfirmed'), '1',
    'Dismissing visible warning cannot erase durable remote uncertainty');
  assert.equal(reload.render().remoteLogoutUnconfirmed, false);
});

test('confirmed 204 on a single new attempt clears its warning and JWTs', async () => {
  const h = harness(verified);
  const before = h.render();
  await before.logout();
  assert.equal(h.storage.has('access_token'), false);
  assert.equal(h.storage.has('refresh_token'), false);
  assert.equal(h.storage.has('fitflow_logout_remote_unconfirmed'), false);
  assert.equal(h.storage.has('fitflow_logout_pending_attempts'), false);
  assert.equal(h.render().remoteLogoutUnconfirmed, false);
});

test('older unconfirmed session survives a later confirmed logout', async () => {
  const h = harness(verified, { pendingRemoteLogout: true });
  const before = h.render();
  assert.equal(before.remoteLogoutUnconfirmed, true);
  await before.logout();
  assert.equal(h.storage.get('fitflow_logout_remote_unconfirmed'), '1');
  const pending = JSON.parse(h.storage.get('fitflow_logout_pending_attempts'));
  assert.deepEqual(Array.from(pending), ['legacy-unconfirmed']);
  assert.equal(h.render().remoteLogoutUnconfirmed, true);
});

test('login page shows durable unconfirmed warning without false remote ACK', () => {
  const login = fs.readFileSync(path.resolve(__dirname, '../src/pages/LoginPage.tsx'), 'utf8');
  assert.match(login, /remoteLogoutUnconfirmed &&/);
  assert.match(login, /no se confirmó su revocación en el servidor/);
  assert.match(login, /Ocultar aviso \(no revoca la sesión\)/);
});

test('stale confirmed logout A cannot clear concurrently failed logout B', async () => {
  const pending = [];
  const h = harness(verified, {
    revocation: (..._args) => new Promise((resolve, reject) => pending.push({ resolve, reject })),
  });
  const a = h.render().logout();
  h.render().login('signed-access-b', 'signed-refresh-b');
  const b = h.render().logout();
  assert.equal(pending.length, 2);
  assert.equal(JSON.parse(h.storage.get('fitflow_logout_pending_attempts')).length, 2);
  pending[0].resolve();
  await a;
  assert.equal(h.storage.get('fitflow_logout_remote_unconfirmed'), '1');
  assert.equal(JSON.parse(h.storage.get('fitflow_logout_pending_attempts')).length, 1);
  pending[1].reject(new Error('synthetic remote failure B'));
  await assert.rejects(b, /synthetic remote failure B/);
  assert.equal(h.storage.get('fitflow_logout_remote_unconfirmed'), '1');
  assert.equal(h.render().remoteLogoutUnconfirmed, true);
});

test('two concurrent confirmed 204 results clear warning only after both ACKs', async () => {
  const pending = [];
  const h = harness(verified, {
    revocation: () => new Promise((resolve, reject) => pending.push({ resolve, reject })),
  });
  const a = h.render().logout();
  h.render().login('signed-access-b', 'signed-refresh-b');
  const b = h.render().logout();
  assert.equal(pending.length, 2);
  pending[1].resolve();
  await b;
  assert.equal(h.storage.get('fitflow_logout_remote_unconfirmed'), '1');
  pending[0].resolve();
  await a;
  assert.equal(h.storage.has('fitflow_logout_remote_unconfirmed'), false);
  assert.equal(h.storage.has('fitflow_logout_pending_attempts'), false);
});

test('submitting login discards password from React state after mutation dispatch', () => {
  const login = fs.readFileSync(path.resolve(__dirname, '../src/pages/LoginPage.tsx'), 'utf8');
  assert.match(login, /loginMutation\.mutate\(\{/);
  assert.match(login, /setPassword\(''\);/);
});

test('unconfirmed ledger alone restores warning when legacy flag is missing', () => {
  const h = harness(verified, { initialPendingLedger: '["prior-lost-ACK"]' });
  assert.equal(h.render().remoteLogoutUnconfirmed, true);
  assert.equal(h.storage.has('fitflow_logout_remote_unconfirmed'), false);
});

test('corrupt pending JSON remains unconfirmed and cannot be converted to ACK', async () => {
  const h = harness(verified, { initialPendingLedger: '{bad-json' });
  assert.equal(h.render().remoteLogoutUnconfirmed, true);
  await h.render().logout();
  assert.equal(h.storage.get('fitflow_logout_remote_unconfirmed'), '1');
  assert.deepEqual(Array.from(JSON.parse(h.storage.get('fitflow_logout_pending_attempts'))),
    ['unrecognized-pending']);
});

test('quota failure on pending storage preserves in-memory warning and still attempts revocation', async () => {
  const h = harness(verified, {
    storageFailures: { write: ['fitflow_logout_pending_attempts'] },
    revocationError: new Error('synthetic offline revocation'),
  });
  await assert.rejects(h.render().logout(), /synthetic offline revocation/);
  assert.equal(h.revoked.length, 1, 'Storage fault must not prevent bounded remote attempt');
  assert.equal(h.render().remoteLogoutUnconfirmed, true);
  assert.equal(h.storage.has('access_token'), false);
  assert.equal(h.storage.has('refresh_token'), false);
});

test('read-denied pending metadata cannot falsely confirm later logout', async () => {
  const h = harness(verified, {
    storageFailures: { read: ['fitflow_logout_pending_attempts'] },
  });
  assert.equal(h.render().remoteLogoutUnconfirmed, true);
  await h.render().logout();
  assert.equal(h.render().remoteLogoutUnconfirmed, true);
  assert.equal(h.revoked.length, 1);
});

test('many failed attempts compact to capped non-secret ledger with sticky uncertainty', async () => {
  const h = harness(verified, { revocationError: new Error('synthetic offline') });
  for (let i = 0; i < 52; i += 1) {
    if (i > 0) h.render().login('access-' + i, 'refresh-' + i);
    await assert.rejects(h.render().logout(), /synthetic offline/);
    const ledger = JSON.parse(h.storage.get('fitflow_logout_pending_attempts'));
    assert.ok(ledger.length <= 24, 'Bounded ledger must not grow with failures');
    assert.equal(h.storage.get('fitflow_logout_remote_unconfirmed'), '1');
  }
  const ledger = JSON.parse(h.storage.get('fitflow_logout_pending_attempts'));
  assert.ok(ledger.includes('unrecognized-pending'),
    'Overflow must preserve a permanent unknown marker, never silently acknowledge lost IDs');
  assert.equal(ledger.length, 24);
});

