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
    assert.equal(await page.evaluate(() => sessionStorage.getItem('access_token')), token);
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
    const signedToken = await page.evaluate(() => sessionStorage.getItem('access_token'));
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
    assert.equal(await page.evaluate(() => sessionStorage.getItem('access_token')), signedToken);
    assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), null,
      'Session must not persist its access token across tabs');
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
    let old401Fulfilled = false;
    let old401FulfillError = null;
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
        old401Fulfilled = true;
      } catch (error) {
        old401FulfillError = String(error);
      } finally {
        settledResolve();
      }
    });
    await page.evaluate(async () => {
      const api = (await import('/src/services/api.ts')).default;
      window.__fitflowOldRequest = api.get('/clients/?skip=0&limit=100')
        .then((response) => ({ kind: 'resolved', status: response.status }),
          (error) => ({ kind: 'rejected', status: error?.response?.status ?? null,
            code: error?.code ?? null }));
    });
    await within(seen, 'captured pre-logout Axios request');
    const revokedResponse = page.waitForResponse((response) =>
      new URL(response.url()).pathname === '/api/v1/auth/logout');
    await page.getByRole('button', { name: 'Menú de perfil' }).click();
    await page.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await page.waitForURL('**/login');
    const remoteLogout = await within(revokedResponse, 'server-side session logout');
    assert.equal(remoteLogout.status(), 204,
      'A03 requires server-confirmed logout; local-only clearing is insufficient');
    const previousAccess = await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + signedToken },
    });
    assert.equal(previousAccess.status, 401,
      'Logout must revoke the backend-signed access JWT before normal expiry');
    await page.waitForFunction(async () => {
      const api = (await import('/src/services/api.ts')).default;
      return api.interceptors.response.handlers.filter(Boolean).length === 0;
    });
    const loggedOutGeneration = (await runtimeSessionState(page)).generation;
    assert.ok(loggedOutGeneration > rehydratedState.generation,
      'Logout must advance the epoch within the rehydrated browser module');
    // Keep the same browser document to preserve the in-flight old Axios
    // response interceptor; only login credentials are sent to the real API.
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Contraseña').fill(password);
    await page.getByRole('button', { name: 'Ingresar' }).click();
    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const renewedToken = await page.evaluate(() => sessionStorage.getItem('access_token'));
    assert.ok(renewedToken && renewedToken !== signedToken,
      'New login must issue a new signed session instead of replaying a revoked JWT');
    const newGeneration = (await runtimeSessionState(page)).generation;
    assert.ok(newGeneration > loggedOutGeneration,
      'Fresh post-logout login must have a distinct generation');
    assert.equal((await runtimeSessionState(page)).activeInterceptors, 1,
      'New ADMIN session must install exactly one interceptor');
    releaseResolve();
    await within(settled, 'late 401 delivery attempt');
    assert.equal(old401Fulfilled, true,
      'Old Axios response must be fulfilled, not silently canceled: ' + (old401FulfillError || ''));
    const oldResult = await within(page.evaluate(() => window.__fitflowOldRequest),
      'old Axios promise rejected with actual HTTP 401');
    assert.equal(oldResult.kind, 'rejected', 'Old response must reject in the original Axios consumer');
    assert.equal(oldResult.status, 401, 'Old Axios consumer must observe HTTP 401, not cancellation');
    assert.equal(await page.evaluate(() => sessionStorage.getItem('access_token')), renewedToken,
      'Old 401 must not log out a newer independently signed session');
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
  let releaseHeldProbe;
  try {
    let firstProfileResolve;
    let oldSettledResolve;
    let probeSeenResolve;
    let probeSettledResolve;
    const firstProfileSeen = new Promise((resolve) => { firstProfileResolve = resolve; });
    const oldSettled = new Promise((resolve) => { oldSettledResolve = resolve; });
    const probeSeen = new Promise((resolve) => { probeSeenResolve = resolve; });
    const probeSettled = new Promise((resolve) => { probeSettledResolve = resolve; });
    let releaseOldResolve;
    const releaseOld = new Promise((resolve) => { releaseOldResolve = resolve; });
    releaseHeldIdentity = releaseOldResolve;
    let releaseProbeResolve;
    const releaseProbe = new Promise((resolve) => { releaseProbeResolve = resolve; });
    releaseHeldProbe = releaseProbeResolve;

    let firstNetworkRequest;
    let oldProfileFulfilled = false;
    let oldProfileRouteError = null;
    let probe401Fulfilled = false;
    let probe401RouteError = null;
    let identityCount = 0;
    let resolveNetworkOutcome;
    const originalNetworkOutcome = new Promise((resolve) => { resolveNetworkOutcome = resolve; });
    page.on('requestfailed', (request) => {
      if (request === firstNetworkRequest) {
        resolveNetworkOutcome({
          kind: 'requestfailed',
          reason: request.failure()?.errorText ?? '',
        });
      }
    });
    page.on('response', (response) => {
      if (response.request() === firstNetworkRequest) {
        resolveNetworkOutcome({ kind: 'httpResponse', status: response.status() });
      }
    });

    await page.route('**/api/v1/auth/me**', async (route) => {
      const requestUrl = new URL(route.request().url());
      if (requestUrl.searchParams.get('fitflow_old_identity_probe') === '1') {
        probeSeenResolve();
        await releaseProbe;
        try {
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: '{"detail":"synthetic delayed identity response"}',
          });
          probe401Fulfilled = true;
        } catch (error) {
          probe401RouteError = String(error);
        } finally {
          probeSettledResolve();
        }
        return;
      }
      identityCount += 1;
      if (identityCount > 1) {
        await route.continue();
        return;
      }
      firstNetworkRequest = route.request();
      firstProfileResolve();
      await releaseOld;
      try {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: '{"detail":"synthetic old identity rejection"}',
        });
        oldProfileFulfilled = true;
      } catch (error) {
        oldProfileRouteError = String(error);
      } finally {
        oldSettledResolve();
      }
    });

    await login(page, email);
    await within(firstProfileSeen, 'first pending TanStack /auth/me request');
    const firstSignedToken = await page.evaluate(() => sessionStorage.getItem('access_token'));
    assert.ok(firstSignedToken, 'Signed JWT must exist during the first pending identity check');

    // Hold an additional *noncancellable* Axios /auth/me request from the OLD
    // session to verify a real 401 is consumed by its original interceptor.
    // TanStack's actual query is allowed to abort on unmount, but that is
    // checked independently and never misreported as delivered HTTP 401.
    await page.evaluate(async () => {
      const api = (await import('/src/services/api.ts')).default;
      window.__fitflowOldIdentityProbe = api.get('/auth/me?fitflow_old_identity_probe=1')
        .then((response) => ({ kind: 'resolved', status: response.status }),
          (error) => ({ kind: 'rejected', status: error?.response?.status ?? null,
            code: error?.code ?? null }));
    });
    await within(probeSeen, 'old noncancellable /auth/me Axios probe');

    await page.evaluate(() => {
      history.pushState({}, '', '/login');
      dispatchEvent(new PopStateEvent('popstate'));
    });
    await page.getByRole('heading', { name: 'Iniciar Sesión' }).waitFor();
    await loginUsingSignedToken(page, firstSignedToken);
    const newState = await runtimeSessionState(page);
    assert.ok(newState.generation >= 2, 'New same-token login must advance auth generation');
    assert.equal(newState.activeInterceptors, 1, 'Only current identity guard interceptor survives');
    assert.ok(identityCount >= 2, 'New generation must independently confirm backend identity');

    releaseOldResolve();
    releaseProbeResolve();
    await within(oldSettled, 'old TanStack /auth/me request terminal route action');
    await within(probeSettled, 'forced old Axios /auth/me 401 delivery attempt');

    // There are two valid cases for the old TanStack request: cancellation by
    // AbortSignal, or actual HTTP 401. We REQUIRE an observed network outcome
    // in either case, and do not claim delivery when it was canceled.
    const networkOutcome = await within(originalNetworkOutcome,
      'old TanStack /auth/me response or explicit request failure');
    assert.ok(oldProfileFulfilled || oldProfileRouteError,
      'Old TanStack query must reach a definite route delivery/cancel result');
    if (networkOutcome.kind === 'httpResponse') {
      assert.equal(networkOutcome.status, 401, 'Old network response must be a 401');
      assert.equal(oldProfileFulfilled, true, 'Old network HTTP 401 must come from the held route');
    } else {
      assert.equal(networkOutcome.kind, 'requestfailed');
      assert.ok(networkOutcome.reason, 'Canceled old query must have a recorded network failure');
    }

    // F002 cannot pass from a cancellation alone: REQUIRE HTTP 401 to be
    // fulfilled AND rejected by the Axios consumer captured before relogin.
    assert.equal(probe401Fulfilled, true,
      'Old Axios /auth/me 401 must be delivered: ' + (probe401RouteError || ''));
    const probeResult = await within(page.evaluate(() => window.__fitflowOldIdentityProbe),
      'old /auth/me Axios consumer rejection');
    assert.equal(probeResult.kind, 'rejected', 'Original /auth/me Axios consumer must reject');
    assert.equal(probeResult.status, 401, 'Old /auth/me Axios consumer must receive 401, not cancellation');

    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    assert.equal(await page.evaluate(() => sessionStorage.getItem('access_token')), firstSignedToken);
    assert.equal((await runtimeSessionState(page)).generation, newState.generation,
      'Old delivered identity 401 must not invalidate the newer same-token login');
    console.log('ADMIN_DELAYED_IDENTITY_RACE_PASS: original query network outcome=' + networkOutcome.kind
      + ', old Axios 401 delivered to consumer');
  } finally {
    if (releaseHeldIdentity) releaseHeldIdentity();
    if (releaseHeldProbe) releaseHeldProbe();
    await context.close();
  }
}

