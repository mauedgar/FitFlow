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
test('ADMIN guard rejects locally expired JWTs and isolates stale HTTP 401 from different accounts', () => {
  assert.match(gate, /jwtDecode<TokenPayload>/);
  assert.match(gate, /payload\.role !== UserRole\.ADMIN/);
  assert.match(gate, /payload\.exp <= 0/);
  assert.match(gate, /expiresAt > Date\.now\(\)/);
  assert.match(gate, /window\.setTimeout\(recheck/);
  assert.match(gate, /window\.clearTimeout\(timeoutId\)/);
  assert.match(gate, /error\.response\?\.status === 401/);
  assert.match(gate, /sent === `Bearer/);
  assert.match(gate, /localStorage\.getItem\('access_token'\) === token/);
  assert.match(gate, /<Navigate to="\/login" replace \/>/);
  assert.match(routes, /<AdminSessionGate><AdminLayout \/><\/AdminSessionGate>/);
});
