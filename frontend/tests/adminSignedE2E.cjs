/* Real signed backend + disposable Postgres/Redis browser qualification. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium } = require('playwright');

const WEB = 'http://127.0.0.1:5173';
const API = 'http://127.0.0.1:8000/api/v1';
const email = process.env.FITFLOW_E2E_ADMIN_EMAIL;
const clientEmail = process.env.FITFLOW_E2E_CLIENT_EMAIL;
const password = process.env.FITFLOW_E2E_PASSWORD;

async function login(page, username) {
  await page.goto(WEB + '/login');
  await page.getByLabel('Email').fill(username);
  await page.getByLabel('Contraseña').fill(password);
  await page.getByRole('button', { name: 'Ingresar' }).click();
}


const within = async (promise, label, timeoutMs = 10000) => {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((_resolve, reject) => {
        timer = setTimeout(() => reject(new Error('Timed out waiting for ' + label)), timeoutMs);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
};

async function runtimeSessionState(page) {
  // Vite serves exactly the same modules consumed by the mounted Product app.
  // This is test-only introspection; no production debug endpoint is added.
  return page.evaluate(async () => {
    const epochs = await import('/src/utils/authSessionGeneration.ts');
    const axiosModule = await import('/src/services/api.ts');
    return {
      generation: epochs.getAuthSessionGeneration(),
      activeInterceptors: axiosModule.default.interceptors.response.handlers.filter(Boolean).length,
    };
  });
}

async function loginUsingSignedToken(page, token) {
  // Replays the same *real backend-signed* token to exercise identical-token
  // re-login. Other API requests continue against the real disposable backend.
  const routePattern = '**/api/v1/auth/token';
  await page.route(routePattern, (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ access_token: token, token_type: 'bearer', refresh_token: 'synthetic-e2e-only' }),
  }));
  try {
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Contraseña').fill(password);
    await page.getByRole('button', { name: 'Ingresar' }).click();
    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), token);
  } finally {
    await page.unroute(routePattern);
  }
}

