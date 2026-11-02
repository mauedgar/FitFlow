const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const root = path.join(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');

test('all login helpers use the mounted /auth/token route', () => {
  const api = read('src/services/api.ts');
  const service = read('src/services/classService.ts');
  const loginPage = read('src/pages/LoginPage.tsx');
  const router = read('../backend/app/routers/auth.py');
  assert.match(router, /APIRouter\(prefix="\/auth"/);
  assert.match(router, /@router\.post\("\/token"/);
  assert.match(api, /apiClient\.post\('\/auth\/token',\s*formData/);
  assert.match(service, /apiClient\.post<TokenResponse>\('\/auth\/token',\s*formData/);
  assert.match(loginPage, /classService\.login\(credentials\)/);
  assert.doesNotMatch(api + service, /['"]\/login\/token['"]/);
});
