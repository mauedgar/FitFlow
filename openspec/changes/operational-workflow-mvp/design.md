## Context

See `proposal.md`. Tecnotron-ai already contains validated library components,
but no entry point composes Task/Profile/OpenSpec/context/runtime/persistence.
The existing Agent MVP also gates on context without delivering that context to
the runtime, and RunStore has no operational caller.

## Goals / Non-Goals

**Goals:**

- Make the existing deterministic components executable as one local workflow.
- Reduce context before runtime and retain coverage telemetry per run.
- Keep OpenSpec, Orca, repo-packager and the runtime behind explicit boundaries.
- Produce durable evidence without any model or paid API call in the first mode.

**Non-Goals:**

- Execute a real model or automate semantic implementation.
- Grant Orca or OpenSpec lifecycle authority.
- Add generic retrieval, Temporal, MCP, embeddings or another dependency.
- Automate commit, push, merge, acceptance or cleanup.

## Decisions

### Exact materialization precedes ranked expansion

repo-packager gains a JSON `exact` mode for explicit paths. It performs no
cache writes and invokes neither npx nor Repomix. This is preferred over ranked
selection for required evidence because required paths are already known and
deterministic. Existing reduced and drill-down modes remain available for a
future bounded expansion cycle.

### OpenSpec is fetched before synchronous context packaging

A read-only CLI client uses only `list --json` and `show --json`. The selected
change is converted to one evidence item before ContextPackager runs. This
keeps the current synchronous materializer contract and avoids making all core
stages asynchronous.

### The Agent MVP passes context but does not own persistence

Agent MVP forwards the validated Task and ContextPackager result to
AgentRuntime. The operational runner owns writing context, identity, events and
RunState through RunStore. This preserves Agent Runtime portability and keeps
Task Lifecycle persistence outside the model adapter.

### Simulation is an explicit adapter

The initial CLI injects a local simulation adapter that mirrors the selected
proposal and performs no inference. A real adapter remains unavailable until
its own conformance task proves permissions, identity and paid-disabled rules.

### FitFlow remains the consumer authority

FitFlow owns Project Profile, Task, OpenSpec artifacts and run output. The AI
Core worktree is provided explicitly to avoid persisting ephemeral paths in the
Project Profile.

## Risks / Trade-offs

- [Approximate token count] -> Persist tokenizer metadata and never infer coverage from tokens.
- [Current Task Markdown varies] -> Accept only v2-compatible YAML frontmatter and fail closed.
- [OpenSpec CLI output can evolve] -> Validate minimum JSON shape and return UNAVAILABLE on mismatch.
- [No real model execution] -> Declare simulation in RuntimeIdentity and never report conformance.
- [Cross-repo writes] -> Use paired worktrees and one Task identity with explicit ownership.

## Migration Plan

1. Bootstrap and strictly validate the OpenSpec change in the FitFlow worktree.
2. Run unit and integration tests against temporary Project Profile and run roots.
3. Execute the CLI in simulation against `FF-AI-OPS-001` with explicit worktree roots.
4. Review evidence before changing Project Profile status from pending bootstrap.
5. Roll back by removing the new CLI/adapters and OpenSpec root; existing core APIs remain compatible.
