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
