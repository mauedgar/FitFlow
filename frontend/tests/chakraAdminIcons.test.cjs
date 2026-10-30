const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');

for (const [component, expected] of [
  ['components/dashboard/BookingCard.tsx', ['FiClock', 'FiMapPin']],
  ['components/admin/layout/AdminSidebar.tsx', ['link.icon']],
  ['components/admin/layout/AdminNavBar.tsx', ['FiHome', 'menu.icon', 'item.icon', 'FiLogOut']],
]) {
  test(`${component} composes react-icons with Chakra v3 as prop`, () => {
    const filename = path.join(__dirname, '..', 'src', component);
    const source = ts.createSourceFile(filename, fs.readFileSync(filename, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const icons = [];
    function visit(node) {
      if (ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node)) {
        const opening = ts.isJsxElement(node) ? node.openingElement : node;
        if (opening.tagName.getText(source) === 'Icon') {
          assert.ok(!opening.attributes.properties.some(p => ts.isJsxAttribute(p) && p.name.text === 'asChild'),
            'Icon asChild must not inject refs into react-icons');
          const prop = opening.attributes.properties.find(p => ts.isJsxAttribute(p) && p.name.text === 'as');
          assert.ok(prop && ts.isJsxExpression(prop.initializer) && prop.initializer.expression,
            'Icon must use as={ReactIcon}');
          icons.push(prop.initializer.expression.getText(source));
        }
      }
      ts.forEachChild(node, visit);
    }
    visit(source);
    assert.deepEqual(icons, expected);
  });
}
