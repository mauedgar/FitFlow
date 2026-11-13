const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const read = (path) => fs.readFileSync(path, 'utf8');
const dashboard = read('src/pages/admin/AdminDashboardPage.tsx');
const teachers = read('src/pages/admin/TeachersPage.tsx');
const classes = read('src/pages/admin/CrudClassesPage.tsx');
const api = read('src/services/adminReadService.ts');
const routes = read('src/routes/AppRouter.tsx');
const sidebar = read('src/components/admin/layout/AdminSidebar.tsx');
const nav = read('src/components/admin/layout/AdminNavBar.tsx');

test('ADMIN dashboard uses only live API-backed read projections and account-isolated queries', () => {
  for (const statement of [
    "getAdminClients(signal)", "getAdminTeacherSummaries(signal)", "getAdminGymClassSummaries(signal)",
    "currentUser?.email", "enabled: adminEnabled", "No disponible",
    "No es el total general", "No disponible",
  ]) {
    if (statement === "No es el total general") continue;
    assert.ok(dashboard.includes(statement), `dashboard missing ${statement}`);
  }
  assert.match(dashboard, /no es el total general/i);
  assert.match(dashboard, /hasError/);
  assert.match(dashboard, /Actualizar datos/);
  assert.doesNotMatch(dashboard, /clientsData|mockData|toaster\.create/);
});

