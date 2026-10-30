const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');

function parse(component) {
  const filename = path.join(__dirname, '..', 'src', 'components', component);
  return ts.createSourceFile(filename, fs.readFileSync(filename, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
}

function elements(source, name) {
  const found = [];
  const sourceFile = source.getSourceFile();
  function visit(node) {
    if ((ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node)) &&
        (ts.isJsxElement(node) ? node.openingElement : node).tagName.getText(sourceFile) === name) {
      found.push(node);
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  return found;
}

function opening(node) {
  return ts.isJsxElement(node) ? node.openingElement : node;
}

function attribute(node, name) {
  return opening(node).attributes.properties.find(prop => ts.isJsxAttribute(prop) && prop.name.text === name);
}

for (const [component, trigger, label] of [
  ['classes/ClassDetailModal.tsx', 'Dialog.CloseTrigger', 'Cerrar detalles de la clase'],
  ['layout/Navbar.tsx', 'Drawer.CloseTrigger', 'Cerrar menú'],
]) {
  test(`${trigger} renders a named close button`, () => {
    const source = parse(component);
    const [closeTrigger] = elements(source, trigger);
    assert.ok(closeTrigger && ts.isJsxElement(closeTrigger));
    assert.ok(attribute(closeTrigger, 'asChild'));
    const [button] = elements(closeTrigger, 'CloseButton');
    assert.ok(button, 'close trigger must render a visible CloseButton');
    assert.equal(attribute(button, 'aria-label')?.initializer?.text, label);
    assert.ok(attribute(button, 'position'), 'close button must remain visible in the overlay');
  });
}

test('carousel dots key their mapped root and expose an accessible active button', () => {
  const source = parse('landing/InfiniteCarousel.tsx');
  const [dot] = elements(source, 'Box').filter(box => attribute(box, 'borderRadius')?.initializer?.text === 'full');
  assert.ok(dot, 'carousel dot root exists');
  assert.ok(attribute(dot, 'key'), 'the mapped root must own the reconciliation key');
  assert.ok(attribute(dot, 'asChild'));
  const [button] = elements(dot, 'button');
  assert.ok(button);
  assert.equal(attribute(button, 'key'), undefined, 'the key must not be on the child button');
  assert.ok(attribute(button, 'aria-label'));
  assert.ok(attribute(button, 'aria-current'));
  assert.equal(attribute(button, 'type')?.initializer?.text, 'button');
  assert.ok(attribute(button, 'onClick'), 'manual slide selection must remain available');
});
