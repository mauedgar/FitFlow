/* Synthetic-only Chrome: real registration -> signed login -> /clients/me. */
const assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const { chromium } = require('playwright');

const WEB = 'http://127.0.0.1:5173';
const API = 'http://127.0.0.1:8000/api/v1';
const password = 'FitFlow-Disposable-Signup-Only-42';
const fullName = 'Ana María Prueba';

async function fillRegistration(page, name, email) {
  await page.goto(WEB + '/register');
  await page.getByRole('heading', { name: 'Crear Cuenta' }).waitFor();
  await page.getByLabel('Nombre y apellido').fill(name);
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

    await fillRegistration(page, fullName, email);
    const created = registrationResponse(page);
    await page.getByRole('button', { name: 'Registrarse' }).click();
    assert.equal((await created).status(), 201, 'Real client registration must create account + profile');
    await page.waitForURL('**/login', { timeout: 20000 });

    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Contraseña').fill(password);
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
        hasStoredToken: await page.evaluate(() => Boolean(localStorage.getItem('access_token'))),
      };
      console.error('CLIENT_SIGNUP_NAVIGATION_DIAGNOSTIC', JSON.stringify(browserState));
      throw error;
    }
    const signed = await page.evaluate(() => localStorage.getItem('access_token'));
    assert.ok(signed, 'Login must retain a real signed JWT');
    const me = await fetch(API + '/clients/me', {
      headers: { Authorization: 'Bearer ' + signed },
    });
    assert.equal(me.status, 200, 'New client must own an accessible profile');
    const profile = await me.json();
    assert.equal(profile.email, email);
    assert.equal(profile.full_name, fullName);
    assert.ok(profile.id);

    const duplicate = await context.newPage();
    await fillRegistration(duplicate, fullName, email);
    const duplicateRequest = registrationResponse(duplicate);
    await duplicate.getByRole('button', { name: 'Registrarse' }).click();
    assert.equal((await duplicateRequest).status(), 400, 'Duplicate email must be rejected');
    assert.equal(new URL(duplicate.url()).pathname, '/register');

    const invalid = await context.newPage();
    await fillRegistration(invalid, 'Ana ' + 'X'.repeat(201), 'fitflow-invalid-' + randomUUID() + '@example.com');
    const rejectedRequest = registrationResponse(invalid);
    await invalid.getByRole('button', { name: 'Registrarse' }).click();
    assert.equal((await rejectedRequest).status(), 422, 'Invalid full name must be rejected');
    await invalid.getByText('Error en el registro').waitFor({ timeout: 10000 });
    assert.equal(new URL(invalid.url()).pathname, '/register');
    console.log('CLIENT_SIGNUP_BROWSER_E2E_PASS: register, signed login, client profile, 400 duplicate, 422 validation');
    await context.close();
  } finally {
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
