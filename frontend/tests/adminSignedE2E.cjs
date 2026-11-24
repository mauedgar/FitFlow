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

async function activeAccessToken(page) {
  // Runtime module introspection only inside synthetic E2E; never print JWT.
  return page.evaluate(async () => {
    const api = (await import('/src/services/api.ts')).default;
    const header = api.defaults.headers.common.Authorization;
    return typeof header === 'string' && header.startsWith('Bearer ')
      ? header.slice(7) : null;
  });
}

async function loginWithNewSignedSession(page) {
  // Replaying the old signed JWT after durable logout must NOT grant access.
  // Preserve the mounted React generation: page.goto would reset the
  // session epoch, masking the stale-response protection being tested.
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Contraseña').fill(password);
  await page.getByRole('button', { name: 'Ingresar' }).click();
  await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
  assert.ok(await activeAccessToken(page), 'Browser access must live in memory');
  assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), null,
    'Modern access must not enter localStorage');
}



async function verifySameTabRefreshCannotRestoreBearerDuringLogout(browser) {
  // Hold a real signed refresh HTTP 200 while local logout begins; the
  // newly bumped same-tab generation must reject that late authorization.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  let announceResponse, releaseResponse;
  const captured = new Promise(resolve => { announceResponse = resolve; });
  const held = new Promise(resolve => { releaseResponse = resolve; });
  try {
    await login(page, email);
    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const oldAccess = await activeAccessToken(page);
    assert.ok(oldAccess, 'Initial bearer must be a real signed session');

    await page.route('**/auth/browser/refresh', async route => {
      const response = await route.fetch();
      assert.equal(response.status(), 200, 'Synthetic refresh reached the real backend');
      announceResponse();
      await held;
      await route.fulfill({ response });
    });

    await page.evaluate(() => window.dispatchEvent(new Event('online')));
    await within(captured, 'held same-tab signed refresh response');
    const before = await runtimeSessionState(page);
    await page.getByRole('button', { name: 'Menú de perfil' }).click();
    await page.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await page.waitForURL('**/login');
    assert.equal(await activeAccessToken(page), null,
      'Local logout must clear bearer before the delayed response');
    const after = await runtimeSessionState(page);
    assert.ok(after.generation > before.generation,
      'Same-tab logout must advance the generation synchronously');
    releaseResponse();
    await page.waitForFunction(() => sessionStorage.getItem('fitflow_logout_pending') === null);
    assert.equal(await activeAccessToken(page), null,
      'Late refresh may not resurrect an in-memory bearer after logout');
    const old = await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + oldAccess },
    });
    assert.equal(old.status, 401, 'Real PostgreSQL revocation must still hold');
  } finally {
    releaseResponse?.();
    await context.close();
  }
}

async function verifyPendingLogoutCannotBeSilentlyReplaced(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  try {
    await login(page, email);
    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const access = await activeAccessToken(page);
    assert.ok(access, 'Signed family was registered');
    // Abort BEFORE forwarding, so the server has no revocation COMMIT.
    await page.route('**/auth/browser/logout', async route => route.abort());
    await page.getByRole('button', { name: 'Menú de perfil' }).click();
    await page.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await page.waitForURL('**/login');
    await page.getByRole('button', { name: 'Reintentar salida segura' }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Ingresar' }).isDisabled(), true,
      'No login may overwrite a pending durable logout cookie');
    const stillActive = await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + access },
    });
    assert.equal(stillActive.status, 200, 'Aborted logout did not revoke old family');
    await page.unroute('**/auth/browser/logout');
    await page.getByRole('button', { name: 'Reintentar salida segura' }).click();
    await page.waitForFunction(() => sessionStorage.getItem('fitflow_logout_pending') === null);
    assert.equal(await page.getByRole('button', { name: 'Ingresar' }).isDisabled(), false,
      'Login unblocks only after PG-confirmed logout or exact replay');
    const revoked = await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + access },
    });
    assert.equal(revoked.status, 401);
  } finally {
    await context.close();
  }
}

async function verifyCrossTabCookieSynchronizationAndReplacementGuard(browser) {
  // Tabs share one actual browser cookie but have distinct React memory.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const first = await context.newPage();
  const second = await context.newPage();
  try {
    await login(first, email);
    await first.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    assert.ok(await activeAccessToken(first));
    await second.goto(WEB + '/admin');
    await second.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    assert.ok(await activeAccessToken(second), 'Other tab must rehydrate same cookie');

    // Another login must not overwrite a still-registered durable family.
    await second.goto(WEB + '/login');
    await second.getByLabel('Email').fill(email);
    await second.getByLabel('Contraseña').fill(password);
    const denial = second.waitForResponse(response =>
      response.url() === API + '/auth/browser/token' && response.status() === 409);
    await second.getByRole('button', { name: 'Ingresar' }).click();
    await within(denial, 'active family replacement must return 409');

    // Server-confirmed logout propagates a nonsecret storage event to both tabs.
    await first.getByRole('button', { name: 'Menú de perfil' }).click();
    await first.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await first.waitForURL('**/login');
    await second.waitForFunction(async () => {
      const api = (await import('/src/services/api.ts')).default;
      return !api.defaults.headers.common.Authorization;
    });
    assert.equal(await activeAccessToken(second), null);
  } finally {
    await context.close();
  }
}


