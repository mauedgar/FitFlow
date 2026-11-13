/* Synthetic-only Chrome: real registration -> signed login -> /clients/me. */
const assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const { chromium } = require('playwright');

const WEB = 'http://127.0.0.1:5173';
const API = 'http://127.0.0.1:8000/api/v1';
const password = 'FitFlow-Disposable-Signup-Only-42';
const firstName = 'Ana María';
const lastName = 'de la Cruz';
const fullName = firstName + ' ' + lastName;

async function fillRegistration(page, given, family, email) {
  await page.goto(WEB + '/register');
  await page.getByRole('heading', { name: 'Crear Cuenta' }).waitFor();
  await page.getByLabel('Nombre(s)').fill(given);
  await page.getByLabel('Apellido(s)').fill(family);
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Contraseña', { exact: true }).fill(password);
  await page.getByLabel('Confirmar Contraseña').fill(password);
}

function registrationResponse(page) {
  return page.waitForResponse(
    (response) => response.url() === API + '/users/register-client'
      && response.request().method() === 'POST',
    { timeout: 20000 }
  );
}

async function run() {
  if (process.env.GITHUB_ACTIONS !== 'true'
      || process.env.FITFLOW_E2E_SYNTHETIC_ONLY !== '1'
      || process.env.ENV !== 'test'
      || process.env.TESTING !== 'true') {
    throw new Error('BLOCKED_PRECONDITION: disposable CI only');
  }
  const email = 'fitflow-signup-' + randomUUID() + '@example.com';
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();

    await fillRegistration(page, firstName, lastName, email);
    const created = registrationResponse(page);
    await page.getByRole('button', { name: 'Registrarse' }).click();
    assert.equal((await created).status(), 201, 'Real client registration must create account + profile');
    await page.waitForURL('**/login', { timeout: 20000 });
    // URL mutation precedes React's form replacement; wait for the login DOM.
    await page.getByRole('heading', { name: 'Iniciar Sesión' }).waitFor({ timeout: 20000 });

    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Contraseña', { exact: true }).fill(password);
    const tokenResponse = page.waitForResponse((response) => {
      const request = response.request();
      return response.url() === API + '/auth/token' && request.method() === 'POST';
    }, { timeout: 20000 });
    await page.getByRole('button', { name: 'Ingresar' }).click();
    const authResponse = await tokenResponse;
    assert.equal(authResponse.status(), 200,
      'Newly registered client must be able to authenticate through real /auth/token');

    try {
      await page.waitForURL('**/home', { timeout: 10000 });
    } catch (error) {
      const browserState = {
        pathname: new URL(page.url()).pathname,
        headings: await page.getByRole('heading').allTextContents(),
        alerts: await page.getByRole('alert').allTextContents(),
        hasStoredToken: await page.evaluate(() => Boolean(sessionStorage.getItem('access_token'))),
      };
      console.error('CLIENT_SIGNUP_NAVIGATION_DIAGNOSTIC', JSON.stringify(browserState));
      throw error;
    }
    const signed = await page.evaluate(() => sessionStorage.getItem('access_token'));
    assert.ok(signed, 'Login must retain a real signed JWT');
    const me = await fetch(API + '/clients/me', {
      headers: { Authorization: 'Bearer ' + signed },
    });
    assert.equal(me.status, 200, 'New client must own an accessible profile');
    const profile = await me.json();
    assert.equal(profile.email, email);
    assert.equal(profile.full_name, fullName);
    assert.ok(profile.id);

    // Bounded real-page failure: an isolated browser intercepts logout twice,
    // so the signed JWT remains live on the disposable backend. Never treat
    // local deauthorization or a frontend warning as server revocation.
    await page.setViewportSize({ width: 1280, height: 800 });
    let observedLogoutAttempts = 0;
    let resolveTwoFailures;
    let rejectTimer;
    const twoFailures = new Promise((resolve, reject) => {
      resolveTwoFailures = resolve;
      rejectTimer = setTimeout(
        () => reject(new Error('Did not observe two bounded 503 logout attempts')),
        15000
      );
    });
    await page.route('**/api/v1/auth/logout', async route => {
      observedLogoutAttempts += 1;
      await route.fulfill({
        status: 503, contentType: 'application/json',
        body: JSON.stringify({ detail: 'SYNTHETIC_LOGOUT_UNAVAILABLE' }),
      });
      if (observedLogoutAttempts === 2) {
        clearTimeout(rejectTimer);
        resolveTwoFailures();
      }
    });
    await page.getByRole('button', { name: 'Cerrar Sesión', exact: true }).click();
    await twoFailures;
    await page.waitForURL('**/login', { timeout: 10000 });
    const unconfirmedText = 'Cerraste la sesión local, pero no se confirmó su revocación en el servidor.';
    await page.getByText(unconfirmedText, { exact: false }).waitFor({ timeout: 10000 });
    assert.equal(observedLogoutAttempts, 2, 'Client sends exactly one bounded retry');
    assert.equal(await page.evaluate(() => sessionStorage.getItem('access_token')), null);
    assert.equal(await page.evaluate(() => sessionStorage.getItem('refresh_token')), null);
    assert.equal(
      await page.evaluate(() => sessionStorage.getItem('fitflow_logout_remote_unconfirmed')),
      '1', 'Only the non-secret status must survive after logout'
    );
    const backendStillAuthorized = await fetch(API + '/auth/me', {
      headers: { Authorization: 'Bearer ' + signed },
    });
    assert.equal(backendStillAuthorized.status, 200,
      'Synthetic offline logout cannot imply actual remote revocation');
    await page.reload();
    await page.getByText(unconfirmedText, { exact: false }).waitFor({ timeout: 10000 });
    assert.equal(await page.evaluate(() => sessionStorage.getItem('access_token')), null);
    assert.equal(await page.evaluate(() => sessionStorage.getItem('refresh_token')), null);
    await page.unroute('**/api/v1/auth/logout');
    console.log('CLIENT_LOGOUT_UNCONFIRMED_RELOAD_WARNING_PASS');

    // Independent browser context avoids inheriting the previous unconfirmed
    // warning. An HTTP 202 must NEVER be mistaken for logout's required 204.
    const unexpectedContext = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    try {
      const unexpected = await unexpectedContext.newPage();
      await unexpected.goto(WEB + '/login');
      await unexpected.getByLabel('Email', { exact: true }).fill(email);
      await unexpected.getByLabel('Contraseña', { exact: true }).fill(password);
      await unexpected.getByRole('button', { name: 'Ingresar' }).click();
      await unexpected.waitForURL('**/home', { timeout: 20000 });
      let unexpectedAckAttempts = 0;
      await unexpected.route('**/api/v1/auth/logout', route => {
        unexpectedAckAttempts += 1;
        return route.fulfill({
          status: 202,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'SYNTHETIC_NOT_YET_REVOKED' }),
        });
      });
      const unexpectedAck = unexpected.waitForResponse(response =>
        response.url() === API + '/auth/logout' && response.status() === 202,
      );
      await unexpected.getByRole('button', { name: 'Cerrar Sesión', exact: true }).click();
      await unexpectedAck;
      await unexpected.waitForURL('**/login', { timeout: 10000 });
      await unexpected.getByText(unconfirmedText, { exact: false }).waitFor();
      assert.equal(unexpectedAckAttempts, 1, 'HTTP 202 must not be retried or accepted as an ACK');
      assert.equal(
        await unexpected.evaluate(() => sessionStorage.getItem('fitflow_logout_remote_unconfirmed')),
        '1', 'Non-204 response cannot erase remote uncertainty'
      );
      assert.equal(await unexpected.evaluate(() => sessionStorage.getItem('access_token')), null);
      assert.equal(await unexpected.evaluate(() => sessionStorage.getItem('refresh_token')), null);
      console.log('CLIENT_LOGOUT_NON204_REJECTED_PASS');
    } finally {
      await unexpectedContext.close();
    }

    const duplicate = await context.newPage();
    await fillRegistration(duplicate, firstName, lastName, email);
    const duplicateRequest = registrationResponse(duplicate);
    await duplicate.getByRole('button', { name: 'Registrarse' }).click();
    assert.equal((await duplicateRequest).status(), 400, 'Duplicate email must be rejected');
    assert.equal(new URL(duplicate.url()).pathname, '/register');

    const invalid = await context.newPage();
    await fillRegistration(invalid, 'Ana', 'X'.repeat(201), 'fitflow-invalid-' + randomUUID() + '@example.com');
    const rejectedRequest = registrationResponse(invalid);
    await invalid.getByRole('button', { name: 'Registrarse' }).click();
    assert.equal((await rejectedRequest).status(), 422, 'Invalid full name must be rejected');
    await invalid.getByText('Error en el registro').waitFor({ timeout: 10000 });
    assert.equal(new URL(invalid.url()).pathname, '/register');
    // Real mounted registration page + Axios, with a synthetic disposable 503.
    // The server text must never be presented by the toaster/UI.
    const unavailable = await context.newPage();
    await fillRegistration(
      unavailable, firstName, lastName,
      'fitflow-upstream-' + randomUUID() + '@example.com'
    );
    const internalDetail = 'SYNTHETIC_PRIVATE_UPSTREAM_DIAGNOSTIC_DO_NOT_SHOW';
    await unavailable.route('**/api/v1/users/register-client', route => route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: internalDetail }),
    }));
    const serverError = registrationResponse(unavailable);
    await unavailable.getByRole('button', { name: 'Registrarse' }).click();
    assert.equal((await serverError).status(), 503,
      'Transient synthetic registration failure must reach the real Axios page');
    await unavailable.getByText('Error en el registro').waitFor({ timeout: 10000 });
    await unavailable.getByText('Error al registrar la cuenta.').waitFor({ timeout: 10000 });
    assert.equal(new URL(unavailable.url()).pathname, '/register');
    assert.equal(await unavailable.getByText(internalDetail).count(), 0,
      'A server diagnostic must not leak into registration UI');
    await unavailable.close();
    console.log('CLIENT_SIGNUP_BROWSER_503_PUBLIC_ERROR_PASS');

    console.log('CLIENT_SIGNUP_BROWSER_E2E_PASS: register, signed login, client profile, 400 duplicate, 422 validation, synthetic 503 public error');
    await context.close();
  } finally {
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
