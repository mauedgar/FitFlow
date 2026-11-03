'use strict';
// Real mounted Chrome browser, synthetic loopback API, zero new npm dependencies.
// No external accounts, database, Redis, server credentials, or browser downloads.
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');

const frontend = path.resolve(__dirname, '../..');
const webOrigin = 'http://127.0.0.1:4173';
const apiOrigin = 'http://127.0.0.1:4180';
const driverOrigin = 'http://127.0.0.1:9515';
const uuid = 'f00d0000-0000-4000-a000-000000000011';
const refreshCredential = 'synthetic-refresh-browser-only';
const name = 'Clase sintética E2E';
const requests = [];
let tokenSerial = 0;
let logoutCalls = 0;
let refreshCalls = 0;
let ackCalls = 0;
let ackDroppedResponses = 0;
let issuedPairs = 0;
let firstAckCredential = null;
const subprocesses = [];
const tmpProfile = fs.mkdtempSync(path.join(os.tmpdir(), 'fitflow-e2e-chrome-'));
let session = null;

function jwt(seconds = 3600) {
  const encode = value => Buffer.from(JSON.stringify(value)).toString('base64url');
  return [
    encode({ alg: 'HS256', typ: 'JWT' }),
    encode({
      sub: uuid, role: 'admin', token_use: 'access',
      exp: Math.floor(Date.now() / 1000) + seconds,
      jti: 'synthetic-' + ++tokenSerial,
    }),
    'synthetic-not-a-signature',
  ].join('.');
}
const user = { id: uuid, email: 'e2e-admin@example.com', role: 'admin', active: true };
const publicClass = {
  id: 'f00d0000-0000-4000-a000-000000000042',
  name, description: 'Contenido sintético sin metadatos operativos',
  activity_type: 'group_class', difficulty: 'beginner',
  duration_minutes: 45, default_capacity: 12,
};

