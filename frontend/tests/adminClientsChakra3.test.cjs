const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const page = fs.readFileSync('src/pages/admin/ClientsPage.tsx', 'utf8');
const service = fs.readFileSync('src/services/clientService.ts', 'utf8');

test('Chakra v3 admin clients page contains no removed Chakra v2 APIs', () => {
  for (const obsolete of ['@chakra-ui/icons', 'AlertIcon', 'InputLeftElement',
    '<Thead', '<Tbody', '<Tr', '<Td', '<Th', 'isDisabled=', 'isLoading=']) {
    assert.ok(!page.includes(obsolete), `obsolete Chakra v2 API: ${obsolete}`);
  }
  assert.match(page, /<Table\.Root/);
  assert.match(page, /<Alert\.Root/);
});

test('admin client read stays scoped to authenticated account and first page', () => {
  assert.match(page, /currentUser\?\.email/);
  assert.match(page, /currentUser\?\.role === 'admin'/);
  assert.match(page, /queryKey: \['adminClients'/);
  assert.match(service, /apiClient\.get<AdminClientSummary\[]>\('\/clients\/'/);
  assert.match(service, /skip: 0, limit: 100/);
});

test('preserves loading, empty, retry, accessible state and responsive views', () => {
  assert.match(page, /role="status"/);
  assert.match(page, /role="alert"/);
  assert.match(page, /onClick=\{\(\) => void refetch\(\)\}/);
  assert.match(page, /No encontramos coincidencias/);
  assert.match(page, /<SimpleGrid/);
  assert.match(page, /<Table\.Body/);
});

test('network errors do not misrepresent an unknown total as zero clients', () => {
  assert.match(page, /isError \? 'No disponible'/);
  assert.match(page, /No pudimos cargar los clientes/);
});

test('admin list HTTP requests consume cancellation signal from query lifecycle', () => {
  assert.match(page, /queryFn: \(\{ signal \}\) => getAdminClients\(signal\)/);
  assert.match(service, /getAdminClients = async \(signal\?: AbortSignal\)/);
  assert.match(service, /\n\s*signal,\n/);
});

test('responsive menu region is keyboard reachable and named', () => {
  const nav = fs.readFileSync('src/components/admin/layout/AdminNavBar.tsx', 'utf8');
  assert.match(nav, /as="nav" aria-label="Secciones de administración" tabIndex=\{0\}/);
  assert.match(nav, /overflowX="auto"/);
  assert.match(nav, /aria-label="Menú de perfil"/);
});
