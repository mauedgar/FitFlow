---
name: fitflow-frontend
description: FitFlow-specific React, TypeScript, Chakra UI and TanStack Query development guidance. Use for authorized frontend diagnosis, bounded repair and validation against the Product repository.
---

# FitFlow frontend — Product-local skill (candidate)

## Authority and starting point

FitFlow owns its frontend behavior, data and API contracts. This skill is procedural guidance only: it cannot select Product work, grant write access, create TaskCycles, authorize dependencies or waive Independent Review. Before each action, observe the competent Git branch, full commit/tree, `docs/SOURCE_OF_TRUTH.md`, `AGENTS.md`, the explicit authorized TASK/scope, and the exact owned worktree. A chat, old model config or installed skill is not sufficient authority.

Work only in the assigned frontend files and tests; coordinate any backend/API contract change with FitFlow Control and its exclusive owner. Never edit `.env`, secrets, production fixtures, backend migrations or other worktrees. Do not install/upgrade dependencies, create commits, push, merge or close a TaskCycle unless separately and explicitly authorized.

## Existing stack and contracts

- React 18, TypeScript 5, Vite, Chakra UI 2, TanStack Query, React Router, Axios.
- Respect backend-authoritative eligibility, capacities, bookings, permissions and audit. An enabled UI button does not confer domain authorization.
- Consult existing typed service adapters and Product API schemas before wiring UI. No direct database access or copied backend rules.
- Keep role gating consistent with `frontend/src/routes/AppRouter.tsx` and `ProtectedRoute`; verify inaccessible routes do not reveal protected data.
- Preserve UTC persistence/business-timezone formatting, cancellation and confirmed-to-attended semantics. Separate ordinary booking/fallback from explicit check-in.
- Source-grounded admin warning at initial candidate baseline: dashboard welcome-only, admin Clients/Teachers/CrudClasses use example data and simulated controls, admin sidebar/nav links diverge from routes. These are investigation targets, not implicit permission to expand or fix all screens.
- Billing/Payments stays deferred unless Product selects it; do not advertise an unimplemented operation as live.

## Working procedure

1. Read the specific Product TASK and relevant source; identify read/write paths, risk and frozen baseline.
2. Classify the observation as actual regression, intentional placeholder, missing Product contract, or unverified runtime hypothesis. Prefer evidence from running UI under safe isolated data; separate static evidence from browser evidence.
3. Propose the smallest bounded repair. Avoid adding dashboard/reporting/payment scope to a navigation repair.
4. Follow current component conventions, loading/empty/error states, accessible labels, responsive behavior and keyboard navigation. Use services/typed boundaries rather than ad-hoc HTTP calls.
5. Keep UI honest: hide/disable unsupported actions with clear user feedback; avoid fake client/teacher/class data in operational flows.
6. Validate affected TypeScript, ESLint, Vite build and existing frontend targeted tests. Request the separately permitted Playwright validator when browser coverage is relevant. Do not treat an installed Playwright skill as authorization for this implementer to launch a browser.
7. Return changed paths, candidate commit/tree or working diff, commands, real results, missing evidence, risks and documentation impact. The implementer must not review its own candidate or declare Product acceptance.

## Testing coverage boundary

`npm run lint` and `npm run build` check compilation and static rules, not browser functionality. The current existing directed guard `node tests/frontDeskLookupIntent.test.cjs` covers in-memory Front Desk lookup intent only. A green build does NOT certify admin routes, real API integration, login, accessibility or beta.

Browser/Playwright validation must use a Control-qualified, isolated validator with synthetic data; collect screenshots/snapshots/traces without tokens, real names or private records. Record explicit PASS, FAIL, BLOCKED or NOT_RUN per scenario and link to exact Git identity. No default Playwright Test dependency adoption or custom Recipe.

## Handoff discipline

Deliver evidence to FitFlow Control (Product authority). The Independent Reviewer remains separate and read-only. Treat a candidate PR, review PASS and CI green as different from acceptance, integration and beta launch authorization. Tecnotron is the producer of reusable runtime/Recipe contracts; this skill cannot change them.