async function verifyExpiredLogoutProofUnblocksWithoutFalseAck(browser) {
  // Single-tab cookie expiry after a network-aborted logout (no PG COMMIT).
  // The separate two-tab test covers automatic orphaned logout recovery.
  // Here no surviving peer can independently COMMIT before cookie removal.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const first = await context.newPage();
  try {
    await login(first, email);
    await first.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const priorAccess = await activeAccessToken(first);
    assert.ok(priorAccess);
    await first.route('**/auth/browser/logout', route => route.abort());
    await first.getByRole('button', { name: 'Menú de perfil' }).click();
    await first.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await first.waitForURL('**/login');
    await first.getByRole('button', { name: 'Reintentar salida segura' }).waitFor();
    assert.equal(await first.getByRole('button', { name: 'Ingresar' }).isDisabled(), true);

    // Browser expires/discards the cookie while the logout remains pending.
    await context.clearCookies();
    await first.unroute('**/auth/browser/logout');
    await first.getByRole('button', { name: 'Reintentar salida segura' }).click();
    await first.getByText('La cookie de sesión ya no está disponible.', { exact: false }).waitFor();
    assert.equal(await first.getByRole('button', { name: 'Ingresar' }).isDisabled(), false);
    // No false server ACK: abort-before-forwarding means original access
    // remains active in PG until its signed expiration.
    const oldStillLive = await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + priorAccess },
    });
    assert.equal(oldStillLive.status, 200, 'Missing cookie must not be reported as PG revocation');

    await loginWithNewSignedSession(first);
    assert.ok(await activeAccessToken(first), 'New login registers a separate durable family');
  } finally {
    await context.close();
  }
}


async function verifyLateLoginResponseRejectedAfterCrossTabLogout(browser) {
  // Synthetic network interleaving: hold a real HTTP 200 login response
  // until a different tab announces a newer logout generation.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const observer = await context.newPage();
  const pending = await context.newPage();
  let release;
  let captured;
  const blocked = new Promise(resolve => { release = resolve; });
  const wasCaptured = new Promise(resolve => { captured = resolve; });
  try {
    await observer.goto(WEB + '/login');
    await pending.goto(WEB + '/login');
    const before = await runtimeSessionState(pending);
    await pending.route('**/auth/browser/token', async route => {
      const response = await route.fetch();
      assert.equal(response.status(), 200, 'Synthetic login was successfully registered');
      captured();
      await blocked;
      await route.fulfill({ response });
    });
    await pending.getByLabel('Email').fill(email);
    await pending.getByLabel('Contraseña').fill(password);
    await pending.getByRole('button', { name: 'Ingresar' }).click();
    await within(wasCaptured, 'held successful browser login');
    await observer.evaluate(() => {
      localStorage.setItem('fitflow_browser_auth_epoch',
        'logout-confirmed|' + Date.now() + '|' + crypto.randomUUID());
    });
    await pending.waitForFunction(async (initial) => {
      const epochs = await import('/src/utils/authSessionGeneration.ts');
      return epochs.getAuthSessionGeneration() > initial;
    }, before.generation);
    release();
    await pending.waitForFunction(() => {
      const button = document.querySelector('button[type=submit]');
      return button && !button.disabled;
    });
    assert.equal(new URL(pending.url()).pathname, '/login',
      'Late HTTP 200 must not navigate after a newer logout');
    assert.equal(await activeAccessToken(pending), null,
      'A stale successful login must not restore memory bearer');
  } finally {
    release?.();
    await context.close();
  }
}


async function verifyQueuedLoginCannotResurrectAfterRealLogout(browser) {
  // The queued browser login begins before another tab confirms logout.
  // Real PG logout must commit while the lock is held by test instrumentation;
  // after the shared epoch advances the queued login must NEVER POST or set cookie.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const owner = await context.newPage();
  const contender = await context.newPage();
  let releaseHeld;
  let loginPosts = 0;
  try {
    await login(owner, email);
    await owner.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const oldAccess = await activeAccessToken(owner);
    assert.ok(oldAccess);
    await contender.goto(WEB + '/login');
    await contender.getByLabel('Email').waitFor();
    const before = await runtimeSessionState(contender);
    const heldLock = owner.evaluate(async () => {
      await navigator.locks.request('fitflow-auth-cookie-write', async () => {
        window.__ffHoldLoginQueue = true;
        await new Promise(resolve => { window.__ffReleaseLoginQueue = resolve; });
      });
    });
    releaseHeld = () => owner.evaluate(() => window.__ffReleaseLoginQueue?.());
    await owner.waitForFunction(() => window.__ffHoldLoginQueue === true);
    contender.on('request', request => {
      if (request.method() === 'POST' && request.url() === API + '/auth/browser/token') {
        loginPosts++;
      }
    });
    await contender.getByLabel('Email').fill(email);
    await contender.getByLabel('Contraseña').fill(password);
    await contender.getByRole('button', { name: 'Ingresar' }).click();
    await contender.waitForFunction(async () => {
      const state = await navigator.locks.query();
      return state.pending.some(item => item.name === 'fitflow-auth-cookie-write');
    });

    const proof = await context.request.get(API + '/auth/browser/logout-proof', {
      headers: { Origin: WEB },
    });
    assert.equal(proof.status(), 200);
    const csrf = (await proof.json()).csrf_token;
    const logout = await context.request.post(API + '/auth/browser/logout', {
      headers: { Origin: WEB, 'X-CSRF-Token': csrf },
    });
    assert.equal(logout.status(), 204, 'Real PostgreSQL logout must confirm COMMIT');
    const revoked = await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + oldAccess },
    });
    assert.equal(revoked.status, 401);
    // The backend DID return a real PG HTTP204 above. Simulate the
    // provider's receipt+broadcast pair, not a naked untrusted storage ACK.
    // The separate real-provider test verifies the actual broadcast path.
    await owner.evaluate(() => {
      const operation = crypto.randomUUID();
      localStorage.setItem('fitflow_logout_confirmed_history',
        JSON.stringify([operation]));
      localStorage.setItem('fitflow_logout_confirmed_operation', operation);
      localStorage.setItem('fitflow_browser_auth_epoch',
        'logout-confirmed|' + Date.now() + '|' + operation);
    });
    await contender.waitForFunction(async initial => {
      const epochs = await import('/src/utils/authSessionGeneration.ts');
      return epochs.getAuthSessionGeneration() > initial;
    }, before.generation);
    await releaseHeld();
    await heldLock;
    await contender.waitForFunction(() => {
      const loginButton = document.querySelector('button[type=submit]');
      return loginButton && !loginButton.disabled;
    });
    assert.equal(loginPosts, 0, 'Superseded queued login must not issue HTTP POST');
    assert.equal(new URL(contender.url()).pathname, '/login');
    assert.equal(await activeAccessToken(contender), null);
    const cookies = await context.cookies(API + '/auth/browser');
    assert.equal(cookies.some(cookie => cookie.name === 'fitflow_browser_refresh'), false,
      'A queued stale login cannot re-create HttpOnly cookie after real logout');
  } finally {
    await releaseHeld?.().catch(() => {});
    await context.close();
  }
}


