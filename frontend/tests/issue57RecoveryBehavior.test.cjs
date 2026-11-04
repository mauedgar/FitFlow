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

function setup() {
  const expires = Math.floor(Date.now() / 1000) + 600;
  const access = JSON.stringify({
    sub: 'user-id', role: 'client', token_use: 'access', exp: expires,
  });
  const refresh = 'synthetic-refresh';
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
    useEffect(callback) { if (firstRender) effects.push(callback); },
    createElement(_component, props) {
      providerValue = props.value;
      return null;
    },
  };
  const state = new Map();
  const refs = new Map();
  const effects = [];
  let hookCursor = 0;
  let firstRender = true;
  let providerValue;
  let getCalls = 0;
  const user = { id: 'user-id', role: 'client', active: true };
  const apiClient = {
    defaults: { headers: { common: {} } },
    async get(url) {
      assert.equal(url, '/auth/me');
      getCalls++;
      if (getCalls === 1) {
        const error = new Error('transient network failure');
        error.isAxiosError = true;
        throw error;
      }
      return { data: user };
    },
    async post(url) {
      assert.equal(url, '/auth/logout');
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
      ensureFreshAccess: async () => access,
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
    setTimeout,
    clearTimeout,
    Date,
    Event: class { constructor(type) { this.type = type; } },
    console,
  }, { filename: 'AuthProvider.tsx' });
  const render = () => {
    hookCursor = 0;
    const output = mod.exports.AuthProvider({ children: null });
    firstRender = false;
    return output;
  };
  render();
  const cleanups = effects.map(effect => effect()).filter(Boolean);
  return {
    access, refresh, storage, timers, state,
    render, cleanup: () => cleanups.forEach(callback => callback()),
    getCalls: () => getCalls,
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
