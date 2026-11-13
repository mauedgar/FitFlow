const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { createRequire } = require("node:module");
const vm = require("node:vm");
const ts = require("typescript");

const source = path.resolve(__dirname, "../src/utils/authMeProfile.ts");
const js = ts.transpileModule(fs.readFileSync(source, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const mod = { exports: {} };
vm.runInNewContext(js, { module: mod, exports: mod.exports, require: createRequire(source) }, { filename: source });
const { projectServerAuthUser } = mod.exports;

const claims = { sub: "synthetic-uuid-123", role: "admin", exp: 9999999999, token_use: "access" };
const response = { id: claims.sub, email: "real-email@example.com", role: "client", active: true };

test("backend profile is authoritative for email and current role", () => {
  const user = projectServerAuthUser(claims, response);
  assert.equal(user.id, claims.sub);
  assert.equal(user.email, "real-email@example.com");
  assert.notEqual(user.email, claims.sub);
  assert.equal(user.role, "client"); // Role can differ from a stale signed token.
  assert.equal(user.active, true);
});

test("mismatched ID, missing email, disabled or unrecognized backend profile fails closed", () => {
  const bad = [
    { ...response, id: "different-uuid" },
    { ...response, email: claims.sub },
    { ...response, email: "" },
    { ...response, active: false },
    { ...response, role: "superadmin" },
    null,
  ];
  for (const value of bad) {
    assert.throws(() => projectServerAuthUser(claims, value));
  }
});