async function verifySurvivingTabRecoversOrphanedLogout(browser) {
  // Real cookie-bound HTTP revocation after the initiator closes without
  // reaching the server. No synthetic localStorage ACK is supplied.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const initiator = await context.newPage();
  const survivor = await context.newPage();
  let releaseHeld;
  let reportCaptured;
  const release = new Promise(resolve => { releaseHeld = resolve; });
  const captured = new Promise(resolve => { reportCaptured = resolve; });
  try {
    await login(initiator, email);
    await initiator.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const oldAccess = await activeAccessToken(initiator);
    assert.ok(oldAccess);
    await survivor.goto(WEB + '/admin');
    await survivor.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    await initiator.route('**/auth/browser/logout', route => route.abort());
    await survivor.route('**/auth/browser/logout', async route => {
      reportCaptured();
      await release;
      await route.continue();
    });
    await initiator.getByRole('button', { name: 'Menú de perfil' }).click();
    await initiator.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await within(captured, 'survivor auto recovery POST');
    assert.equal(await survivor.evaluate(
      () => sessionStorage.getItem('fitflow_logout_pending')), '1');
    assert.equal((await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + oldAccess },
    })).status, 200, 'Intercepted survivor POST has not revoked the old family');
    await initiator.close(); // Origin dies; the surviving tab owns the recovery.
    const ack = survivor.waitForResponse(response =>
      response.url() === API + '/auth/browser/logout' && response.status() === 204);
    releaseHeld();
    await within(ack, 'real PG revocation ACK in survivor');
    await survivor.waitForFunction(
      () => sessionStorage.getItem('fitflow_logout_pending') === null);
    assert.equal((await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + oldAccess },
    })).status, 401, 'Confirmed survivor ACK must revoke the old family');
    await survivor.goto(WEB + '/login');
    assert.equal(await survivor.getByRole('button', { name: 'Ingresar' }).isDisabled(),
      false, 'Sign-in unblocks only after real revocation ACK');
  } finally {
    releaseHeld?.();
    await context.close();
  }
}



async function verifyEarlierRealLogoutReceiptSurvivesLaterConfirmedFamily(browser) {
  // Both receipts originate from real signed PostgreSQL 204 responses.
  // A surviving tab may reload after a different later family is revoked.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const owner = await context.newPage();
  try {
    await login(owner, email);
    await owner.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    await owner.getByRole('button', { name: 'Menú de perfil' }).click();
    const firstAck = owner.waitForResponse(response =>
      response.url() === API + '/auth/browser/logout' && response.status() === 204);
    await owner.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await within(firstAck, 'first genuine PostgreSQL logout 204');
    await owner.waitForFunction(() =>
      sessionStorage.getItem('fitflow_logout_pending') === null);
    const first = await owner.evaluate(
      () => localStorage.getItem('fitflow_logout_confirmed_operation'));
    assert.ok(first, 'First confirmed logout must have a nonsecret operation');

    await owner.goto(WEB + '/login');
    await loginWithNewSignedSession(owner);
    await owner.getByRole('button', { name: 'Menú de perfil' }).click();
    const secondAck = owner.waitForResponse(response =>
      response.url() === API + '/auth/browser/logout' && response.status() === 204);
    await owner.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await within(secondAck, 'second genuine PostgreSQL logout 204');
    await owner.waitForFunction(() =>
      sessionStorage.getItem('fitflow_logout_pending') === null);
    const saved = await owner.evaluate(() => ({
      last: localStorage.getItem('fitflow_logout_confirmed_operation'),
      history: JSON.parse(localStorage.getItem('fitflow_logout_confirmed_history') || '[]'),
    }));
    assert.notEqual(saved.last, first, 'Two different session revocations have different IDs');
    assert.ok(saved.history.includes(first) && saved.history.includes(saved.last),
      'Previous real server ACK must survive a later family confirmation');

    const survivor = await context.newPage();
    await survivor.goto(WEB + '/login');
    await survivor.evaluate(operation => {
      sessionStorage.setItem('fitflow_logout_pending', '1');
      sessionStorage.setItem('fitflow_logout_operation', operation);
    }, first);
    await survivor.reload();
    await survivor.waitForFunction(() =>
      sessionStorage.getItem('fitflow_logout_pending') === null);
    assert.equal(await survivor.getByText(
      'La cookie de sesión ya no está disponible.', { exact: false }).count(), 0,
    'A reloaded previous pending operation must recognize its real 204');
    assert.equal(await survivor.getByRole('button', { name: 'Ingresar' }).isDisabled(),
      false, 'Previously committed logout cannot regress to pending');
  } finally {
    await context.close();
  }
}

