const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const root = path.join(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');

test('all login helpers use the mounted /auth/token route', () => {
  const api = read('src/services/api.ts');
  const service = read('src/services/classService.ts');
  const loginPage = read('src/pages/LoginPage.tsx');
  const router = read('../backend/app/routers/auth.py');
  assert.match(router, /APIRouter\(prefix="\/auth"/);
  assert.match(router, /@router\.post\("\/token"/);
  assert.match(api, /apiClient\.post\('\/auth\/token',\s*formData/);
  assert.match(service, /apiClient\.post<TokenResponse>\('\/auth\/token',\s*formData/);
  assert.match(loginPage, /classService\.login\(credentials\)/);
  assert.doesNotMatch(api + service, /['"]\/login\/token['"]/);
});


test('IR005 browser auth contract keeps refresh for server logout and verifies /auth/me', () => {
  const provider = read('src/context/AuthProvider.tsx');
  const login = read('src/pages/LoginPage.tsx');
  const navbar = read('src/components/layout/Navbar.tsx');
  const admin = read('src/components/admin/layout/AdminNavBar.tsx');
  const types = read('src/types/index.ts');
  assert.match(types, /refresh_token:\s*string/);
  assert.match(login, /await login\(pair\)/);
  assert.match(provider, /sessionStorage\.setItem\(REFRESH_KEY, pair\.refresh_token\)/);
  assert.match(provider, /apiClient\.post\("\/auth\/logout", \{ refresh_token: refresh \}/);
  assert.match(provider, /get<User>\("\/auth\/me"/);
  assert.match(provider, /claim\.exp <= Date\.now\(\) \/ 1000/);
  assert.match(provider, /localStorage\.removeItem\("access_token"\)/);
  assert.doesNotMatch(provider, /localStorage\.setItem\(.*refresh/);
  assert.match(navbar, /const revoked = await logout\(\)/);
  assert.match(admin, /const revoked = await logout\(\)/);
  assert.match(navbar, /if \(!revoked\)/);
  assert.match(admin, /if \(!revoked\)/);
});

test('IR005 mounted routes use the canonical teacher/front_desk roles without loops', () => {
  const ts = require('typescript');
  const vm = require('node:vm');
  const routes = read('src/utils/authRoutes.ts');
  const js = ts.transpileModule(routes, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const roles = { ADMIN: 'admin', CLIENT: 'client', TEACHER: 'teacher', FRONT_DESK: 'front_desk' };
  const fake = { exports: {} };
  vm.runInNewContext(js, {
    exports: fake.exports, module: fake,
    require: () => ({ UserRole: roles }),
  });
  const destination = fake.exports.roleDestination;
  assert.equal(destination(roles.ADMIN), '/admin');
  assert.equal(destination(roles.CLIENT), '/home');
  assert.equal(destination(roles.TEACHER), '/home');
  assert.equal(destination(roles.FRONT_DESK), '/front-desk');
  assert.equal(destination('unknown'), '/landing');
  const router = read('src/routes/AppRouter.tsx');
  const root = read('src/components/auth/RootAuthGuard.tsx');
  const provider = read('src/context/AuthProvider.tsx');
  assert.match(router, /UserRole\.TEACHER/);
  assert.match(router, /UserRole\.FRONT_DESK/);
  assert.match(root, /roleDestination\(userRole\)/);
  assert.match(provider, /userRole === "teacher"/);
  assert.doesNotMatch(router, /UserRole\.TRAINER/);
});
