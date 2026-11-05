/* Synthetic mounted AuthProvider effect runner: recovery uses real provider code.
 * No DOM/staging and no network. Timeouts and HTTP are deterministic mocks.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'src', 'context', 'AuthProvider.tsx'), 'utf8',
);
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    jsx: ts.JsxEmit.React,
    esModuleInterop: true,
  },
}).outputText;

async function settle() {
  for (let i = 0; i < 20; i++) await Promise.resolve();
}

function setup({ failures = 1, failureStatus = null, holdFirstGet = false, holdLogin = false, delayForcedRefresh = false } = {}) {
  let failuresRemaining = failures;
  const expires = Math.floor(Date.now() / 1000) + 600;
  const access = JSON.stringify({
    sub: 'user-id', role: 'client', token_use: 'access', exp: expires,
  });
  const refresh = 'synthetic-refresh';
  const access2 = JSON.stringify({
    sub: 'user-two', role: 'teacher', token_use: 'access', exp: expires,
  });
  const refresh2 = 'synthetic-refresh-user-two';
  const entries = new Map([
    ['fitflow_access_token', access],
    ['fitflow_refresh_token', refresh],
  ]);
  const storage = {
    getItem: key => entries.get(key) ?? null,
    setItem: (key, value) => entries.set(key, value),
    removeItem: key => entries.delete(key),
  };
  const listeners = new Map();
  const window = {
    addEventListener(name, callback) {
      if (!listeners.has(name)) listeners.set(name, new Set());
      listeners.get(name).add(callback);
    },
    removeEventListener(name, callback) { listeners.get(name)?.delete(callback); },
    dispatchEvent(event) {
      for (const callback of listeners.get(event.type) ?? []) callback(event);
    },
  };
  const timers = new Map();
  let timerID = 0;
  const setTimeout = (callback, delay) => {
    const id = ++timerID;
    timers.set(id, { callback, delay });
    return id;
  };
  const clearTimeout = id => timers.delete(id);
  let abortedGets = 0;
  let logoutCalls = 0;
  let resolveHeldLogin;
  let rejectForcedRefresh;
  const fakeReact = {
    useState(initial) {
      const id = hookCursor++;
      if (!state.has(id)) state.set(id, initial);
      return [state.get(id), value => state.set(id,
        typeof value === 'function' ? value(state.get(id)) : value)];
    },
    useRef(initial) {
      const id = hookCursor++;
      if (!refs.has(id)) refs.set(id, { current: initial });
      return refs.get(id);
    },
    useEffect(callback, deps) {
      const id = hookCursor++;
      const prior = effectRecords.get(id);
      const changed = !prior || !deps || !prior.deps || deps.length !== prior.deps.length ||
        deps.some((value, index) => value !== prior.deps[index]);
      if (changed) pendingEffects.push({ id, callback, deps });
    },
    createElement(_component, props) {
      providerValue = props.value;
      return null;
    },
  };
  const state = new Map();
  const refs = new Map();
  const effectRecords = new Map();
  const pendingEffects = [];
  let hookCursor = 0;
  let providerValue;
  let getCalls = 0;
  const user = { id: 'user-id', role: 'client', active: true };
  const secondUser = { id: 'user-two', role: 'teacher', active: true };
  const apiClient = {
    defaults: { headers: { common: {} } },
    async get(url, config) {
      assert.equal(url, '/auth/me');
      getCalls++;
      const principal = config?.headers?.Authorization === 'Bearer ' + access2
        ? secondUser : user;
      if (holdFirstGet && getCalls === 1) {
        assert.ok(config?.signal);
        return await new Promise((_resolve, reject) => {
          config.signal.addEventListener('abort', () => {
            abortedGets++;
            const error = new Error('aborted');
            error.isAxiosError = true;
            reject(error);
          }, { once: true });
        });
      }
      if (holdLogin && getCalls >= 2) {
        return await new Promise(resolve => { resolveHeldLogin = () => resolve({ data: principal }); });
      }
      if (failuresRemaining-- > 0) {
        const error = new Error('transient network failure');
        error.isAxiosError = true;
        if (failureStatus !== null) error.response = { status: failureStatus };
        throw error;
      }
      return { data: principal };
    },
    async post(url) {
      assert.equal(url, '/auth/logout');
      logoutCalls++;
      return { status: 204 };
    },
  };
  const modules = {
    react: { __esModule: true, default: fakeReact, ...fakeReact },
    '@tanstack/react-query': {
      useQuery: () => ({ data: undefined, isLoading: false }),
      useQueryClient: () => ({ clear() {}, invalidateQueries() {} }),
    },
    'jwt-decode': { jwtDecode: JSON.parse },
    '../services/api': {
      __esModule: true, default: apiClient,
      ensureFreshAccess: async force => {
        if (force && delayForcedRefresh) {
          return await new Promise((_resolve, reject) => { rejectForcedRefresh = reject; });
        }
        return storage.getItem('fitflow_refresh_token') === refresh2 ? access2 : access;
      },
      invalidateAuthEpoch() {},
    },
    axios: { __esModule: true, default: { isAxiosError: e => !!e?.isAxiosError } },
    '../services/classService': {
      __esModule: true, default: { getMyBookings: async () => [] },
    },
    './AuthContext': { AuthContext: { Provider: 'Provider' } },
  };
  const mod = { exports: {} };
  vm.runInNewContext(compiled, {
    module: mod, exports: mod.exports,
    require(name) {
      if (!(name in modules)) throw Error('unexpected import ' + name);
      return modules[name];
    },
    sessionStorage: storage,
    localStorage: { removeItem() {} },
    window,
    AbortController,
    setTimeout,
    clearTimeout,
    Date,
    Event: class { constructor(type) { this.type = type; } },
    console,
  }, { filename: 'AuthProvider.tsx' });
  const render = () => {
    hookCursor = 0;
    const output = mod.exports.AuthProvider({ children: null });
    for (const e of pendingEffects.splice(0)) {
      effectRecords.get(e.id)?.cleanup?.();
      const cleanup = e.callback();
      effectRecords.set(e.id, { deps: e.deps, cleanup });
    }
    return output;
  };
  render();
  return {
    access, refresh, access2, refresh2, storage, timers, state,
    authHeader: () => apiClient.defaults.headers.common.Authorization,
    render,
    cleanup: () => {
      for (const record of effectRecords.values()) record.cleanup?.();
      effectRecords.clear();
    },
    getCalls: () => getCalls,
    logoutCalls: () => logoutCalls,
    abortedGets: () => abortedGets,
    resolveHeldLogin: () => {
      if (!resolveHeldLogin) throw Error('no pending login');
      resolveHeldLogin();
    },
    rejectForcedRefresh: error => {
      if (!rejectForcedRefresh) throw Error('no pending refresh');
      rejectForcedRefresh(error);
    },
    emitOnline: () => window.dispatchEvent({ type: 'online' }),
    getValue: () => providerValue,
    fireNext() {
      const next = timers.entries().next().value;
      if (!next) throw Error('expected retry timer');
      timers.delete(next[0]);
      next[1].callback();
    },
    savedTimer() {
      const next = timers.entries().next().value;
      return next?.[1].callback;
    },
  };
}

test('transient transport failure retains credentials and auto-verifies on bounded timer', async () => {
  const h = setup();
  await settle();
  assert.equal(h.getCalls(), 1);
  assert.equal(h.state.get(0), null);
  assert.equal(h.storage.getItem('fitflow_refresh_token'), h.refresh);
  assert.equal(h.timers.size, 1);
  const scheduledDelay = [...h.timers.values()][0].delay;
  assert.ok(scheduledDelay >= 1000 && scheduledDelay <= 30000);
  h.fireNext();
  await settle();
  assert.equal(h.getCalls(), 2);
  assert.equal(h.state.get(0), h.access);
  assert.equal(h.state.get(1).id, 'user-id');
  assert.equal(h.timers.size, 0);
  h.cleanup();
});

test('logout fences an already scheduled recovery callback', async () => {
  const h = setup();
  await settle();
  const stale = h.savedTimer();
  assert.equal(typeof stale, 'function');
  h.render();
  const confirmed = await h.getValue().logout();
  assert.equal(confirmed, true);
  assert.equal(h.storage.getItem('fitflow_refresh_token'), null);
  assert.equal(h.timers.size, 0);
  stale();
  await settle();
  assert.equal(h.getCalls(), 1);
  assert.equal(h.state.get(0), null);
  h.cleanup();
});


test('online event supersedes pending backoff and reschedules after another outage', async () => {
  const h = setup({ failures: 2 });
  await settle();
  assert.equal(h.getCalls(), 1);
  assert.equal(h.timers.size, 1);
  const stale = h.savedTimer();
  h.emitOnline();
  await settle();
  assert.equal(h.getCalls(), 2);
  assert.equal(h.timers.size, 1);
  stale();
  await settle();
  assert.equal(h.getCalls(), 2);
  h.fireNext();
  await settle();
  assert.equal(h.getCalls(), 3);
  assert.equal(h.state.get(0), h.access);
  h.cleanup();
});


test('HTTP 503 and 429 preserve unverified session and recover with bounded backoff', async () => {
  for (const failureStatus of [503, 429]) {
    const h = setup({ failures: 7, failureStatus });
    await settle();
    for (let i = 0; i < 7; i++) {
      assert.equal(h.storage.getItem('fitflow_refresh_token'), h.refresh);
      assert.equal(h.timers.size, 1);
      const delay = [...h.timers.values()][0].delay;
      assert.ok(delay >= 1000 && delay <= 30000, delay);
      if (i === 6) assert.equal(delay, 30000);
      h.fireNext();
      await settle();
    }
    assert.equal(h.getCalls(), 8);
    assert.equal(h.state.get(0), h.access);
    h.cleanup();
  }
});

test('provider unmount cancels pending backoff and forbids recovery work', async () => {
  const h = setup({ failures: 3 });
  await settle();
  const old = h.savedTimer();
  h.cleanup();
  assert.equal(h.timers.size, 0);
  old();
  await settle();
  assert.equal(h.getCalls(), 1);
});


test('new login cancels stale recovery timer and starts a new attempt', async () => {
  const h = setup({ failures: 2 });
  await settle();
  const stale = h.savedTimer();
  h.render();
  await assert.rejects(h.getValue().login({
    access_token: h.access, refresh_token: h.refresh,
  }));
  assert.equal(h.getCalls(), 2);
  assert.equal(h.timers.size, 1);
  stale();
  await settle();
  assert.equal(h.timers.size, 1);
  h.fireNext();
  await settle();
  assert.equal(h.getCalls(), 3);
  assert.equal(h.state.get(0), h.access);
  h.cleanup();
});

test('new login HTTP 429/503 keeps only new unverified credentials and recovers without revoke', async () => {
  for (const failureStatus of [429, 503]) {
    const h = setup({ failures: 2, failureStatus });
    await settle(); // initial rehydration fails and schedules a timer
    h.render();
    await assert.rejects(h.getValue().login({
      access_token: h.access2, refresh_token: h.refresh2,
    }));
    assert.equal(h.getCalls(), 2);
    assert.equal(h.logoutCalls(), 0);
    assert.equal(h.storage.getItem('fitflow_access_token'), h.access2);
    assert.equal(h.storage.getItem('fitflow_refresh_token'), h.refresh2);
    assert.equal(h.state.get(0), null);
    assert.equal(h.state.get(1), null);
    assert.equal(h.state.get(2), null);
    assert.equal(h.authHeader(), undefined);
    assert.equal(h.timers.size, 1);
    h.fireNext();
    await settle();
    assert.equal(h.getCalls(), 3);
    assert.equal(h.state.get(0), h.access2);
    assert.equal(h.state.get(1).id, 'user-two');
    assert.equal(h.state.get(2), 'teacher');
    assert.equal(h.logoutCalls(), 0);
    h.cleanup();
  }
});

test('initial HTTP 401 hydration clears invalid pair and exits loading without retry', async () => {
  const h = setup({ failures: 1, failureStatus: 401 });
  await settle();
  h.render();
  assert.ok(h.getValue(), 'provider must mount after rejecting stored credentials');
  assert.equal(h.getValue().isLoadingAuth, false);
  assert.equal(h.getValue().isAuthenticated, false);
  assert.equal(h.storage.getItem('fitflow_access_token'), null);
  assert.equal(h.storage.getItem('fitflow_refresh_token'), null);
  assert.equal(h.timers.size, 0);
  assert.equal(h.logoutCalls(), 0);
  h.cleanup();
});

test('new login HTTP 401 is not recoverable and attempts refresh revocation', async () => {
  const h = setup({ failures: 2, failureStatus: 401 });
  await settle();
  h.render();
  await assert.rejects(h.getValue().login({
    access_token: h.access2, refresh_token: h.refresh2,
  }));
  assert.equal(h.logoutCalls(), 1);
  assert.equal(h.storage.getItem('fitflow_access_token'), null);
  assert.equal(h.storage.getItem('fitflow_refresh_token'), null);
  assert.equal(h.state.get(1), null);
  assert.equal(h.timers.size, 0);
  h.cleanup();
});

test('online supersession aborts pending HTTP identity verification', async () => {
  const h = setup({ failures: 0, holdFirstGet: true });
  await settle();
  assert.equal(h.getCalls(), 1);
  h.emitOnline();
  await settle();
  assert.equal(h.abortedGets(), 1);
  assert.equal(h.getCalls(), 2);
  assert.equal(h.state.get(0), h.access);
  h.cleanup();
});

test('unmount fences late successful login response', async () => {
  const h = setup({ failures: 0, holdLogin: true });
  await settle();
  h.render();
  const previousToken = h.state.get(0);
  const pending = h.getValue().login({ access_token: h.access, refresh_token: h.refresh });
  await settle();
  h.cleanup();
  h.resolveHeldLogin();
  await assert.rejects(pending, /Login superseded/);
  assert.equal(h.state.get(0), null);
  assert.equal(h.state.get(1), null);
  assert.equal(h.state.get(2), null);
  assert.equal(h.storage.getItem('fitflow_refresh_token'), null);
  assert.equal(h.authHeader(), undefined);
});

test('stale scheduled refresh rejection cannot clear a newly logged-in session', async () => {
  const h = setup({ failures: 0, delayForcedRefresh: true });
  await settle();
  h.render();
  assert.equal(h.state.get(0), h.access);
  assert.equal(h.timers.size, 1);
  h.fireNext();
  await settle();
  h.render();
  const oldEpochValue = h.state.get(0);
  assert.equal(await h.getValue().logout(), true);
  await h.getValue().login({ access_token: h.access2, refresh_token: h.refresh2 });
  h.render();
  const error = new Error('old token refused');
  error.isAxiosError = true;
  error.response = { status: 401 };
  h.rejectForcedRefresh(error);
  await settle();
  assert.notEqual(h.state.get(0), oldEpochValue);
  assert.equal(h.state.get(0), h.access2);
  assert.equal(h.state.get(1).id, 'user-two');
  assert.equal(h.state.get(2), 'teacher');
  assert.equal(h.storage.getItem('fitflow_refresh_token'), h.refresh2);
  assert.equal(h.authHeader(), 'Bearer ' + h.access2);
  h.cleanup();
});


test('account switch hides previous principal while new login is pending', async () => {
  const h = setup({ failures: 0, holdLogin: true });
  await settle();
  h.render();
  assert.equal(h.state.get(1).id, 'user-id');
  assert.equal(h.storage.getItem('fitflow_refresh_token'), h.refresh);
  const pending = h.getValue().login({ access_token: h.access2, refresh_token: h.refresh2 });
  await settle();
  assert.equal(h.state.get(0), null);
  assert.equal(h.state.get(1), null);
  assert.equal(h.state.get(2), null);
  assert.equal(h.storage.getItem('fitflow_refresh_token'), null);
  h.resolveHeldLogin();
  await pending;
  h.render();
  assert.equal(h.state.get(0), h.access2);
  assert.equal(h.state.get(1).id, 'user-two');
  assert.equal(h.state.get(2), 'teacher');
  assert.equal(h.storage.getItem('fitflow_refresh_token'), h.refresh2);
  assert.equal(h.authHeader(), 'Bearer ' + h.access2);
  h.cleanup();
});