async function verifyCrossTabLogoutAckDominatesQueuedMissingProof(browser) {
  // The origin's real server COMMIT happens before the first tab receives
  // HTTP 204; a peer auto-recovery waits on the same Web Lock.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const origin = await context.newPage();
  const peer = await context.newPage();
  let free;
  let captured;
  const held = new Promise(resolve => { free = resolve; });
  const intercepted = new Promise(resolve => { captured = resolve; });
  try {
    await login(origin, email);
    await origin.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const oldAccess = await activeAccessToken(origin);
    assert.ok(oldAccess);
    await peer.goto(WEB + '/admin');
    await peer.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    await origin.route('**/auth/browser/logout', async route => {
      const response = await route.fetch();
      assert.equal(response.status(), 204, 'Original real PG revocation must COMMIT');
      captured();
      await held;
      await route.fulfill({ response });
    });
    await origin.getByRole('button', { name: 'Menú de perfil' }).click();
    await origin.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await within(intercepted, 'held real logout HTTP 204');
    await peer.waitForFunction(async () => {
      const locks = await navigator.locks.query();
      return locks.pending.some(lock => lock.name === 'fitflow-auth-cookie-write');
    });
    const operation = await peer.evaluate(
      () => sessionStorage.getItem('fitflow_logout_operation'));
    assert.ok(operation, 'Both tabs must refer to the same pending logout');
    free();
    await origin.waitForFunction(() =>
      sessionStorage.getItem('fitflow_logout_pending') === null);
    await peer.waitForFunction(() =>
      sessionStorage.getItem('fitflow_logout_pending') === null);
    const both = await Promise.all([origin, peer].map(page => page.evaluate(() => ({
      confirmed: localStorage.getItem('fitflow_logout_confirmed_operation'),
      epoch: localStorage.getItem('fitflow_browser_auth_epoch'),
      pending: sessionStorage.getItem('fitflow_logout_pending'),
      operation: sessionStorage.getItem('fitflow_logout_operation'),
    }))));
    for (const state of both) {
      assert.equal(state.confirmed, operation, 'Real 204 must persist exact nonsecret receipt');
      assert.equal(state.pending, null);
      assert.equal(state.operation, null);
      assert.ok(state.epoch.startsWith('logout-confirmed|') &&
        state.epoch.endsWith('|' + operation),
      'A later missing proof 401 must not downgrade confirmed status');
    }
    assert.equal(await peer.getByText(
      'La cookie de sesión ya no está disponible.', { exact: false }).count(), 0,
    'A peer must not show expired-unconfirmed after a real PG ACK');
    const revoked = await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + oldAccess },
    });
    assert.equal(revoked.status, 401, 'Original access family is revoked');
  } finally {
    free?.();
    await context.close();
  }
}



