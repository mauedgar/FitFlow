const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const source = (file) => fs.readFileSync(path.join(__dirname, '..', 'src', file), 'utf8');
const navbar = source('components/admin/layout/AdminNavBar.tsx');
const sidebar = source('components/admin/layout/AdminSidebar.tsx');
const toast = source('components/ui/toaster.tsx');
const store = source('components/ui/toaster-store.ts');

test('mobile admin navigation is a controlled Chakra v3 Drawer with named controls and focus return', () => {
  assert.match(navbar, /<Drawer\.Root open=\{menuOpen\} onOpenChange=\{\(\{ open \}\) => setMenuOpen\(open\)\}/);
  assert.match(navbar, /finalFocusEl=\{\(\) => menuTrigger\.current\}/);
  assert.match(navbar, /<Drawer\.Trigger asChild>/);
  assert.match(navbar, /aria-label="Menú" aria-expanded=\{menuOpen\}/);
  assert.match(navbar, /<Drawer\.Backdrop\s*\/>/);
  assert.match(navbar, /<Drawer\.Positioner>/);
  assert.match(navbar, /<Drawer\.CloseTrigger aria-label="Cerrar menú"/);
  assert.match(navbar, /display=\{\{ base: 'inline-flex', md: 'none' \}\}/);
  assert.doesNotMatch(navbar, /overflowX="auto"|minW="max-content"/);
});

test('mobile links close on navigation, preserve exact Dashboard route and profile logout', () => {
  for (const route of ['/admin', '/admin/clients', '/admin/teachers']) {
    assert.ok(navbar.includes(`to: '${route}'`));
  }
  assert.match(navbar, /end: true/);
  assert.match(navbar, /<RouterNavLink to=\{link\.to\} end=\{link\.end\}/);
  assert.match(navbar, /onClick=\{\(\) => setMenuOpen\(false\)\}/);
  assert.match(navbar, /_focusVisible=\{\{ outline: '3px solid'/);
  assert.match(navbar, /aria-label="Menú de perfil"/);
  assert.match(navbar, /onSelect=\{handleLogout\}/);
  assert.match(navbar, /navigate\('\/login'\)/);
});

test('toast group fits 320px viewport and wraps long title and description', () => {
  assert.match(store, /placement: 'bottom-end', offsets: '16px'/);
  assert.match(toast, /width="min\(400px, calc\(100vw - 32px\)\)"/);
  assert.match(toast, /maxW="calc\(100vw - 32px\)"/);
  assert.match(toast, /overflowWrap="anywhere"/);
  assert.match(toast, /<Toast\.Title minW=\{0\}>/);
  assert.match(toast, /<Toast\.Description minW=\{0\}>/);
  assert.match(toast, /toast\.closable && <Toast\.CloseTrigger aria-label="Cerrar notificación"/);
});

function relativeLuminance(hex) {
  const channels = hex.match(/[\da-f]{2}/gi).map((channel) => {
    const value = parseInt(channel, 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}

test('active sidebar and drawer links meet AA normal text contrast against white and show focus', () => {
  const sidebarColor = sidebar.match(/backgroundColor: '(#[\da-f]{6})'/i)?.[1];
  const drawerColor = navbar.match(/backgroundColor: isActive \? '(#[\da-f]{6})'/i)?.[1];
  assert.ok(sidebarColor && drawerColor);
  for (const color of [sidebarColor, drawerColor]) {
    assert.ok(1.05 / (relativeLuminance(color) + 0.05) >= 4.5, `${color} must meet AA`);
  }
  assert.match(sidebar, /_focusVisible=\{\{ outline: '3px solid'/);
  assert.match(navbar, /_focusVisible=\{\{ outline: '3px solid'/);
});
