const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');
const vm = require('node:vm');

const frontend = path.join(__dirname, '..');
const helperPath = path.join(frontend, 'src', 'utils', 'registrationErrors.ts');
const helperSource = fs.readFileSync(helperPath, 'utf8');
const compiled = ts.transpileModule(helperSource, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const moduleShim = { exports: {} };
vm.runInNewContext(compiled, { exports: moduleShim.exports, module: moduleShim }, {
  filename: helperPath,
});
const { registrationErrorMessage, PASSWORD_POLICY_MESSAGE } = moduleShim.exports;

test('422 password validation shows an actionable UTF-8 byte policy, not object text', () => {
  const detail = [{ loc: ['body', 'password'], msg: 'Value error' }];
  assert.equal(registrationErrorMessage(422, detail), PASSWORD_POLICY_MESSAGE);
  assert.match(PASSWORD_POLICY_MESSAGE, /72 bytes UTF-8/);
  assert.match(PASSWORD_POLICY_MESSAGE, /NUL/);
  assert.doesNotMatch(registrationErrorMessage(422, detail), /object Object/);
});

test('other 422 validation is generic and 400 string detail is preserved', () => {
  assert.equal(registrationErrorMessage(422, [{ loc: ['body', 'email'] }]),
    'Revisá el nombre, apellido, correo y contraseña ingresados.');
  assert.equal(registrationErrorMessage(400, 'El email ya está registrado.'),
    'El email ya está registrado.');
  assert.equal(registrationErrorMessage(500, { detail: 'internal' }),
    'Error al registrar la cuenta.');
});

test('registration client consumes 422 helper and page displays byte-boundary hint', () => {
  const service = fs.readFileSync(path.join(frontend, 'src', 'services', 'api.ts'), 'utf8');
  const page = fs.readFileSync(path.join(frontend, 'src', 'pages', 'RegisterPage.tsx'), 'utf8');
  assert.match(service, /registrationErrorMessage\(error\.response\.status,\s*error\.response\.data\?\.detail\)/);
  assert.match(page, /PASSWORD_POLICY_MESSAGE/);
  assert.match(service, /'\/users\/register-client'/);
  assert.match(service, /first_name: firstName/);
  assert.match(service, /last_name: lastName/);
  assert.doesNotMatch(page, /console\.(log|error|debug|warn|info)\s*\(/);
});
