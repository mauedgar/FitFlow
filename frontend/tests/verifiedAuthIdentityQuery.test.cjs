const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");

const source = path.resolve(__dirname, "../src/utils/verifiedAuthIdentityQuery.ts");
const js = ts.transpileModule(fs.readFileSync(source, "utf8"), {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    esModuleInterop: true,
  },
}).outputText;

let response = { id: "subject-uuid", email: "server@example.com", role: "admin", active: true };
const requests = [];
const api = {
  get: async (url, options) => {
    requests.push({ url, options });
    return { data: response };
  },
};
const moduleUnderTest = { exports: {} };
const validatedProfile = (claims, data) => {
  if (
    !data || data.id !== claims.sub || data.active !== true ||
    typeof data.email !== "string" || !data.email.includes("@") ||
    !["admin", "client", "front_desk", "teacher"].includes(data.role)
  ) throw new Error("Untrusted backend identity");
  return { id: data.id, email: data.email, role: data.role, active: data.active };
};
vm.runInNewContext(js, {
  module: moduleUnderTest,
  exports: moduleUnderTest.exports,
  require: (request) => {
    if (request === "../services/api") return { __esModule: true, default: api };
    if (request === "./accessTokenClaims") return {
      inspectLocalAccessClaims: (value) => {
        if (value !== "signed-synthetic") throw new Error("Invalid access JWT");
        return { sub: "subject-uuid", role: "client", token_use: "access" };
      },
    };
    if (request === "./authMeProfile") return { projectServerAuthUser: validatedProfile };
    throw new Error("Unexpected import " + request);
  },
}, { filename: source });
const { verifiedAuthIdentityQuery } = moduleUnderTest.exports;

test("provider and admin use the exact same validated query factory", () => {
  for (const relative of [
    "../src/context/AuthProvider.tsx",
    "../src/components/admin/auth/useAdminIdentity.ts",
  ]) {
    const consumer = fs.readFileSync(path.resolve(__dirname, relative), "utf8");
    assert.match(consumer, /verifiedAuthIdentityQuery\(token, sessionGeneration\)/);
    assert.doesNotMatch(consumer, /getAdminAuthenticatedIdentity\(signal\)/);
  }
});

test("validated query is generation-scoped and uses backend email/role", async () => {
  const query = verifiedAuthIdentityQuery("signed-synthetic", 42);
  assert.deepEqual(Array.from(query.queryKey), ["currentUserProfile", "signed-synthetic", 42]);
  const signal = new AbortController().signal;
  const user = await query.queryFn({ signal });
  assert.equal(requests.at(-1).url, "/auth/me");
  assert.equal(requests.at(-1).options.headers.Authorization, "Bearer signed-synthetic");
  assert.equal(requests.at(-1).options.signal, signal);
  assert.equal(user.email, "server@example.com");
  assert.equal(user.role, "admin");
  assert.equal(user.id, "subject-uuid");
  assert.notEqual(user.email, user.id);
});

test("invalid and mismatched server identity cannot enter shared cache", async () => {
  const query = verifiedAuthIdentityQuery("signed-synthetic", 43);
  for (const invalid of [
    { ...response, id: "other-uuid" },
    { ...response, active: false },
    { ...response, role: "superadmin" },
    { ...response, email: "" },
  ]) {
    response = invalid;
    await assert.rejects(query.queryFn({ signal: new AbortController().signal }));
  }
  await assert.rejects(
    verifiedAuthIdentityQuery("wrong-token", 44).queryFn({ signal: new AbortController().signal }),
  );
});
