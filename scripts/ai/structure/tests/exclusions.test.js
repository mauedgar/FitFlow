'use strict';

const test = require('node:test');
const assert = require('node:assert');
const path = require('path');
const fs = require('fs');

const root = path.join(__dirname, '..');
const exclusions = require(path.join(root, 'lib/exclusions.js'));

test('isExcluded returns true for .git', () => {
  assert.strictEqual(exclusions.isExcluded('.git/config', { isDirectory: false }), false);
  assert.strictEqual(exclusions.isExcluded('.git/', { isDirectory: true }), true);
});

test('isExcluded returns true for node_modules', () => {
  assert.strictEqual(exclusions.isExcluded('node_modules/react/index.js', { isDirectory: false }), true);
  assert.strictEqual(exclusions.isExcluded('frontend/node_modules/x', { isDirectory: false }), true);
});

test('isExcluded returns true for __pycache__', () => {
  assert.strictEqual(exclusions.isExcluded('backend/__pycache__/x.pyc', { isDirectory: false }), true);
  assert.strictEqual(exclusions.isExcluded('__pycache__/', { isDirectory: true }), true);
});

test('isExcluded returns true for .venv', () => {
  assert.strictEqual(exclusions.isExcluded('.venv/bin/python', { isDirectory: false }), true);
  assert.strictEqual(exclusions.isExcluded('backend/.venv_backend/lib/x', { isDirectory: false }), true);
});

test('isExcluded returns true for dist', () => {
  assert.strictEqual(exclusions.isExcluded('frontend/dist/main.js', { isDirectory: false }), true);
  assert.strictEqual(exclusions.isExcluded('dist/main.js', { isDirectory: false }), true);
});

test('isExcluded returns true for .env files', () => {
  assert.strictEqual(exclusions.isExcluded('.env', { isDirectory: false }), true);
  assert.strictEqual(exclusions.isExcluded('backend/.env', { isDirectory: false }), true);
  assert.strictEqual(exclusions.isExcluded('.env.local', { isDirectory: false }), true);
  assert.strictEqual(exclusions.isExcluded('frontend/.env.development', { isDirectory: false }), true);
});

test('isExcluded returns true for secrets', () => {
  assert.strictEqual(exclusions.isExcluded('secrets/key.pem', { isDirectory: false }), true);
  assert.strictEqual(exclusions.isExcluded('app/config/cert.p12', { isDirectory: false }), true);
  assert.strictEqual(exclusions.isExcluded('data/test.sqlite3', { isDirectory: false }), true);
});

test('isExcluded returns true for docs/archive', () => {
  assert.strictEqual(exclusions.isExcluded('docs/archive/README.md', { isDirectory: false }), true);
  assert.strictEqual(exclusions.isExcluded('docs/archive/source-material/x.md', { isDirectory: false }), true);
});

test('isExcluded returns false for legitimate source', () => {
  assert.strictEqual(exclusions.isExcluded('backend/app/main.py', { isDirectory: false }), false);
  assert.strictEqual(exclusions.isExcluded('frontend/src/App.tsx', { isDirectory: false }), false);
  assert.strictEqual(exclusions.isExcluded('docs/SOURCE_OF_TRUTH.md', { isDirectory: false }), false);
  assert.strictEqual(exclusions.isExcluded('backend/app/services/booking_service.py', { isDirectory: false }), false);
});

test('isSecretFile identifies secret files', () => {
  assert.strictEqual(exclusions.isSecretFile('.env'), true);
  assert.strictEqual(exclusions.isSecretFile('backend/.env'), true);
  assert.strictEqual(exclusions.isSecretFile('.env.local'), true);
  assert.strictEqual(exclusions.isSecretFile('key.pem'), true);
  assert.strictEqual(exclusions.isSecretFile('cert.key'), true);
  assert.strictEqual(exclusions.isSecretFile('app.p12'), true);
  assert.strictEqual(exclusions.isSecretFile('test.sqlite'), true);
  assert.strictEqual(exclusions.isSecretFile('main.py'), false);
  assert.strictEqual(exclusions.isSecretFile('config.yaml'), false);
  assert.strictEqual(exclusions.isSecretFile('App.tsx'), false);
});

test('isSecretFile does not flag legitimate config', () => {
  assert.strictEqual(exclusions.isSecretFile('config.yaml'), false);
  assert.strictEqual(exclusions.isSecretFile('settings.json'), false);
  assert.strictEqual(exclusions.isSecretFile('.repomixignore'), false);
});

test('hasSpaces detects spaces in paths', () => {
  assert.strictEqual(exclusions.hasSpaces('docs/directorios/Estructura de Clases/file.xml'), true);
  assert.strictEqual(exclusions.hasSpaces('docs/directorios/Estructura_de_Clases/file.xml'), false);
  assert.strictEqual(exclusions.hasSpaces('backend/app/main.py'), false);
});

test('matchesAnyPattern handles glob patterns', () => {
  assert.strictEqual(exclusions.matchesAnyPattern('.env.local', ['.env.*']), true);
  assert.strictEqual(exclusions.matchesAnyPattern('backend/.env.prod', ['.env.*']), true);
  assert.strictEqual(exclusions.matchesAnyPattern('app/.env', ['.env.*']), true);
  assert.strictEqual(exclusions.matchesAnyPattern('src/main.py', ['.env.*']), false);
});

test('EXCLUSIONS_PROFILE is default-v1', () => {
  assert.strictEqual(exclusions.EXCLUSIONS_PROFILE, 'default-v1');
});

test('loadRepomixIgnore reads existing ignore file', () => {
  const repoRoot = path.join(root, '..', '..', '..', '..');
  const patterns = exclusions.loadRepomixIgnore(repoRoot);
  assert.ok(Array.isArray(patterns));
  assert.ok(patterns.some((p) => p.includes('node_modules')));
});
