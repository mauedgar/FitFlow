---
name: fitflow-frontend
description: Product-specific React, TypeScript, Chakra UI and TanStack Query guidance for authorized FitFlow frontend analysis and bounded implementation.
---

# FitFlow frontend — Product-local skill (repaired proposal)

This skill guides a specialized implementer; it grants **no** Product authority, runtime tool permission, TaskCycle, dependency installation, acceptance, reviewer independence or Tecnotron Recipe.

## Mandatory scope and authority

1. Read `AGENTS.md` and `docs/SOURCE_OF_TRUTH.md` on the competent Product commit/tree.
2. Require an immutable Control-supplied authorization packet with TASK ID, exact source commit/tree, acceptance criteria, owned worktree, allowed paths, risk and validation contract. No write if absent, stale, unverifiable or conflicting with the Product SOT. The packet is evidence to reconcile, not authority merely because it appears in a prompt.
3. Keep read, edit, Git, external directory, web and validator permissions separate. This skill is not an alternative way to invoke blocked tools or read files outside the configured sandbox.
4. Do not modify environment files, credentials, production data, backend, API schemas or migrations without separate authorized ownership. Never widen scope opportunistically.

## Current architecture

- React, TypeScript, Vite, Chakra UI, TanStack Query, Axios and React Router.
- Backend remains authoritative for roles, capacity, eligibility, booking, check-in, audit and persistence. Do not replicate or bypass backend policies in UI.
- Use existing typed services and error/loading/empty states; preserve accessibility, keyboard and responsive behavior. Avoid mock data or buttons that imply a live domain operation where none exists.
- Preserve UTC persistence vs local display and the booking/check-in domain boundaries. Billing/Payments remains deferred until Product selection.

## Source audit notes, not product facts

On the **historical** FitFlow baseline `develop@98fac9ea2591880a8cf3316953326d65af170af8` (not current authority on subsequent commits), read-only source observations identified areas to recheck: `frontend/src/pages/admin/AdminDashboardPage.tsx` was a welcome view; `ClientsPage.tsx`, `TeachersPage.tsx`, and `CrudClassesPage.tsx` contained example rows/actions; and `frontend/src/routes/AppRouter.tsx` differed from `frontend/src/components/admin/layout/AdminSidebar.tsx` and `AdminNavBar.tsx` links. These are **hypotheses requiring fresh source and browser reproduction**, not accepted findings, runtime proof, permission to edit or authorization to build a dashboard.

## Bounded procedure

1. Confirm Product TASK packet, source, worktree, path ownership and relevant code.
2. Categorize observations: demonstrated regression, deliberate placeholder, contract gap or unverified hypothesis. Separate static inspection from native browser evidence.
3. Suggest minimal fixes within specifically authorized paths, preferring truthful navigation and existing typed APIs; avoid new payment/reporting/dashboard scope.
4. If authorized, propose source-only edits and request tool approval. Preserve code conventions and invariants.
5. **Request all executable validation from a separate qualified validator:** TypeScript, ESLint, Vite build, targeted tests, and Playwright where appropriate. The implementer has no shell/Playwright approval merely because the skill mentions those tools.
6. Hand off frozen candidate/diff, evidence, validation requests, risk and documentation impact. Independent Review and Product acceptance remain separate.

Green lint/build does not prove real UI behavior. Native Playwright browser tests must use approved isolated fixtures and avoid screenshots/traces with personal data, secrets or tokens. No new E2E framework or Recipe is introduced by this skill.
