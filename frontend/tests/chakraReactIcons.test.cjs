const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');

for (const [component, expectedIcons] of [
  ['components/classes/ClassCard.tsx', ['FaClock', 'FaCalendarAlt']],
  ['components/classes/ClassDetailView.tsx', ['FaTachometerAlt', 'FaClock']],
  ['pages/HomePage.tsx', ['FiCalendar']],
]) {
  test(`${component} composes react-icons without asChild refs`, () => {
    const filename = path.join(__dirname, '..', 'src', component);
    const source = ts.createSourceFile(filename, fs.readFileSync(filename, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const icons = [];

    function visit(node) {
      if ((ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node))) {
        const opening = ts.isJsxElement(node) ? node.openingElement : node;
        if (opening.tagName.getText(source) === 'Icon') {
          assert.ok(!opening.attributes.properties.some(prop => ts.isJsxAttribute(prop) && prop.name.text === 'asChild'),
            'react-icons must not receive refs from Chakra asChild');
          const as = opening.attributes.properties.find(prop => ts.isJsxAttribute(prop) && prop.name.text === 'as');
          assert.ok(as && ts.isJsxExpression(as.initializer) && as.initializer.expression,
            'Icon must use the Chakra v3 as={ReactIcon} form');
          icons.push(as.initializer.expression.getText(source));
        }
      }
      ts.forEachChild(node, visit);
    }

    visit(source);
    assert.deepEqual(icons, expectedIcons);
  });
}
