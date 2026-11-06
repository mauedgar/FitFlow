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
    await page.getByRole('link', { name: 'Profesores' }).focus();
    await page.keyboard.press('Enter');
    await page.getByRole('heading', { name: 'Profesores' }).waitFor();
    await page.getByText('Profesora Sintética', { exact: true }).filter({ visible: true }).first().waitFor();
    assert.equal(await page.getByText('20999999999').count(), 0, 'Teacher CUIL must not appear');
    await page.getByRole('button', { name: 'Menú', exact: true }).click();
    await page.getByRole('link', { name: 'Clases' }).click();
    await page.getByRole('heading', { name: 'Clases', exact: true }).waitFor();
    await page.getByText('Clase Sintética E2E', { exact: true }).filter({ visible: true }).first().waitFor();
    await page.setViewportSize({ width: 1280, height: 800 });
    const widthDesktop = await page.evaluate(() => [document.documentElement.clientWidth, document.documentElement.scrollWidth]);
    assert.equal(widthDesktop[0], 1280);
    assert.ok(widthDesktop[1] <= 1280, 'ADMIN desktop must not overflow');
    await page.getByText(email).first().waitFor();
    await page.getByRole('link', { name: 'Clientes' }).click();
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
    console.log('ADMIN_SIGNED_E2E_PASS: JWT login, backend identity, real data, privacy, 390/1280, role, expired, anonymous, logout');
  } finally {
    await browser.close();
  }
}

run().catch((error) => { console.error(error.stack || error.message); process.exitCode = 1; });
