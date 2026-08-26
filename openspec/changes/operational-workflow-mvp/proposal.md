## Why

The AI Core components are implemented but not composed into an operational
workflow, causing agents to rediscover architecture and load excessive context.
The workflow needs an executable, deterministic spine before adding more model
or orchestration capability.

## What Changes

- Add a local workflow runner that validates Task, Project Profile and active registries.
- Materialize exact requested files through repo-packager under a hard token budget.
- Include an OpenSpec change as read-only context evidence when the Task links one.
- Deliver only included evidence to the runtime adapter.
- Persist context, runtime identity, events and RunState with replay-safe identifiers.
- Provide a declared simulation mode that performs no inference and no paid API call.
- Register the zero-incremental line observed through bounded invocations, enable Planner/Coder Strong A and preserve Ox Alpha as unavailable.
- Bootstrap OpenSpec in FitFlow without granting it lifecycle or acceptance authority.

Non-goals: real provider execution, paid APIs, automatic Developer acceptance,
Git integration, full Orca automation, Temporal, MCP and semantic retrieval.

## Capabilities

### New Capabilities

- `operational-ai-workflow`: Deterministic, token-bounded preparation, execution simulation and durable run evidence.

### Modified Capabilities

None.

## Impact

Affected systems are FitFlow Task/OpenSpec/model/FinOps configuration and Tecnotron-ai
adapters, ContextPackager composition, Agent Runtime handoff, RunStore and CLI.
No product runtime, database, dependency manifest or paid service is changed.
