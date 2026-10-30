const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');
const load = (p) => fs.readFileSync(path.join(__dirname, '..', 'src', p), 'utf8');

test('Login errors never log the AxiosError or stringify arbitrary response data', () => {
  const page = load('pages/LoginPage.tsx');
  const service = load('services/classService.ts').split('// --- GymClass Endpoints ---')[0];
  assert.doesNotMatch(page, /console\.(log|error|debug|warn|info)\s*\(/);
  assert.doesNotMatch(page, /JSON\.stringify\(error\.response\.data\)/);
  assert.match(page, /error\.response\?\.status === 401/);
  assert.doesNotMatch(page, /error\.response\.data/);
  assert.doesNotMatch(service, /console\.(log|error|debug|warn|info)\s*\(/);
  assert.match(service, /await apiClient\.post<TokenResponse>\('\/auth\/token'/);
});

test('Mobile navigation uses semantic RouterLink destinations rather than inert anchors', () => {
  const source = load('components/layout/Navbar.tsx');
  for (const route of ['/', '/home', '/classes']) {
    assert.ok(source.includes('to="' + route + '" onClick={onClose}'), 'missing semantic route ' + route);
  }
  assert.doesNotMatch(source, /<Link onClick=\{/);
});

test('Carousel pauses autoplay on pointer or focus and respects reduced motion', () => {
  const source = load('components/landing/InfiniteCarousel.tsx');
  for (const token of ['useReducedMotion', 'onMouseEnter', 'onMouseLeave',
      'onFocusCapture', 'onBlurCapture', 'isPaused || shouldReduceMotion',
      'shouldReduceMotion ? { duration: 0 }']) {
    assert.ok(source.includes(token), 'missing ' + token);
  }
});
