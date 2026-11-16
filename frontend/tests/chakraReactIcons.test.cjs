const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');

// Regression contract: Chakra Icon must receive React icons through "as".
// The particular icon glyph is presentation, not a Product invariant.
const componentPaths = [
  'components/dashboard/BookingCard.tsx',
  'components/admin/layout/AdminSidebar.tsx',
  'components/admin/layout/AdminNavBar.tsx',
  'components/classes/ClassCard.tsx',
  'components/classes/ClassDetailView.tsx',
  'pages/HomePage.tsx',
];

for (const component of componentPaths) {
  test(`${component} composes Chakra v3 Icon without incompatible asChild refs`, () => {
    const filename = path.join(__dirname, '..', 'src', component);
    const source = ts.createSourceFile(
      filename, fs.readFileSync(filename, 'utf8'),
      ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX,
    );
    let iconCount = 0;

    function visit(node) {
      if (ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node)) {
        const opening = ts.isJsxElement(node) ? node.openingElement : node;
        if (opening.tagName.getText(source) === 'Icon') {
          iconCount += 1;
          const props = opening.attributes.properties;
          assert.ok(!props.some(prop =>
            ts.isJsxAttribute(prop) && prop.name.text === 'asChild'),
          'Chakra Icon asChild must not inject refs into react-icons');
          const asProp = props.find(prop =>
            ts.isJsxAttribute(prop) && prop.name.text === 'as');
          assert.ok(
            asProp && ts.isJsxExpression(asProp.initializer)
              && asProp.initializer.expression
              && (ts.isIdentifier(asProp.initializer.expression)
                || ts.isPropertyAccessExpression(asProp.initializer.expression)),
            'Chakra v3 Icon must receive an icon expression through as={ReactIcon}',
          );
        }
      }
      ts.forEachChild(node, visit);
    }

    visit(source);
    assert.ok(iconCount > 0, `No Icon components found in ${component}`);
  });
}
