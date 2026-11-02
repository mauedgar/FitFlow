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

test('IR006 retried 401 has a bounded one-shot retry', async () => {
  const state = setup();
  const cfg = { url: '/bookings/me', headers: headers() };
  cfg.headers.set('Authorization', 'Bearer ' + state.oldAccess);
  const error = { isAxiosError: true, response: { status: 401 }, config: cfg };
  const result = await state.client.interceptors.response.fail(error);
  assert.equal(result.status, 200);
  assert.equal(state.refreshCalls, 1);
  assert.equal(cfg.headers.get('Authorization'), 'Bearer ' + state.newAccess);
  assert.equal(cfg._fitflowRetried, true);
  await assert.rejects(state.client.interceptors.response.fail(error));
  assert.equal(state.refreshCalls, 1);
});
