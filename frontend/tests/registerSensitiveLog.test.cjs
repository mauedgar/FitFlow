const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');

test('Registration does not log sensitive form values', () => {
  const filename = path.join(__dirname, '..', 'src', 'pages', 'RegisterPage.tsx');
  const source = ts.createSourceFile(filename, fs.readFileSync(filename, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  function visit(node) {
    if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression) &&
        node.expression.expression.getText(source) === 'console' &&
        ['log','debug','info','warn','error'].includes(node.expression.name.text)) {
      const args = node.arguments.map(arg => arg.getText(source)).join(' ');
      assert.ok(!/\b(password|confirmPassword)\b/.test(args), 'passwords must not reach console');
      assert.ok(!args.includes('Datos de Registro'), 'registration payload must not be logged');
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
});
