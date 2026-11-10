const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const filename = path.resolve(__dirname, '../src/utils/identityFailurePolicy.ts');
const output = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
}).outputText;
const mod = { exports: {} };
vm.runInNewContext(output, {
  module: mod, exports: mod.exports,
  require: name => {
    if (name === 'axios') return { __esModule: true, default: {
      isAxiosError: error => error?.isAxiosError === true,
    } };
    throw Error('Unexpected import ' + name);
  },
});
const check = mod.exports.isRecoverableIdentityFailure;
test('only temporary network/HTTP identity failures allow local session recovery', () => {
  const error = status => ({ isAxiosError: true, response: status === undefined ? undefined : { status } });
  for (const code of [undefined, 429, 500, 502, 503, 504]) {
    assert.equal(check(error(code)), true, String(code));
  }
  for (const code of [400, 401, 403, 404, 422]) {
    assert.equal(check(error(code)), false, String(code));
  }
  assert.equal(check(new Error('Mismatched identity')), false);
  assert.equal(check(null), false);
});