function mockApi(req, res) {
  const url = new URL(req.url || '/', apiOrigin);
  const route = url.pathname;
  const method = req.method || 'GET';
  requests.push(method + ' ' + route);
  res.setHeader('Access-Control-Allow-Origin', webOrigin);
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type, X-FitFlow-Refresh-Ack');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Cache-Control', 'no-store');
  const send = (code, data) => {
    res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(data));
  };
  if (method === 'OPTIONS') return send(204, {});
  if (method === 'GET' && route === '/api/v1/gym-classes/public') {
    return send(200, [publicClass]);
  }
  if (method === 'GET' && route === '/api/v1/gym-classes/') {
    return send(403, { detail: 'Operational endpoint not public' });
  }
  let body = '';
  req.on('data', chunk => {
    body += chunk;
    if (body.length > 8192) req.destroy();
  });
  req.on('end', () => {
    const bearer = req.headers.authorization || '';
    if (method === 'POST' && route === '/api/v1/auth/token') {
      assert.equal(req.headers['x-fitflow-refresh-ack'], 'v1', 'Mounted SPA negotiates pending refresh');
      const form = new URLSearchParams(body);
      if (form.get('username') !== user.email ||
          form.get('password') !== 'synthetic-e2e-only') {
        return send(401, { detail: 'Invalid synthetic login' });
      }
      issuedPairs++;
      return send(200, {
        access_token: jwt(), refresh_token: refreshCredential, token_type: 'bearer',
      });
    }
    if (method === 'POST' && route === '/api/v1/auth/ack') {
      const payload = JSON.parse(body || '{}');
      if (!bearer.startsWith('Bearer ') || payload.refresh_token !== refreshCredential) {
        return send(403, { detail: 'Bad synthetic acknowledgement' });
      }
      const credential = bearer + '|' + payload.refresh_token;
      if (firstAckCredential === null) firstAckCredential = credential;
      assert.equal(credential, firstAckCredential, 'ACK retries must preserve exactly the first pair');
      ackCalls++;
      if (ackCalls === 1) {
        // The server has accepted the ACK, but the HTTP 204 reply is lost.
        // A real browser network failure must trigger a retry, not a re-login.
        ackDroppedResponses++;
        res.destroy();
        return;
      }
      return send(204, {});
    }
    if (method === 'GET' && route === '/api/v1/auth/me') {
      return bearer.startsWith('Bearer ') ? send(200, user) :
        send(401, { detail: 'Unauthenticated' });
    }
    if (method === 'POST' && route === '/api/v1/auth/refresh') {
      const payload = JSON.parse(body || '{}');
      if (payload.refresh_token !== refreshCredential) {
        return send(401, { detail: 'Unknown synthetic refresh' });
      }
      refreshCalls++;
      return send(200, { access_token: jwt(), token_type: 'bearer' });
    }
    if (method === 'POST' && route === '/api/v1/auth/logout') {
      if (!bearer.startsWith('Bearer ') ||
          JSON.parse(body || '{}').refresh_token !== refreshCredential) {
        return send(403, { detail: 'Bad synthetic logout' });
      }
      logoutCalls++;
      return send(200, { detail: 'Synthetic credential revoked' });
    }
    return send(404, { detail: 'No such synthetic endpoint' });
  });
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
async function until(fn, label, timeout = 25000) {
  const expiry = Date.now() + timeout;
  let last;
  while (Date.now() < expiry) {
    try {
      const result = await fn();
      if (result) return result;
    } catch (e) { last = e; }
    await sleep(170);
  }
  throw new Error('Timeout: ' + label + (last ? ' (' + last.message + ')' : ''));
}
async function webdriver(method, endpoint, data) {
  const reply = await fetch(driverOrigin + endpoint, {
    method, headers: { 'Content-Type': 'application/json' },
    body: data === undefined ? undefined : JSON.stringify(data),
    signal: AbortSignal.timeout(12000),
  });
  const payload = await reply.json();
  if (!reply.ok || payload.value?.error) {
    throw new Error('ChromeDriver ' + method + ' ' + endpoint + ': ' +
      JSON.stringify(payload.value).slice(0,800));
  }
  return payload.value;
}
async function evaluate(code) {
  return webdriver('POST', '/session/' + session + '/execute/sync', {
    script: 'return (' + code + ');', args: [],
  });
}
async function navigate(route) {
  await webdriver('POST', '/session/' + session + '/url', { url: webOrigin + route });
}
async function element(selector) {
  const found = await webdriver('POST', '/session/' + session + '/element', {
    using: 'css selector', value: selector,
  });
  return found['element-6066-11e4-a52e-4f735466cecf'];
}
async function input(selector, text) {
  const id = await element(selector);
  await webdriver('POST', '/session/' + session + '/element/' + id + '/value', { text });
}
async function click(selector) {
  const id = await element(selector);
  await webdriver('POST', '/session/' + session + '/element/' + id + '/click', {});
}
async function documentText(fragment) {
  return evaluate("document.body?.innerText?.includes(" + JSON.stringify(fragment) + ") || false");
}
async function browserTest() {
  const mock = http.createServer(mockApi);
  await new Promise((resolve, reject) => {
    mock.once('error', reject);
    mock.listen(4180, '127.0.0.1', resolve);
  });
  subprocesses.push({ kill: () => mock.close() });
  const vite = spawn(process.execPath, [
    path.join(frontend, 'node_modules/vite/bin/vite.js'),
    'preview', '--host', '127.0.0.1', '--port', '4173', '--strictPort',
  ], { cwd: frontend, stdio: 'pipe' });
  subprocesses.push(vite);
  let viteLog = '';
  vite.stderr.on('data', d => { viteLog += d.toString().slice(0,800); });
  await until(async () => {
    const response = await fetch(webOrigin + '/classes', { signal: AbortSignal.timeout(750) });
    return response.ok;
  }, 'vite preview (last stderr: ' + viteLog.slice(-400) + ')');

  const candidates = [
    process.env.CHROMEWEBDRIVER && path.join(process.env.CHROMEWEBDRIVER, 'chromedriver'),
    '/usr/local/bin/chromedriver', '/usr/bin/chromedriver',
  ].filter(Boolean);
  const binary = candidates.find(candidate => fs.existsSync(candidate));
  assert.ok(binary, 'No preinstalled ChromeDriver found; do not install automatically');
  const driver = spawn(binary, ['--port=9515', '--allowed-ips=127.0.0.1'], {
    stdio: 'pipe',
  });
  subprocesses.push(driver);
  await until(async () => {
    const response = await fetch(driverOrigin + '/status', { signal: AbortSignal.timeout(750) });
    return response.ok;
  }, 'preinstalled ChromeDriver');
  const created = await webdriver('POST', '/session', {
    capabilities: {
      alwaysMatch: {
        browserName: 'chrome',
        'goog:chromeOptions': {
          args: [
            '--headless=new', '--no-sandbox', '--disable-dev-shm-usage',
            '--no-first-run', '--window-size=1280,900', '--disable-gpu',
            '--user-data-dir=' + tmpProfile,
          ],
        },
      },
    },
  });
  session = created.sessionId;
  const browser = created.capabilities?.browserVersion || 'unknown';

  // Scenario 1: React mounted in Chrome, anonymous catalogue through safe API.
  await navigate('/classes');
  await until(() => documentText(name), 'public catalogue card');
  assert.ok(requests.includes('GET /api/v1/gym-classes/public'));
  assert.ok(!requests.includes('GET /api/v1/gym-classes/'));
  console.log('E2E_BROWSER_PUBLIC_CATALOG_PASS');

  // Scenario 2: protected role route cannot render anonymously.
  await navigate('/admin');
  await until(() => evaluate("location.pathname === '/login'"), 'anonymous redirect to /login');
  console.log('E2E_BROWSER_UNAUTH_ADMIN_REDIRECT_PASS');

  // Scenario 3: real form events -> API token -> /auth/me -> React admin route.
  await until(() => evaluate("!!document.querySelector('input[type=email]')"), 'login form');
  await input('input[type=email]', user.email);
  await input('input[type=password]', 'synthetic-e2e-only');
  await click('button[type=submit]');
  await until(async () => {
    const location = await evaluate('location.pathname');
    return location === '/admin' && await documentText('Bienvenido al Panel de Administración');
  }, 'authenticated admin navigation');
  assert.equal(await evaluate("sessionStorage.getItem('fitflow_refresh_token')"), refreshCredential);
  assert.equal(ackCalls, 2, 'Lost successful ACK reply must cause one same-pair retry');
  assert.equal(ackDroppedResponses, 1);
  assert.equal(issuedPairs, 1, 'Retry must not issue a second credential pair');
  console.log('E2E_BROWSER_ACK_LOST_RESPONSE_RETRY_PASS');
  console.log('E2E_BROWSER_LOGIN_AND_ROLE_ROUTE_PASS');

  // Scenario 4: real browser reload with expiring access performs one refresh.
  const refreshBefore = refreshCalls;
  const oldAccess = jwt(3);
  await evaluate('sessionStorage.setItem("fitflow_access_token",' + JSON.stringify(oldAccess) + ')');
  await navigate('/admin');
  await until(async () => {
    const location = await evaluate('location.pathname');
    return location === '/admin' && await documentText('Bienvenido al Panel de Administración');
  }, 'rehydrated admin route');
  assert.ok(refreshCalls > refreshBefore, 'Expected mounted SPA HTTP refresh');
  assert.notEqual(await evaluate("sessionStorage.getItem('fitflow_access_token')"), oldAccess);
  console.log('E2E_BROWSER_REFRESH_REHYDRATE_PASS');

  // Scenario 5: mounted Chakra profile menu triggers server revoke and local clear.
  await click('[aria-label="Menú de perfil"]');
  await until(() => documentText('Cerrar Sesión'), 'profile logout menu');
  const logoutItem = await element('[role=menuitem][data-value=logout]');
  await webdriver('POST', '/session/' + session + '/element/' + logoutItem + '/click', {});
  await until(() => evaluate("location.pathname === '/login'"), 'logout navigates to login');
  assert.equal(await evaluate("sessionStorage.getItem('fitflow_refresh_token')"), null);
  assert.equal(ackCalls, 2);
  assert.equal(logoutCalls, 1);
  await navigate('/admin');
  await until(() => evaluate("location.pathname === '/login'"), 'post-logout redirect');
  console.log('E2E_BROWSER_LOGOUT_AND_REVOCATION_PASS');

  const shot = await webdriver('GET', '/session/' + session + '/screenshot');
  const digest = crypto.createHash('sha256').update(Buffer.from(shot, 'base64')).digest('hex');
  console.log('E2E_BROWSER_RECEIPT ' + JSON.stringify({
    browser, mountedReact: true, apiSynthetic: true, stagingDeployed: false,
    publicRequests: requests.filter(x => x === 'GET /api/v1/gym-classes/public').length,
    authMeRequests: requests.filter(x => x === 'GET /api/v1/auth/me').length,
    refreshCalls, logoutCalls, ackCalls, ackDroppedResponses, issuedPairs,
    screenshotSha256: digest, checks: 6, noExternalCredentials: true, noNewDependencies: true,
  }));
}
(async () => {
  try {
    await browserTest();
  } catch (error) {
    console.error('E2E_BROWSER_FAIL', error?.stack || String(error));
    process.exitCode = 1;
  } finally {
    if (session) {
      try { await webdriver('DELETE', '/session/' + session); } catch {}
    }
    for (const child of subprocesses.reverse()) {
      try { child.kill('SIGTERM'); } catch {}
    }
    fs.rmSync(tmpProfile, { recursive: true, force: true });
  }
})();
