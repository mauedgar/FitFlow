/* Frontend auth renewal behavioral tests with deterministic simulated browser APIs.
 * This runs transpiled TypeScript, not a deployed browser E2E.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'src', 'services', 'api.ts'), 'utf8')
  .replace('import.meta.env.VITE_API_BASE_URL', 'undefined');
const code = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    esModuleInterop: true,
  },
}).outputText;

function setup() {
  const entries = new Map();
  const storage = {
    getItem: (k) => entries.get(k) ?? null,
    setItem: (k, v) => entries.set(k, v),
    removeItem: (k) => entries.delete(k),
  };
  const now = Math.floor(Date.now() / 1000);
  const oldAccess = JSON.stringify({
    sub: 'synthetic-user', token_use: 'access', role: 'client', exp: now - 5,
  });
  const validOldAccess = JSON.stringify({
    sub: 'synthetic-user', token_use: 'access', role: 'client', exp: now + 300,
  });
  const newAccess = JSON.stringify({
    sub: 'synthetic-user', token_use: 'access', role: 'client', exp: now + 1800,
  });
  entries.set('fitflow_access_token', oldAccess);
  entries.set('fitflow_refresh_token', 'synthetic-refresh');
  const events = [];
  const client = {
    defaults: { headers: { common: {} } },
    interceptors: {
      request: { use(fn) { this.fn = fn; } },
      response: { use(ok, fail) { this.ok = ok; this.fail = fail; } },
    },
    request: async (config) => ({ status: 200, config }),
  };
  let refreshCalls = 0;
  const axios = {
    create: () => client,
    isAxiosError: (err) => Boolean(err?.isAxiosError),
    async post(url, body) {
      assert.match(url, /\/auth\/refresh$/);
      assert.equal(body.refresh_token, 'synthetic-refresh');
      refreshCalls += 1;
      await Promise.resolve();
      return { data: { access_token: newAccess } };
    },
  };
  const module = { exports: {} };
  vm.runInNewContext(code, {
    module,
    exports: module.exports,
    require(name) {
      if (name === 'axios') return axios;
      if (name === 'jwt-decode') return { jwtDecode: JSON.parse };
      if (name.endsWith('registrationErrors')) return { registrationErrorMessage: () => 'error' };
      throw Error('Unexpected mocked import: ' + name);
    },
    sessionStorage: storage,
    window: { dispatchEvent: e => events.push(e.type) },
    Event: class { constructor(type) { this.type = type; } },
    URLSearchParams,
    Date,
    console,
    Promise,
  }, { filename: 'src/services/api.ts' });
  return { api: module.exports, client, storage, events, newAccess, oldAccess,
    validOldAccess,
    get refreshCalls() { return refreshCalls; } };
}

function headers() {
  const values = new Map();
  return {
    get: name => values.get(name),
    set: (name, value) => values.set(name, value),
  };
}

test('IR006 concurrent expired access requests perform exactly one refresh', async () => {
  const state = setup();
  const results = await Promise.all(
    Array.from({ length: 12 }, () => state.api.ensureFreshAccess()),
  );
  assert.ok(results.every(x => x === state.newAccess));
  assert.equal(state.refreshCalls, 1);
  assert.equal(state.storage.getItem('fitflow_access_token'), state.newAccess);
  assert.deepEqual(state.events, ['fitflow:access-renewed']);
});

test('IR006 request interceptor attaches renewed Bearer and skips refresh endpoint', async () => {
  const state = setup();
  const config = { url: '/bookings/me', headers: headers() };
  const updated = await state.client.interceptors.request.fn(config);
  assert.equal(updated.headers.get('Authorization'), 'Bearer ' + state.newAccess);
  assert.equal(state.refreshCalls, 1);
  await state.client.interceptors.request.fn({ url: '/auth/refresh', headers: headers() });
  assert.equal(state.refreshCalls, 1);
});

test('IR006 login explicit principal token is not replaced by old session token', async () => {
  const state = setup();
  const config = { url: '/auth/me', headers: headers() };
  config.headers.set('Authorization', 'Bearer new-login-token');
  await state.client.interceptors.request.fn(config);
  assert.equal(config.headers.get('Authorization'), 'Bearer new-login-token');
  assert.equal(state.refreshCalls, 0);
});

test('IR007 protected 401 has a bounded one-shot retry', async () => {
  const state = setup();
  state.storage.setItem('fitflow_access_token', state.validOldAccess);
  const cfg = { url: '/bookings/me', headers: headers() };
  await state.client.interceptors.request.fn(cfg);
  assert.equal(cfg.headers.get('Authorization'), 'Bearer ' + state.validOldAccess);
  const error = { isAxiosError: true, response: { status: 401 }, config: cfg };
  const result = await state.client.interceptors.response.fail(error);
  assert.equal(result.status, 200);
  assert.equal(state.refreshCalls, 1);
  assert.equal(cfg.headers.get('Authorization'), 'Bearer ' + state.newAccess);
  assert.equal(cfg._fitflowRetried, true);
  await assert.rejects(state.client.interceptors.response.fail(error));
  assert.equal(state.refreshCalls, 1);
});

test('IR007 staggered concurrent 401s reuse one new access generation', async () => {
  const state = setup();
  state.storage.setItem('fitflow_access_token', state.validOldAccess);
  const first = { url: '/bookings/me', headers: headers() };
  const later = { url: '/classes', headers: headers() };
  await state.client.interceptors.request.fn(first);
  await state.client.interceptors.request.fn(later);
  assert.equal(first.headers.get('Authorization'), 'Bearer ' + state.validOldAccess);
  assert.equal(later.headers.get('Authorization'), 'Bearer ' + state.validOldAccess);
  const error = cfg => ({ isAxiosError: true, response: { status: 401 }, config: cfg });
  await state.client.interceptors.response.fail(error(first));
  assert.equal(state.refreshCalls, 1);
  await state.client.interceptors.response.fail(error(later));
  assert.equal(state.refreshCalls, 1);
  assert.equal(later.headers.get('Authorization'), 'Bearer ' + state.newAccess);
});

test('IR007 prior session cannot retry after refresh identity changes', async () => {
  const state = setup();
  state.storage.setItem('fitflow_access_token', state.validOldAccess);
  const stale = { url: '/classes', headers: headers() };
  await state.client.interceptors.request.fn(stale);
  state.storage.removeItem('fitflow_refresh_token');
  await assert.rejects(state.client.interceptors.response.fail({
    isAxiosError: true, response: { status: 401 }, config: stale,
  }));
  assert.equal(state.refreshCalls, 0);
});

test('IR007 provider refuses stale rehydrate after logout by session epoch', () => {
  const source = fs.readFileSync(
    path.join(__dirname, '..', 'src', 'context', 'AuthProvider.tsx'), 'utf8',
  );
  assert.match(source, /const epoch = \+\+sessionEpoch\.current/);
  assert.match(source, /epoch !== sessionEpoch\.current/);
  assert.match(source, /sessionStorage\.getItem\(REFRESH_KEY\) !== refresh/);
  assert.match(source, /sessionEpoch\.current\+\+/);
});


test('IR011 catalog uses safe public projection instead of operational metadata', () => {
  const service = fs.readFileSync(
    path.join(__dirname, '..', 'src', 'services', 'classService.ts'), 'utf8',
  );
  assert.match(service, /apiClient\.get<Omit<GymClass, 'class_schedules'>\[\]>\('\/gym-classes\/public'\)/);
  assert.match(service, /class_schedules: \[\]/);
  assert.doesNotMatch(service, /apiClient\.get<GymClass\[\]>\('\/gym-classes\/'\)/);
});