test('ADMIN public teachers and classes consume safe API DTOs only', () => {
  assert.match(api, /'\/teachers\/public'/);
  assert.match(api, /'\/gym-classes\/public'/);
  assert.match(api, /signal/);
  assert.doesNotMatch(api, /cuil|\/teachers\/'\s*,/i);
  assert.match(teachers, /getAdminTeacherSummaries\(signal\)/);
  assert.match(classes, /getAdminGymClassSummaries\(signal\)/);
  for (const page of [teachers, classes]) {
    assert.match(page, /currentUser\?\.email/);
    assert.match(page, /enabled: currentUser\?\.role === 'admin'/);
    assert.match(page, /role="status"/);
    assert.match(page, /role="alert"/);
    assert.match(page, /onClick=\{\(\) => void refetch\(\)\}/);
    assert.match(page, /<SimpleGrid/);
    assert.match(page, /<Table\.Root/);
    assert.doesNotMatch(page, /clientsData|LuTrash2|LuPencil|handleAdd|handleDelete|handleEdit/);
  }
});

test('ADMIN sections are routed and navigable on desktop and mobile, with no fake class CRUD', () => {
  assert.match(routes, /<Route path="classes" element=\{<CrudClassesPage \/>\} \/>/);
  assert.match(routes, /<Route path="CruClasses" element=\{<Navigate to="\/admin\/classes" replace \/>\} \/>/);
  for (const file of [nav, sidebar]) {
    assert.match(file, /to: '\/admin\/classes'/);
    assert.match(file, /to: '\/admin\/teachers'/);
    assert.match(file, /to: '\/admin\/clients'/);
  }
  for (const url of ['/admin/clients', '/admin/teachers', '/admin/classes']) {
    assert.ok(dashboard.includes(url));
  }
});

const gate = read('src/components/admin/auth/AdminSessionGate.tsx');
const session = read('src/utils/adminSession.ts');
test('ADMIN guard rejects expired tokens and retires same-token stale interceptors', () => {
  assert.match(session, /jwtDecode<TokenPayload>/);
  assert.match(session, /payload\.role !== 'admin'/);
  assert.match(session, /payload\.exp <= 0/);
  assert.match(gate, /expiresAt > Date\.now\(\)/);
  assert.match(gate, /window\.setTimeout\(recheck/);
  assert.match(gate, /window\.clearTimeout\(timeoutId\)/);
  assert.match(gate, /error\.response\?\.status === 401/);
  assert.match(gate, /sessionActive = false/);
  assert.match(gate, /\[token, currentUser, sessionGeneration\]/);
  assert.match(gate, /logoutRef\.current\(\)\.catch/);
  assert.match(gate, /endSession\(\)/);
  assert.match(gate, /toaster\.create/);
  assert.match(gate, /shouldInvalidateCurrentAdminSession/);
  assert.match(gate, /sessionStorage\.getItem\('access_token'\)/);
  assert.match(gate, /<Navigate to="\/login" replace \/>/);
  assert.match(routes, /<AdminSessionGate><AdminLayout \/><\/AdminSessionGate>/);
});

test('ADMIN JWT expiry and role checks execute over synthetically encoded tokens', () => {
  const ts = require('typescript');
  const output = ts.transpileModule(session, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const exported = {};
  new Function('require', 'exports', output)(require, exported);
  const expiry = exported.adminTokenExpiryMs;
  const token = (claims) => [
    Buffer.from(JSON.stringify({ alg: 'none', typ: 'JWT' })).toString('base64url'),
    Buffer.from(JSON.stringify(claims)).toString('base64url'),
    '',
  ].join('.');
  assert.equal(expiry(token({ sub: 'synthetic@example.invalid', role: 'admin', exp: 1_800_000_000 })), 1_800_000_000_000);
  assert.equal(expiry(token({ sub: 'synthetic@example.invalid', role: 'client', exp: 1_800_000_000 })), null);
  assert.equal(expiry(token({ sub: 'synthetic@example.invalid', role: 'admin' })), null);
  assert.equal(expiry(token({ sub: 'synthetic@example.invalid', role: 'admin', exp: -1 })), null);
  assert.equal(expiry('not-a-jwt'), null);
});

test('admin read services execute safe HTTP projections and propagate AbortSignal', async () => {
  const ts = require('typescript');
  const serviceSource = read('src/services/adminReadService.ts');
  const output = ts.transpileModule(serviceSource, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const observed = [];
  const fakeApi = {
    get: async (url, options) => {
      observed.push({ url, signal: options.signal });
      return { data: url === '/teachers/public'
        ? [{ id: 'synthetic-t', full_name: 'Profesora Prueba' }]
        : [{ id: 'synthetic-c', name: 'Clase Prueba' }] };
    },
  };
  const exports = {};
  new Function('require', 'exports', output)(
    (name) => name === './api' ? { __esModule: true, default: fakeApi } : require(name),
    exports,
  );
  const controller = new AbortController();
  const teacherRows = await exports.getAdminTeacherSummaries(controller.signal);
  const classRows = await exports.getAdminGymClassSummaries(controller.signal);
  assert.equal(teacherRows[0].full_name, 'Profesora Prueba');
  assert.equal(classRows[0].name, 'Clase Prueba');
  assert.deepEqual(observed.map((x) => x.url), ['/teachers/public', '/gym-classes/public']);
  assert.ok(observed.every((x) => x.signal === controller.signal));
  fakeApi.get = (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(new Error('Synthetic request aborted')), { once: true });
  });
  const cancelled = new AbortController();
  const pending = exports.getAdminTeacherSummaries(cancelled.signal);
  cancelled.abort();
  await assert.rejects(pending, /Synthetic request aborted/);
});

test('dashboard unknown data must not become a fabricated zero', () => {
  assert.match(dashboard, /isError \|\| count === undefined \? 'No disponible'/);
  assert.doesNotMatch(dashboard, /count \?\? 0/);
});

test('session-generation mismatch rejects same-token stale 401 callbacks', () => {
  const ts = require('typescript');
  const mod = ts.transpileModule(session, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const exported = {};
  new Function('require', 'exports', mod)(require, exported);
  const check = exported.shouldInvalidateCurrentAdminSession;
  assert.equal(check(true, 4, 4, 'Bearer tok', 'tok', 'tok'), true);
  assert.equal(check(true, 4, 5, 'Bearer tok', 'tok', 'tok'), false);
  assert.equal(check(false, 4, 4, 'Bearer tok', 'tok', 'tok'), false);
  assert.equal(check(true, 4, 4, 'Bearer old', 'tok', 'tok'), false);
  assert.equal(check(true, 4, 4, 'Bearer tok', 'tok', 'other'), false);
});

test('auth entrypoints advance their epoch before notifying React context', () => {
  const hook = read('src/context/useAuth.tsx');
  assert.match(hook, /advanceAuthSessionGeneration\(\);\s*context\.login/);
  assert.match(hook, /advanceAuthSessionGeneration\(\);\s*return context\.logout/);
  assert.match(gate, /expectedGeneration !== getAuthSessionGeneration\(\)/);
  assert.match(gate, /sessionActive, expectedGeneration, getAuthSessionGeneration\(\)/);
  const ts = require('typescript');
  const source = read('src/utils/authSessionGeneration.ts');
  const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
  const mod = {};
  new Function('exports', js)(mod);
  assert.equal(mod.getAuthSessionGeneration(), 0);
  const before = mod.advanceAuthSessionGeneration();
  assert.equal(before, 1);
  assert.equal(mod.advanceAuthSessionGeneration(), 2);
  assert.equal(mod.getAuthSessionGeneration(), 2);
});