async function verifyDistinctPendingLogoutPreservesOriginalReceipt(browser) {
  // Force a distinct peer operation and a premature peer proof-loss signal
  // while a genuine origin HTTP204 is withheld. The signals are explicit
  // test instrumentation; only the actual signed backend response is an ACK.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const origin = await context.newPage();
  const peer = await context.newPage();
  let release;
  let markCaptured;
  const held = new Promise(resolve => { release = resolve; });
  const captured = new Promise(resolve => { markCaptured = resolve; });
  try {
    await login(origin, email);
    await origin.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const oldAccess = await activeAccessToken(origin);
    assert.ok(oldAccess);
    await peer.goto(WEB + '/admin');
    await peer.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    await origin.evaluate(() => {
      window.__ffConflictSignals = [];
      window.addEventListener('storage', event => {
        if (event.key === 'fitflow_browser_auth_epoch' && event.newValue) {
          window.__ffConflictSignals.push(event.newValue);
        }
      });
    });
    await origin.route('**/auth/browser/logout', async route => {
      const response = await route.fetch();
      assert.equal(response.status(), 204, 'Real PostgreSQL revocation must commit');
      markCaptured();
      await held;
      await route.fulfill({ response });
    });
    await origin.getByRole('button', { name: 'Menú de perfil' }).click();
    await origin.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await within(captured, 'withheld original PG logout ACK');
    const original = await origin.evaluate(() =>
      sessionStorage.getItem('fitflow_logout_operation'));
    assert.ok(original);
    const generation = (await runtimeSessionState(origin)).generation;

    // A matching but unconfirmed peer signal must not clear an in-flight
    // original before its own definitive response.
    await peer.evaluate(operation => {
      localStorage.setItem('fitflow_browser_auth_epoch',
        'logout-expired-unconfirmed|' + Date.now() + '|' + operation);
    }, original);
    await origin.waitForFunction(operation => window.__ffConflictSignals.some(value =>
      value.startsWith('logout-expired-unconfirmed|') && value.endsWith('|' + operation)), original);
    assert.equal(await origin.evaluate(() =>
      sessionStorage.getItem('fitflow_logout_operation')), original);

    // Deliberately introduce another operation ID as if two tab clicks raced.
    // Reload the peer with that pending identity so its real cookie-proof
    // recovery owns B, not the original A's queued task.
    const foreign = await peer.evaluate(() => {
      const operation = crypto.randomUUID();
      sessionStorage.setItem('fitflow_logout_pending', '1');
      sessionStorage.setItem('fitflow_logout_operation', operation);
      localStorage.setItem('fitflow_browser_auth_epoch',
        'logout-pending|' + Date.now() + '|' + operation);
      return operation;
    });
    assert.notEqual(foreign, original);
    await origin.waitForFunction(operation => window.__ffConflictSignals.some(value =>
      value.startsWith('logout-pending|') && value.endsWith('|' + operation)), foreign);
    assert.equal(await origin.evaluate(() =>
      sessionStorage.getItem('fitflow_logout_operation')), original,
      'Distinct peer pending must not replace the original operation');
    assert.equal((await runtimeSessionState(origin)).generation, generation,
      'Peer conflict must not invalidate the original in-flight receipt');
    await peer.reload();
    await peer.waitForFunction(operation =>
      sessionStorage.getItem('fitflow_logout_operation') === operation, foreign);
    await peer.waitForFunction(async () => (await navigator.locks.query()).pending.some(lock =>
      lock.name === 'fitflow-auth-cookie-write'));
    release();
    await origin.waitForFunction(() => sessionStorage.getItem('fitflow_logout_pending') === null);
    await peer.waitForFunction(() => sessionStorage.getItem('fitflow_logout_pending') === null);
    await origin.waitForFunction(operation => window.__ffConflictSignals.some(value =>
      value.startsWith('logout-expired-unconfirmed|') && value.endsWith('|' + operation)), foreign);
    const receipt = await origin.evaluate(() => ({
      last: localStorage.getItem('fitflow_logout_confirmed_operation'),
      history: JSON.parse(localStorage.getItem('fitflow_logout_confirmed_history') || '[]'),
    }));
    assert.equal(receipt.last, original, 'Only the exact original HTTP204 is confirmed');
    assert.ok(receipt.history.includes(original));
    assert.ok(!receipt.history.includes(foreign), 'No invented ACK for another operation');
    assert.equal(await origin.getByText('La cookie de sesión ya no está disponible.',
      { exact: false }).count(), 0, 'Foreign proof loss cannot downgrade the local receipt');
    await peer.getByText('La cookie de sesión ya no está disponible.', { exact: false }).waitFor();
    for (const page of [origin, peer]) {
      assert.equal(await activeAccessToken(page), null);
      assert.equal(await page.getByRole('button', { name: 'Ingresar' }).isDisabled(), false);
    }
    assert.equal((await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + oldAccess },
    })).status, 401, 'Original PostgreSQL family is revoked');
  } finally {
    release?.();
    await context.close();
  }
}


async function verifyNonCooperativeCookieWriterKeepsExclusiveLock(browser) {
  const context = await browser.newContext();
  const first = await context.newPage();
  const second = await context.newPage();
  let original;
  let successor;
  try {
    await first.goto(WEB + '/login');
    await second.goto(WEB + '/login');
    original = first.evaluate(async () => {
      const { withExclusiveBrowserCookie } = await import('/src/utils/browserCookieLock.ts');
      await withExclusiveBrowserCookie(async signal => {
        window.__ffNonCooperativeStarted = true;
        signal.addEventListener('abort', () => { window.__ffNonCooperativeAborted = true; });
        // Deliberately ignore AbortSignal for completion, no network mutation.
        await new Promise(resolve => { window.__ffReleaseNonCooperative = resolve; });
      });
      return 'ORIGINAL_SETTLED';
    });
    void original.catch(() => {});
    await first.waitForFunction(() => window.__ffNonCooperativeStarted === true);
    await first.waitForFunction(() => window.__ffNonCooperativeAborted === true,
      undefined, { timeout: 18000 });
    successor = second.evaluate(async () => {
      const { withExclusiveBrowserCookie } = await import('/src/utils/browserCookieLock.ts');
      await withExclusiveBrowserCookie(async () => {
        window.__ffSuccessorEntered = true;
      });
      return 'SUCCESSOR_SETTLED';
    });
    void successor.catch(() => {});
    await second.waitForFunction(async () => {
      const locks = await navigator.locks.query();
      return locks.held.some(lock => lock.name === 'fitflow-auth-cookie-write') &&
        locks.pending.some(lock => lock.name === 'fitflow-auth-cookie-write');
    });
    assert.equal(await second.evaluate(() => !!window.__ffSuccessorEntered), false,
      'Cancellation budget cannot force-release a noncooperative original writer');
    await first.evaluate(() => window.__ffReleaseNonCooperative());
    assert.equal(await within(original, 'original cookie writer settlement'), 'ORIGINAL_SETTLED');
    assert.equal(await within(successor, 'subsequent exclusive writer'), 'SUCCESSOR_SETTLED');
    assert.equal(await second.evaluate(() => window.__ffSuccessorEntered), true);
  } finally {
    await first.evaluate(() => window.__ffReleaseNonCooperative?.()).catch(() => {});
    await context.close();
    await Promise.allSettled([original, successor].filter(Boolean));
  }
}

