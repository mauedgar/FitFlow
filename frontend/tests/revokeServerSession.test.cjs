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
let rejected = false;
const api = { post: async (...args) => {
  calls.push(args);
  if (rejected) throw new Error("server down");
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

test("real logout sends refresh only in JSON body and bearer only in header", async () => {
  await revokeServerSession("synthetic-access", "synthetic-refresh");
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], "/auth/logout");
  assert.equal(calls[0][1].refresh_token, "synthetic-refresh");
  assert.equal(calls[0][2].headers.Authorization, "Bearer synthetic-access");
  assert.doesNotMatch(JSON.stringify(calls[0][0]), /synthetic/);
});
test("missing legacy refresh never reports success and makes no request", async () => {
  await assert.rejects(revokeServerSession("synthetic-access", null));
  assert.equal(calls.length, 1);
});
test("server outage propagates, never fabricates confirmed revocation", async () => {
  rejected = true;
  await assert.rejects(revokeServerSession("synthetic-access", "synthetic-refresh"));
});
test("SPA stores refresh in sessionStorage and both UI logout entrypoints report failures", () => {
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