// Diagnostic-only snapshot: no tokens, emails, query strings, DOM dumps or passwords.
async function safeKeyboardNavSnapshot(page) {
  try {
    return await page.evaluate(() => {
      const active = document.activeElement;
      const rawPath = window.location.pathname;
      const allowedPaths = ['/admin', '/admin/teachers', '/login', '/home'];
      const heading = Array.from(document.querySelectorAll('main h1'))
        .find((element) => element.textContent?.trim() === 'Profesores');
      const visible = (element) => Boolean(element && element.getClientRects().length > 0 &&
        getComputedStyle(element).visibility !== 'hidden');
      const dialogs = Array.from(document.querySelectorAll('[role="dialog"]'));
      const trigger = document.querySelector('button[aria-label="Menú"]');
      return {
        path: allowedPaths.includes(rawPath) ? rawPath : 'other_path',
        focusedTag: active?.tagName ?? null,
        focusedTeachersLink: active?.tagName === 'A' &&
          active.getAttribute('href') === '/admin/teachers',
        menuExpanded: trigger?.getAttribute('aria-expanded') ?? null,
        dialogCount: dialogs.length,
        visibleDialogCount: dialogs.filter(visible).length,
        teachersHeadingMounted: Boolean(heading),
        teachersHeadingVisible: visible(heading) &&
          !heading.closest('[aria-hidden="true"], [inert]'),
      };
    });
  } catch {
    return { observation: 'snapshot_unavailable' };
  }
}


