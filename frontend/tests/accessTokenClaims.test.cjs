const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { createRequire } = require("node:module");
const vm = require("node:vm");
const ts = require("typescript");

// Execute the production TS helper through the existing TypeScript compiler.
// No test-only copy or extra dependency is introduced.
const source = path.resolve(__dirname, "../src/utils/accessTokenClaims.ts");
const compiled = ts.transpileModule(
  fs.readFileSync(source, "utf8"),
  { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } },
).outputText;
const mod = { exports: {} };
vm.runInNewContext(compiled, {
  module: mod,
  exports: mod.exports,
  require: createRequire(source),
}, { filename: source });
const { inspectLocalAccessClaims } = mod.exports;

const token = (payload) => [
  Buffer.from(JSON.stringify({ alg: "HS256" })).toString("base64url"),
  Buffer.from(JSON.stringify(payload)).toString("base64url"),
  "synthetic-signature-not-verified-by-ui",
].join(".");
const future = () => Math.floor(Date.now() / 1000) + 300;
const valid = (role = "admin") => ({ sub: "synthetic-uuid", role, exp: future(), token_use: "access" });

test("new and legacy access UI claims remain usable", () => {
  for (const role of ["admin", "client", "teacher", "front_desk"]) {
    assert.equal(inspectLocalAccessClaims(token(valid(role))).role, role);
  }
  const legacy = valid("client");
  delete legacy.token_use;
  assert.equal(inspectLocalAccessClaims(token(legacy)).role, "client");
});

test("refresh tokens, expired tokens and missing fields cannot hydrate UI", () => {
  const variants = [
    { ...valid(), token_use: "refresh" },
    { ...valid(), token_use: "unknown" },
    { ...valid(), exp: Math.floor(Date.now() / 1000) - 10 },
    { ...valid(), role: undefined },
    { ...valid(), role: "superadmin" },
    { ...valid(), sub: "" },
    { ...valid(), exp: undefined },
  ];
  for (const claims of variants) {
    assert.throws(() => inspectLocalAccessClaims(token(claims)));
  }
  assert.throws(() => inspectLocalAccessClaims("invalid-jwt"));
});
