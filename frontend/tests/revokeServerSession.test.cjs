const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");

const source = path.resolve(__dirname, "../src/utils/revokeServerSession.ts");
const code = ts.transpileModule(fs.readFileSync(source, "utf8"), {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    esModuleInterop: true,
  },
}).outputText;
const calls = [];
let failures = [];
const api = { post: async (...args) => {
  calls.push(args);
  if (failures.length) throw failures.shift();
  return { status: 204 };
} };
const mod = { exports: {} };
vm.runInNewContext(code, {
  module: mod,
  exports: mod.exports,
  require: (name) => {
    if (name === "../services/api") return { __esModule: true, default: api };
    throw new Error("Unexpected imported module");
  },
}, { filename: source });
const { revokeServerSession } = mod.exports;

test("logout sends refresh in body and access bearer only in header", async () => {
  failures = [];
  const n = calls.length;
  await revokeServerSession("synthetic-access", "synthetic-refresh");
  assert.equal(calls.length, n + 1);
  assert.equal(calls[n][0], "/auth/logout");
  assert.equal(calls[n][1].refresh_token, "synthetic-refresh");
  assert.equal(calls[n][2].headers.Authorization, "Bearer synthetic-access");
  assert.doesNotMatch(JSON.stringify(calls[n][0]), /synthetic/);
});

test("missing legacy refresh never reports success and never makes request", async () => {
  failures = [];
  const n = calls.length;
  await assert.rejects(revokeServerSession("synthetic-access", null));
  assert.equal(calls.length, n);
});

test("synthetic transient 503 gets one idempotent retry and confirms", async () => {
  failures = [{ response: { status: 503 } }];
  const n = calls.length;
  await revokeServerSession("synthetic-access", "synthetic-refresh");
  assert.equal(calls.length, n + 2);
  assert.equal(calls[n + 1][1].refresh_token, "synthetic-refresh");
  assert.equal(calls[n + 1][2].headers.Authorization, "Bearer synthetic-access");
});

test("synthetic network acknowledgement loss gets one retry", async () => {
  failures = [{ request: { synthetic: true } }];
  const n = calls.length;
  await revokeServerSession("synthetic-access", "synthetic-refresh");
  assert.equal(calls.length, n + 2);
});

test("two synthetic transient failures remain UNCONFIRMED", async () => {
  failures = [{ response: { status: 503 } }, { request: { synthetic: true } }];
  const n = calls.length;
  await assert.rejects(revokeServerSession("synthetic-access", "synthetic-refresh"));
  assert.equal(calls.length, n + 2);
});

test("HTTP 401 must never retry or report success", async () => {
  failures = [{ response: { status: 401 } }];
  const n = calls.length;
  await assert.rejects(revokeServerSession("synthetic-access", "synthetic-refresh"));
  assert.equal(calls.length, n + 1);
});

test("unexpected programming error without HTTP transport never retries", async () => {
  failures = [new TypeError("synthetic unexpected failure")];
  const n = calls.length;
  await assert.rejects(revokeServerSession("synthetic-access", "synthetic-refresh"));
  assert.equal(calls.length, n + 1);
});

test("SPA keeps refresh tab-scoped and both logout UI entrypoints report failures", () => {
  const provider = fs.readFileSync(path.resolve(__dirname, "../src/context/AuthProvider.tsx"), "utf8");
  const loginPage = fs.readFileSync(path.resolve(__dirname, "../src/pages/LoginPage.tsx"), "utf8");
  for (const file of ["../src/components/layout/Navbar.tsx", "../src/components/admin/layout/AdminNavBar.tsx"]) {
    const contents = fs.readFileSync(path.resolve(__dirname, file), "utf8");
    assert.match(contents, /revocation\.catch/);
  }
  assert.match(provider, /sessionStorage\.setItem\("refresh_token"/);
  assert.doesNotMatch(provider, /localStorage\.setItem\("refresh_token"/);
  assert.match(provider, /sessionStorage\.removeItem\("refresh_token"/);
  assert.match(loginPage, /login\(data\.access_token, data\.refresh_token\)/);
});

test("mobile drawer invokes logout without delayed callback after close", () => {
  const nav = fs.readFileSync(path.resolve(__dirname, "../src/components/layout/Navbar.tsx"), "utf8");
  assert.doesNotMatch(nav, /setTimeout\s*\(\s*logoutUser/);
  assert.match(nav, /onClose\(\);\s*\/\/ Primero cierra la UI\s*logoutUser\(\)/);
});