async function verifyNon204LogoutCannotInventAck(browser) {
  // Axios considers all 2xx successful. Neither 200 nor 202 is a durable
  // server revocation receipt. The old signed bearer must remain active.
  for (const bogusStatus of [200, 202]) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    try {
      await login(page, email);
      await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
      const oldAccess = await activeAccessToken(page);
      assert.ok(oldAccess);
      await page.route('**/auth/browser/logout', route =>
        route.fulfill({ status: bogusStatus, body: 'not-a-commit' }));
      await page.getByRole('button', { name: 'Menú de perfil' }).click();
      await page.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
      await page.waitForURL('**/login');
      await page.getByRole('button', { name: 'Reintentar salida segura' }).waitFor();
      assert.equal(await page.evaluate(
        () => sessionStorage.getItem('fitflow_logout_pending')), '1');
      assert.equal(await page.evaluate(
        () => localStorage.getItem('fitflow_logout_confirmed_operation')), null,
      'A non-204 response must not record a false ACK');
      assert.equal(await page.getByRole('button', { name: 'Ingresar' }).isDisabled(), true);
      assert.equal((await fetch(API + '/auth/me', {
        headers: { Authorization: 'Bearer ' + oldAccess },
      })).status, 200, 'A mocked non-204 never revokes the PG family');
      await page.unroute('**/auth/browser/logout');
      await page.getByRole('button', { name: 'Reintentar salida segura' }).click();
      await page.waitForFunction(
        () => sessionStorage.getItem('fitflow_logout_pending') === null);
      assert.ok(await page.evaluate(
        () => localStorage.getItem('fitflow_logout_confirmed_operation')),
      'Only the later real PG 204 may record a confirmed operation');
      assert.equal((await fetch(API + '/auth/me', {
        headers: { Authorization: 'Bearer ' + oldAccess },
      })).status, 401, 'Real retry must revoke the original family');
    } finally {
      await context.close();
    }
  }
}


async function verifyQueuedLoginHonorsRealProviderLogoutBroadcast(browser) {
  // Unlike the synthetic epoch test, only mounted AuthProvider may broadcast.
  // Hold the cookie Web Lock, queue a login, then trigger real UI logout.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const owner = await context.newPage();
  const contender = await context.newPage();
  const holder = await context.newPage();
  let freeHeld;
  try {
    await login(owner, email);
    await owner.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const oldAccess = await activeAccessToken(owner);
    assert.ok(oldAccess);
    await contender.goto(WEB + '/login');
    await contender.getByLabel('Email').waitFor();
    await holder.goto(WEB + '/login');
    await contender.evaluate(() => {
      window.__ffRealAuthBroadcasts = [];
      window.addEventListener('storage', event => {
        if (event.key === 'fitflow_browser_auth_epoch' && event.newValue) {
          window.__ffRealAuthBroadcasts.push(event.newValue);
        }
      });
    });
    const held = holder.evaluate(async () => {
      await navigator.locks.request('fitflow-auth-cookie-write', async () => {
        window.__ffRealLockHeld = true;
        await new Promise(resolve => { window.__ffReleaseRealLock = resolve; });
      });
    });
    freeHeld = () => holder.evaluate(() => window.__ffReleaseRealLock?.());
    await holder.waitForFunction(() => window.__ffRealLockHeld === true);
    let loginPosts = 0;
    contender.on('request', request => {
      if (request.method() === 'POST' && request.url() === API + '/auth/browser/token') {
        loginPosts++;
      }
    });
    await contender.getByLabel('Email').fill(email);
    await contender.getByLabel('Contraseña').fill(password);
    await contender.getByRole('button', { name: 'Ingresar' }).click();
    await contender.waitForFunction(async () =>
      (await navigator.locks.query()).pending.some(lock =>
        lock.name === 'fitflow-auth-cookie-write'));
    // The real React handler emits logout-pending while both real HTTP writers
    // remain queued. No direct API logout or synthetic storage epoch is used.
    await owner.getByRole('button', { name: 'Menú de perfil' }).click();
    await owner.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await contender.waitForFunction(() =>
      window.__ffRealAuthBroadcasts.some(value => value.startsWith('logout-pending|')));
    await freeHeld();
    await held;
    await owner.waitForURL('**/login');
    await owner.waitForFunction(() =>
      sessionStorage.getItem('fitflow_logout_pending') === null);
    await contender.waitForFunction(() =>
      window.__ffRealAuthBroadcasts.some(value => value.startsWith('logout-confirmed|')));
    assert.equal(loginPosts, 0,
      'The real logout-pending broadcast must stop an already queued login POST');
    assert.equal(new URL(contender.url()).pathname, '/login');
    assert.equal(await activeAccessToken(contender), null);
    assert.equal((await context.cookies()).some(
      cookie => cookie.name === 'fitflow_browser_refresh'), false);
    const response = await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + oldAccess },
    });
    assert.equal(response.status, 401,
      'Real React logout must revoke old signed PG family');
  } finally {
    await freeHeld?.().catch(() => {});
    await context.close();
  }
}