async function verifyRapidReLoginAndStale401(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  let authMeRequests = 0;
  let releaseHeldRequest;
  try {
    page.on('request', (request) => {
      if (new URL(request.url()).pathname === '/api/v1/auth/me') authMeRequests += 1;
    });
    await login(page, email);
    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const signedToken = await page.evaluate(() => localStorage.getItem('access_token'));
    assert.ok(signedToken, 'Live browser session must retain signed token');
    const firstState = await runtimeSessionState(page);
    assert.equal(firstState.activeInterceptors, 1, 'Exactly one Axios response interceptor on initial mount');
    assert.ok(firstState.generation > 0, 'Login must synchronously create an auth generation');
    assert.ok(authMeRequests >= 1 && authMeRequests <= 2, 'Shared identity query should be deduplicated');
    const requestsBeforeNavigation = authMeRequests;

    for (const section of ['Profesores', 'Clases', 'Clientes']) {
      await page.locator('aside').getByRole('link', { name: section, exact: true }).click();
      await page.getByRole('heading', { name: section, exact: true }).waitFor();
    }
    assert.equal(authMeRequests, requestsBeforeNavigation,
      'ADMIN navigation must reuse verified /auth/me result without redundant requests');
    assert.equal((await runtimeSessionState(page)).activeInterceptors, 1,
      'Changing ADMIN routes must not accumulate Axios interceptors');

    // Full browser rehydration is distinct from SPA login. It must validate the
    // retained signed token again without installing duplicate interceptors.
    await page.reload();
    await page.getByRole('heading', { name: 'Clientes', exact: true }).waitFor();
    assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), signedToken);
    assert.ok(authMeRequests > requestsBeforeNavigation &&
      authMeRequests <= requestsBeforeNavigation + 2, 'Rehydration rechecks one verified identity');
    const rehydratedState = await runtimeSessionState(page);
    assert.equal(rehydratedState.activeInterceptors, 1,
      'Rehydration must have exactly one active response interceptor');
    await page.locator('aside').getByRole('link', { name: 'Dashboard', exact: true }).click();
    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();

    // Deliberately start a no-AbortSignal Axios request with a captured older
    // interceptor; hold its synthetic 401 until AFTER logout + same-JWT login.
    let seenResolve;
    let settledResolve;
    const seen = new Promise((resolve) => { seenResolve = resolve; });
    const settled = new Promise((resolve) => { settledResolve = resolve; });
    let heldOnce = false;
    let releaseResolve;
    const release = new Promise((resolve) => { releaseResolve = resolve; });
    releaseHeldRequest = releaseResolve;
    await page.route('**/api/v1/clients/**', async (route) => {
      if (heldOnce) {
        await route.continue();
        return;
      }
      heldOnce = true;
      seenResolve();
      await release;
      try {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: '{"detail":"synthetic stale session"}',
        });
      } catch {
        // Browser may already have cancelled the old request; no JWT is logged.
      } finally {
        settledResolve();
      }
    });
    await page.evaluate(async () => {
      const api = (await import('/src/services/api.ts')).default;
      window.__fitflowOldRequest = api.get('/clients/?skip=0&limit=100')
        .then(() => 'success', () => 'rejected');
    });
    await within(seen, 'captured pre-logout Axios request');
    await page.getByRole('button', { name: 'Menú de perfil' }).click();
    await page.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await page.waitForURL('**/login');
    await page.waitForFunction(async () => {
      const api = (await import('/src/services/api.ts')).default;
      return api.interceptors.response.handlers.filter(Boolean).length === 0;
    });
    const loggedOutGeneration = (await runtimeSessionState(page)).generation;
    assert.ok(loggedOutGeneration > rehydratedState.generation,
      'Logout must advance the epoch within the rehydrated browser module');
    await loginUsingSignedToken(page, signedToken);
    const newGeneration = (await runtimeSessionState(page)).generation;
    assert.ok(newGeneration > loggedOutGeneration,
      'Same-token re-login must have a distinct generation');
    assert.equal((await runtimeSessionState(page)).activeInterceptors, 1,
      'New ADMIN session must install exactly one interceptor');
    releaseResolve();
    await within(settled, 'late 401 delivery attempt');
    await page.evaluate(() => window.__fitflowOldRequest);
    assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), signedToken,
      'Old 401 must not log out a newer same-token generation');
    assert.equal((await runtimeSessionState(page)).generation, newGeneration,
      'Late old-generation 401 must not change session generation');
    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    console.log('ADMIN_SESSION_EPOCH_AND_STALE_401_PASS');
  } finally {
    if (releaseHeldRequest) releaseHeldRequest();
    await context.close();
  }
}

async function verifyDelayedIdentityAcrossSameTokenReLogin(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  let releaseHeldIdentity;
  try {
    let firstProfileResolve;
    let settledResolve;
    const firstProfileSeen = new Promise((resolve) => { firstProfileResolve = resolve; });
    const settled = new Promise((resolve) => { settledResolve = resolve; });
    let releaseResolve;
    const release = new Promise((resolve) => { releaseResolve = resolve; });
    releaseHeldIdentity = releaseResolve;
    let identityCount = 0;
    await page.route('**/api/v1/auth/me', async (route) => {
      identityCount += 1;
      if (identityCount > 1) {
        await route.continue();
        return;
      }
      firstProfileResolve();
      await release;
      try {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: '{"detail":"synthetic old identity rejection"}',
        });
      } catch {
        // The old authenticated query may already have been cancelled.
      } finally {
        settledResolve();
      }
    });
    await login(page, email);
    await within(firstProfileSeen, 'old /auth/me request in pending ADMIN guard');
    const firstSignedToken = await page.evaluate(() => localStorage.getItem('access_token'));
    assert.ok(firstSignedToken, 'Signed JWT must be present while first profile is pending');
    await page.evaluate(() => {
      history.pushState({}, '', '/login');
      dispatchEvent(new PopStateEvent('popstate'));
    });
    await page.getByRole('heading', { name: 'Iniciar Sesión' }).waitFor();
    await loginUsingSignedToken(page, firstSignedToken);
    const newState = await runtimeSessionState(page);
    assert.ok(newState.generation >= 2, 'Second same-token login must advance generation');
    assert.equal(newState.activeInterceptors, 1, 'Only current identity guard interceptor survives');
    assert.ok(identityCount >= 2, 'New generation must independently confirm backend identity');
    releaseResolve();
    await within(settled, 'late old /auth/me response');
    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), firstSignedToken);
    assert.equal((await runtimeSessionState(page)).generation, newState.generation,
      'Old profile 401 must not invalidate the newer same-token login');
    console.log('ADMIN_DELAYED_IDENTITY_RACE_PASS');
  } finally {
    if (releaseHeldIdentity) releaseHeldIdentity();
    await context.close();
  }
}

