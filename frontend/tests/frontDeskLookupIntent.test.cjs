// No external test framework: use the existing TypeScript compiler and Node's assert.
// The exact helper used by FrontDeskPage is transpiled in-memory and exercised.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ts = require('typescript');

const sourcePath = path.join(__dirname, '..', 'src', 'utils', 'frontDeskLookupIntent.ts');
const pagePath = path.join(__dirname, '..', 'src', 'pages', 'FrontDeskPage.tsx');
const sourceText = fs.readFileSync(sourcePath, 'utf8');
const pageText = fs.readFileSync(pagePath, 'utf8');
const code = ts.transpileModule(sourceText, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  reportDiagnostics: true,
});
assert.equal(code.diagnostics.length, 0, 'lookup guard should compile');
const moduleRef = { exports: {} };
vm.runInNewContext(code.outputText, { module: moduleRef, exports: moduleRef.exports });
const { nextLookupIntent, isCurrentLookupIntent } = moduleRef.exports;

assert(pageText.includes('if (!isCurrentLookupIntent(lookupIntentRef.current, intent)) return;'),
  'late success/error callbacks must guard the current request');
assert(pageText.includes('lookupIntentRef.current = nextLookupIntent(lookupIntentRef.current, event.target.value);'),
  'input edits must invalidate prior requests synchronously');
assert(pageText.includes('lookupMutation.mutate(intent);'),
  'requests must carry the exact intent generation');

let current = { revision: 0, document: '' };
let selectedClient = null;
let selectedSession = null;
let preparedBooking = null;
const applySuccess = (request, client) => {
  if (!isCurrentLookupIntent(current, request)) return;
  selectedClient = client;
  selectedSession = null;
  preparedBooking = null;
};

// A pending -> change to B -> late A response: A must not be selected.
current = nextLookupIntent(current, 'A');
const requestedA = current;
current = nextLookupIntent(current, 'B');
selectedClient = null;
selectedSession = null;
preparedBooking = null;
applySuccess(requestedA, { id: 'client-A' });
assert.equal(selectedClient, null, 'late A response selected the wrong client');
assert.equal(selectedSession, null, 'late A response restored session');
assert.equal(preparedBooking, null, 'late A response restored booking');
assert.equal(selectedClient !== null && selectedSession !== null, false, 'late A enabled actions');

// A->B->A is still stale: comparison of document alone would fail.
current = nextLookupIntent(current, 'A');
applySuccess(requestedA, { id: 'client-A' });
assert.equal(selectedClient, null, 'A->B->A revived a stale request');

// Normal current lookup returns its correct client.
const latestRequestA = nextLookupIntent(current, 'A');
current = latestRequestA;
applySuccess(latestRequestA, { id: 'fresh-A' });
assert.equal(selectedClient.id, 'fresh-A', 'current lookup failed');
assert.equal(isCurrentLookupIntent(current, requestedA), false);

// A newer response followed by stale callback cannot overwrite current selection.
current = nextLookupIntent(current, 'B');
const requestedB = current;
applySuccess(requestedB, { id: 'client-B' });
applySuccess(latestRequestA, { id: 'client-A' });
assert.equal(selectedClient.id, 'client-B', 'stale response overwrote newer resolution');
console.log('F3_LOOKUP_INTENT_REGRESSION_PASS (6 targeted guards)');