async function verifySameTabConcurrentLogoutRetriesJoinOriginal(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  let release;
  let notify;
  let logoutPosts = 0;
  const hold = new Promise(resolve => { release = resolve; });
  const intercepted = new Promise(resolve => { notify = resolve; });
  try {
    await login(page, email);
    await page.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    await page.route('**/auth/browser/logout', async route => {
      logoutPosts++;
      const response = await route.fetch();
      assert.equal(response.status(), 204);
      notify();
      await hold;
      await route.fulfill({ response });
    });
    await page.getByRole('button', { name: 'Menú de perfil' }).click();
    await page.getByRole('menuitem', { name: 'Cerrar Sesión' }).click();
    await within(intercepted, 'held real PG logout response');
    await page.waitForURL('**/login');
    const retry = page.getByRole('button', { name: 'Reintentar salida segura' });
    await retry.waitFor();
    await retry.click();
    await retry.click();
    release();
    await page.waitForFunction(() => sessionStorage.getItem('fitflow_logout_pending') === null);
    assert.equal(logoutPosts, 1, 'Manual retries must join the original request');
    assert.equal(await page.getByRole('button', { name: 'Ingresar' }).isDisabled(), false);
    assert.equal(await page.getByText('La cookie de sesión ya no está disponible.', { exact: false }).count(), 0,
      'A proven 204 cannot be overwritten by an expired-unconfirmed retry');
  } finally {
    release?.();
    await context.close();
  }
}

async function verifyRefreshReadsCsrfAfterQueuedCookieLock(browser) {
  // An external API request rotates the shared cookie while a tab is
  // queued on the Web Lock. Refresh MUST read the latest signed proof.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const first = await context.newPage();
  const second = await context.newPage();
  try {
    await login(first, email);
    await first.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    await second.goto(WEB + '/admin');
    await second.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    const beforeProof = await context.request.get(API + '/auth/browser/logout-proof', {
      headers: { Origin: WEB },
    });
    assert.equal(beforeProof.status(), 200);
    const originalCsrf = (await beforeProof.json()).csrf_token;
    const held = first.evaluate(async () => {
      await navigator.locks.request('fitflow-auth-cookie-write', async () => {
        window.__fitflowHeldLock = true;
        await new Promise(resolve => { window.__fitflowReleaseLock = resolve; });
      });
    });
    await first.waitForFunction(() => window.__fitflowHeldLock === true);
    const queued = second.evaluate(async () => {
      const service = (await import('/src/services/classService.ts')).default;
      return service.refreshBrowserSession();
    });
    await second.waitForFunction(async () => {
      const state = await navigator.locks.query();
      return state.pending.some(lock => lock.name === 'fitflow-auth-cookie-write');
    });
    try {
      const logout = await context.request.post(API + '/auth/browser/logout', {
        headers: { Origin: WEB, 'X-CSRF-Token': originalCsrf },
      });
      assert.equal(logout.status(), 204);
      const replacement = await context.request.post(API + '/auth/browser/token', {
        headers: { Origin: WEB },
        form: { username: email, password },
      });
      assert.equal(replacement.status(), 200);
    } finally {
      await first.evaluate(() => window.__fitflowReleaseLock());
    }
    await held;
    const refreshed = await within(queued, 'post-lock refresh of rotated cookie');
    assert.ok(refreshed.access_token, 'Refresh must return access for replacement family');
    assert.notEqual(refreshed.csrf_token, originalCsrf,
      'Refresh must read the new cookie-bound proof within the acquired lock');
  } finally {
    await first.evaluate(() => window.__fitflowReleaseLock?.()).catch(() => {});
    await context.close();
  }
}

