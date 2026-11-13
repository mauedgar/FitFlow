const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const utilPath = path.resolve(__dirname, '../src/utils/verifiedRoleDestination.ts');
const routerPath = path.resolve(__dirname, '../src/routes/AppRouter.tsx');
const rootPath = path.resolve(__dirname, '../src/components/auth/RootAuthGuard.tsx');
const loginPath = path.resolve(__dirname, '../src/pages/LoginPage.tsx');
const pagePath = path.resolve(__dirname, '../src/pages/TeacherLandingPage.tsx');
const source = fs.readFileSync(utilPath, 'utf8');
const UserRole = { ADMIN: 'admin', FRONT_DESK: 'front_desk', TEACHER: 'teacher', CLIENT: 'client', TRAINER: 'trainer' };
const transpiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  reportDiagnostics: true,
});
assert.equal(transpiled.diagnostics?.filter(d => d.category === ts.DiagnosticCategory.Error).length || 0, 0);
const moduleRecord = { exports: {} };
vm.runInNewContext(transpiled.outputText, {
  module: moduleRecord, exports: moduleRecord.exports,
  require: name => {
    if (name === '../types') return { UserRole };
    throw new Error('Unexpected import ' + name);
  },
});
const destination = moduleRecord.exports.verifiedRoleDestination;

test('backend-verified role routes to its own permitted landing', () => {
  assert.equal(destination(UserRole.ADMIN), '/admin');
  assert.equal(destination(UserRole.FRONT_DESK), '/front-desk');
  assert.equal(destination(UserRole.TEACHER), '/teacher');
  assert.equal(destination(UserRole.CLIENT), '/home');
  assert.equal(destination(UserRole.TRAINER), '/landing');
});

test('unknown authenticated role cannot trigger redirect loop or gain privileges', () => {
  assert.equal(destination('unknown'), '/landing');
  assert.notEqual(destination('unknown'), '/admin');
});

test('root and post-login navigation share exactly the verified role mapping', () => {
  const root = fs.readFileSync(rootPath, 'utf8');
  const login = fs.readFileSync(loginPath, 'utf8');
  assert.match(root, /verifiedRoleDestination\(userRole\)/);
  assert.match(login, /verifiedRoleDestination\(currentUser\.role\)/);
  assert.doesNotMatch(login, /jwtDecode/);
});

test('teacher entry has a teacher-only guard and does not grant admin/front desk access', () => {
  const router = fs.readFileSync(routerPath, 'utf8');
  const page = fs.readFileSync(pagePath, 'utf8');
  assert.match(router, /allowedRoles=\{\[UserRole\.TEACHER\]\}/);
  assert.match(router, /allowedRoles=\{\[UserRole\.CLIENT\]\}/);
  assert.doesNotMatch(router, /allowedRoles=\{\[UserRole\.CLIENT, UserRole\.TRAINER\]\}/);
  assert.match(router, /path="teacher" element=\{<TeacherLandingPage \/>\}/);
  assert.match(router, /allowedRoles=\{\[UserRole\.ADMIN, UserRole\.FRONT_DESK\]\}/);
  assert.match(page, /Esta vista no habilita esas operaciones/);
});

test('trainer state cannot be derived from a noncanonical legacy role alias', () => {
  const provider = fs.readFileSync(path.resolve(__dirname, '../src/context/AuthProvider.tsx'), 'utf8');
  assert.match(provider, /const isTrainer = userRole === "teacher";/);
  assert.doesNotMatch(provider, /userRole === "teacher" \|\| userRole === "trainer"/);
});