/**
 * Observe navigation only after keyboard Enter has been delivered. A
 * synthetic-only local fixture exercises this catch path without real data.
 */
async function qualifyTeachersKeyboardRoute(page, { timeout = 30000, report = console.error } = {}) {
  let failedStage = 'route';
  try {
    await page.waitForURL((url) => url.pathname === '/admin/teachers', { timeout });
    failedStage = 'drawer';
    await page.getByRole('dialog').waitFor({ state: 'hidden', timeout });
    failedStage = 'heading';
    await page.getByRole('heading', { name: 'Profesores' }).waitFor({ timeout });
  } catch (error) {
    const afterEnter = await safeKeyboardNavSnapshot(page);
    report('ADMIN_KEYBOARD_NAV_DIAGNOSTIC', JSON.stringify({ failedStage, afterEnter }));
    throw error;
  }
}

async function qualifySyntheticFailureDiagnostic(browser) {
  // Browser-local markup only: no backend calls, remote routes or credentials.
  const fixture = await browser.newContext();
  try {
    const page = await fixture.newPage();
    await page.setContent('<button aria-label="Menú" aria-expanded="true">Menú</button>' +
      '<div role="dialog"><a href="/admin/teachers">Profesores</a></div>' +
      '<main><h1>Fixture</h1></main>');
    const reports = [];
    let rejected = false;
    try {
      await qualifyTeachersKeyboardRoute(page, {
        timeout: 80,
        report: (marker, payload) => reports.push({ marker, payload }),
      });
    } catch (error) {
      rejected = error?.name === 'TimeoutError';
    }
    assert.equal(rejected, true, 'Synthetic wrong-route failure must propagate');
    assert.equal(reports.length, 1, 'Synthetic failure must emit exactly one report');
    assert.equal(reports[0].marker, 'ADMIN_KEYBOARD_NAV_DIAGNOSTIC');
    const payload = JSON.parse(reports[0].payload);
    assert.deepEqual(Object.keys(payload).sort(), ['afterEnter', 'failedStage'].sort());
    assert.equal(payload.failedStage, 'route');
    assert.equal(payload.afterEnter.path, 'other_path');
    assert.equal(payload.afterEnter.menuExpanded, 'true');
    assert.equal(payload.afterEnter.teachersHeadingMounted, false);
    assert.equal(payload.afterEnter.focusedTeachersLink, false);
    assert.deepEqual(Object.keys(payload.afterEnter).sort(), [
      'path', 'focusedTag', 'focusedTeachersLink', 'menuExpanded', 'dialogCount',
      'visibleDialogCount', 'teachersHeadingMounted', 'teachersHeadingVisible',
    ].sort());
    assert.doesNotMatch(reports[0].payload,
      /authorization|access_token|refresh_token|password|localstorage|@example\.com/i);
    console.log('ADMIN_KEYBOARD_NEGATIVE_DIAGNOSTIC_PASS');
  } finally {
    await fixture.close();
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
    await qualifyTeachersKeyboardRoute(page);
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
    assert.equal(await page.evaluate(() => sessionStorage.getItem('access_token')), null);
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
      sessionStorage.setItem('access_token', token);
      sessionStorage.setItem('refresh_token', 'expired-synthetic-fixture-only');
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
    await qualifySyntheticFailureDiagnostic(browser);
    console.log('ADMIN_SIGNED_E2E_PASS: JWT login, backend identity, real data, privacy, 390/1280, role, expired, anonymous, logout, stale session races');
  } finally {
    await browser.close();
  }
}

run().catch((error) => { console.error(error.stack || error.message); process.exitCode = 1; });