async function verifyStalledProofReleasesCookieLock(browser) {
  // Real two-tab liveness test: proof GET intentionally never answers until
  // its requester aborts. The second tab must eventually acquire the lock.
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const first = await context.newPage();
  const second = await context.newPage();
  let releaseBlockedProof;
  let markIntercepted;
  const gate = new Promise(resolve => { releaseBlockedProof = resolve; });
  const intercepted = new Promise(resolve => { markIntercepted = resolve; });
  try {
    await login(first, email);
    await first.getByRole('heading', { name: 'Panel de administración' }).waitFor();
    await second.goto(WEB + '/login');
    await second.getByLabel('Email').fill(email);
    await second.getByLabel('Contraseña').fill(password);

    await first.route('**/auth/browser/logout-proof', async route => {
      markIntercepted();
      await gate;
      await route.abort().catch(() => {});
    });
    const slowRefresh = first.evaluate(async () => {
      const client = (await import('/src/services/classService.ts')).default;
      try {
        await client.refreshBrowserSession();
        return 'UNEXPECTED_SUCCESS';
      } catch {
        return 'ABORTED';
      }
    });
    await within(intercepted, 'stalled csrf proof intercept');
    const startedAt = Date.now();
    const denied = second.waitForResponse(response =>
      response.url() === API + '/auth/browser/token' && response.status() === 409);
    await second.getByRole('button', { name: 'Ingresar' }).click();
    const result = await within(slowRefresh, 'abort of stalled auth lock', 18000);
    assert.equal(result, 'ABORTED');
    await within(denied, 'second tab released after auth lock budget', 18000);
    assert.ok(Date.now() - startedAt < 18000,
      'Auth Web Lock must release before bounded browser test deadline');
  } finally {
    releaseBlockedProof?.();
    await context.close();
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
    const signedToken = await activeAccessToken(page);
    assert.ok(signedToken, 'Browser must hold signed access only in memory');
    assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), null);
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
    assert.ok(await activeAccessToken(page), 'HttpOnly cookie should rehydrate a signed access');
    assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), null);
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
    await loginWithNewSignedSession(page);
    const successorToken = await activeAccessToken(page);
    assert.ok(successorToken && successorToken !== signedToken,
      'Durable relogin must issue a new SID, never replay a revoked SID');
    const newGeneration = (await runtimeSessionState(page)).generation;
    assert.ok(newGeneration > loggedOutGeneration,
      'Same-user re-login must have a distinct generation');
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
    assert.ok((await activeAccessToken(page)) === successorToken,
      'Old 401 must not log out a later session generation');
    assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), null);
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
    const firstSignedToken = await activeAccessToken(page);
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

    // The legacy test originally attempted to overwrite an ACTIVE HttpOnly
    // family. That is now correctly blocked (HTTP 409). Revoke the first
    // disposable family via the exact signed refresh before re-login; hold
    // the old /auth/me responses so the stale-401 race is still exercised.
    // Use real browser logout: PG commits and server clears HttpOnly
    // refresh cookie. A direct API /session/logout revokes PG but deliberately
    // leaves a cookie that the browser-login guard must not overwrite.
    const oldFamilyCookie = (await context.cookies()).find(
      (cookie) => cookie.name === 'fitflow_browser_refresh');
    assert.ok(oldFamilyCookie && oldFamilyCookie.httpOnly);
    const proof = await context.request.get(API + '/auth/browser/session', {
      headers: { Origin: WEB },
    });
    assert.equal(proof.status(), 200, 'Old family must still be valid');
    const { csrf_token: oldCsrf } = await proof.json();
    const durableRevoke = await context.request.post(API + '/auth/browser/logout', {
      headers: { Origin: WEB, 'X-CSRF-Token': oldCsrf },
    });
    assert.equal(durableRevoke.status(), 204,
      'Browser logout must COMMIT and clear the old cookie');
    assert.equal((await context.cookies()).some(
      (cookie) => cookie.name === 'fitflow_browser_refresh'), false,
      'No signed refresh cookie may be replaced before confirmed logout');
    await page.evaluate(() => {
      history.pushState({}, '', '/login');
      dispatchEvent(new PopStateEvent('popstate'));
    });
    await page.getByRole('heading', { name: 'Iniciar Sesión' }).waitFor();
    await loginWithNewSignedSession(page);
    const secondSignedToken = await activeAccessToken(page);
    assert.ok(secondSignedToken && secondSignedToken !== firstSignedToken,
      'Same user relogin must register a new signed session family');
    const newState = await runtimeSessionState(page);
    assert.ok(newState.generation >= 2, 'New same-user login must advance auth generation');
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
    assert.ok((await activeAccessToken(page)) === secondSignedToken,
      'Old delayed 401 cannot revoke newer session UX');
    assert.equal(await page.evaluate(() => localStorage.getItem('access_token')), null);
    assert.equal((await runtimeSessionState(page)).generation, newState.generation,
      'Old delivered identity 401 must not invalidate the newer same-user login');
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
    await verifySameTabRefreshCannotRestoreBearerDuringLogout(browser);
    await verifyPendingLogoutCannotBeSilentlyReplaced(browser);
    await verifyExpiredLogoutProofUnblocksWithoutFalseAck(browser);
    await verifyCrossTabCookieSynchronizationAndReplacementGuard(browser);
    await verifySurvivingTabRecoversOrphanedLogout(browser);
    await verifyCrossTabLogoutAckDominatesQueuedMissingProof(browser);
    await verifyDistinctPendingLogoutPreservesOriginalReceipt(browser);
    await verifyEarlierRealLogoutReceiptSurvivesLaterConfirmedFamily(browser);
    await verifyNon204LogoutCannotInventAck(browser);
    await verifyLateLoginResponseRejectedAfterCrossTabLogout(browser);
    await verifyQueuedLoginCannotResurrectAfterRealLogout(browser);
    await verifyQueuedLoginHonorsRealProviderLogoutBroadcast(browser);
    await verifySameTabConcurrentLogoutRetriesJoinOriginal(browser);
    await verifyRefreshReadsCsrfAfterQueuedCookieLock(browser);
    await verifyStalledProofReleasesCookieLock(browser);
    await verifyNonCooperativeCookieWriterKeepsExclusiveLock(browser);
    await verifyRapidReLoginAndStale401(browser);
    await verifyDelayedIdentityAcrossSameTokenReLogin(browser);
    await qualifySyntheticFailureDiagnostic(browser);
    console.log('ADMIN_SIGNED_E2E_PASS: JWT login, backend identity, real data, privacy, 390/1280, role, expired, anonymous, logout, stale session races');
  } finally {
    await browser.close();
  }
}

run().catch((error) => { console.error(error.stack || error.message); process.exitCode = 1; });