async function run() {
  if (process.env.GITHUB_ACTIONS !== 'true' || process.env.FITFLOW_E2E_SYNTHETIC_ONLY !== '1' ||
      !email?.endsWith('@example.com') || !clientEmail?.endsWith('@example.com')) {
    throw new Error('BLOCKED_PRECONDITION: CI synthetic-only E2E');
  }
  // Validate the real signed HTTP contract before attributing any failure to React.
  const form = new URLSearchParams({ username: email, password });
  const loginResponse = await fetch(API + '/auth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  });
  assert.equal(loginResponse.status, 200, 'Synthetic ADMIN login must return signed credentials');
  const { access_token: signed } = await loginResponse.json();
  assert.ok(signed, 'Backend must return access token');
  const profileResponse = await fetch(API + '/auth/me', {
    headers: { Authorization: 'Bearer ' + signed },
  });
  assert.equal(profileResponse.status, 200, 'Signed /auth/me must resolve real user profile');
  const identity = await profileResponse.json();
  assert.equal(identity.email, email);
  assert.equal(identity.role, 'admin');
  assert.equal(identity.active, true);
  const clientResponse = await fetch(API + '/clients/', {
    headers: { Authorization: 'Bearer ' + signed },
  });
  assert.equal(clientResponse.status, 200, 'Signed ADMIN must list real clients');
  assert.ok((await clientResponse.json()).some((x) => x.full_name === 'Cliente Sintético'));
  const teacherResponse = await fetch(API + '/teachers/public');
  assert.equal(teacherResponse.status, 200);
  const teacherRows = await teacherResponse.json();
  assert.ok(teacherRows.some((x) => x.full_name === 'Profesora Sintética'));
  assert.ok(teacherRows.every((x) => !Object.hasOwn(x, 'cuil')), 'TeacherPublic must omit CUIL');
  const classesResponse = await fetch(API + '/gym-classes/public');
  assert.equal(classesResponse.status, 200);
  assert.ok((await classesResponse.json()).some((x) => x.name === 'Clase Sintética E2E'));
  const clientForm = new URLSearchParams({ username: clientEmail, password });
  const clientLogin = await fetch(API + '/auth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: clientForm,
  });
  assert.equal(clientLogin.status, 200, 'Synthetic client must obtain backend-signed token');
  const clientTokens = await clientLogin.json();
  const denied = await fetch(API + '/clients/', {
    headers: { Authorization: 'Bearer ' + clientTokens.access_token },
  });
  assert.equal(denied.status, 403, 'Backend must deny the client role access to admin list');
  console.log('ADMIN_SIGNED_HTTP_PREFLIGHT_PASS');
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    await login(page, email);
    try {
      await page.getByRole('heading', { name: 'Panel de administración' }).waitFor({ timeout: 20000 });
    } catch (error) {
      // Bounded synthetic-only diagnostics. Never log Authorization or form values.
      const state = {
        path: new URL(page.url()).pathname,
        headings: await page.getByRole('heading').allTextContents(),
        alerts: await page.getByRole('alert').allTextContents(),
      };
      console.error('ADMIN_BROWSER_DIAGNOSTIC', JSON.stringify(state));
      throw error;
    }
    assert.equal(new URL(page.url()).pathname, '/admin');
    const widthMobile = await page.evaluate(() => [document.documentElement.clientWidth, document.documentElement.scrollWidth]);
    assert.equal(widthMobile[0], 390);
    assert.ok(widthMobile[1] <= 390, 'ADMIN dashboard must not overflow at 390px');
    const mobileMenu = page.getByRole('button', { name: 'Menú', exact: true });
    await mobileMenu.click();
    await page.keyboard.press('Escape');
    assert.equal(await mobileMenu.getAttribute('aria-expanded'), 'false');
    assert.equal(await mobileMenu.evaluate((element) => element === document.activeElement), true,
      'Escape must restore keyboard focus to mobile menu trigger');
    await mobileMenu.click();
    await page.getByRole('link', { name: 'Profesores', exact: true }).focus();
    await page.keyboard.press('Enter');
    await page.getByRole('heading', { name: 'Profesores' }).waitFor();
    await page.getByText('Profesora Sintética', { exact: true }).filter({ visible: true }).first().waitFor();
    // Controlled synthetic outage: prove error/retry without changing Product data.
    const teacherApi = '**/api/v1/teachers/public';
    await page.route(teacherApi, (route) => route.abort('failed'));
    await page.getByRole('button', { name: 'Actualizar', exact: true }).click();
    await page.getByRole('alert').getByText('No pudimos cargar los profesores.').waitFor();
    await page.unroute(teacherApi);
    await page.getByRole('button', { name: 'Actualizar', exact: true }).click();
    await page.getByText('Profesora Sintética', { exact: true }).filter({ visible: true }).first().waitFor();

    assert.equal(await page.getByText('20999999999').count(), 0, 'Teacher CUIL must not appear');
    await page.getByRole('button', { name: 'Menú', exact: true }).click();
    await page.getByRole('link', { name: 'Clases', exact: true }).click();
    await page.getByRole('heading', { name: 'Clases', exact: true }).waitFor();
    await page.getByText('Clase Sintética E2E', { exact: true }).filter({ visible: true }).first().waitFor();
    await page.getByRole('dialog').waitFor({ state: 'hidden' });
    await page.setViewportSize({ width: 1280, height: 800 });
    const widthDesktop = await page.evaluate(() => [document.documentElement.clientWidth, document.documentElement.scrollWidth]);
    assert.equal(widthDesktop[0], 1280);
    assert.ok(widthDesktop[1] <= 1280, 'ADMIN desktop must not overflow');
    await page.getByText(email).first().waitFor();
    await page.locator('aside').getByRole('link', { name: 'Clientes', exact: true }).click();
    await page.getByRole('heading', { name: 'Clientes' }).waitFor();
    await page.getByText('Cliente Sintético').first().waitFor();
    await page.goto(WEB + '/admin');
    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    await page.getByRole('button', { name: 'Menú de perfil' }).click();
    await page.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await page.waitForURL('**/login');
    assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), null);
    await page.goto(WEB + '/admin');
    await page.waitForURL('**/login');

    // The expired token is genuinely signed by this disposable backend secret.
    const expired = fs.readFileSync('/tmp/fitflow-admin-e2e-expired.jwt', 'utf8');
    const expiredResponse = await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + expired },
    });
    assert.equal(expiredResponse.status, 401);
    const expiredContext = await browser.newContext();
    const expiredPage = await expiredContext.newPage();
    await expiredPage.addInitScript((token) => {
      localStorage.setItem('access_token', token);
    }, expired);
    await expiredPage.goto(WEB + '/admin');
    await expiredPage.waitForURL('**/login');
    assert.equal(await expiredPage.getByRole('heading', { name: 'Panel de administración' }).count(), 0);
    await expiredContext.close();

    const guest = await browser.newContext();
    const guestPage = await guest.newPage();
    await guestPage.goto(WEB + '/admin');
    await guestPage.waitForURL('**/login');
    await guest.close();

    const wrongRole = await browser.newContext();
    const wrongPage = await wrongRole.newPage();
    await login(wrongPage, clientEmail);
    await wrongPage.waitForURL('**/home');
    await wrongPage.goto(WEB + '/admin');
    await wrongPage.waitForURL((url) => !url.pathname.startsWith('/admin'));
    assert.equal(await wrongPage.getByRole('heading', { name: 'Panel de administración' }).count(), 0);
    await wrongRole.close();
    await context.close();
    await verifyRapidReLoginAndStale401(browser);
    await verifyDelayedIdentityAcrossSameTokenReLogin(browser);
    console.log('ADMIN_SIGNED_E2E_PASS: JWT login, backend identity, real data, privacy, 390/1280, role, expired, anonymous, logout, stale session races');
  } finally {
    await browser.close();
  }
}

run().catch((error) => { console.error(error.stack || error.message); process.exitCode = 1; });
