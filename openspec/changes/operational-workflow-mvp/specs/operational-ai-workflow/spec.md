## Purpose

Define an executable AI workflow that minimizes context before runtime while
preserving verifiable evidence, component boundaries and Developer authority.

## ADDED Requirements

### Requirement: Deterministic workflow preflight
The workflow SHALL validate the Project Profile, canonical Task and active
registries before routing, context delivery or runtime execution.

#### Scenario: Invalid preflight input
- **WHEN** a required input is absent or violates its executable contract
- **THEN** the workflow stops with a stable blocked outcome before invoking a runtime

### Requirement: Token-bounded context delivery
The workflow SHALL materialize only explicitly requested evidence and SHALL
enforce the Task context budget before any runtime receives content.

#### Scenario: Required evidence exceeds budget
- **WHEN** one or more required evidence items cannot fit within the budget
- **THEN** the context result is PARTIAL or EMPTY and runtime execution does not begin

#### Scenario: Required evidence fits budget
- **WHEN** all required evidence items are safely materialized within the budget
- **THEN** the runtime receives only the included evidence and its telemetry

### Requirement: OpenSpec evidence boundary
The workflow SHALL consume a Task-linked OpenSpec change through read-only JSON
operations and SHALL treat the resulting delta as context evidence only.

#### Scenario: Task links an OpenSpec change
- **WHEN** the Task declares an available OpenSpec change identifier
- **THEN** that change is included as requested evidence without changing Task or RunState authority

#### Scenario: OpenSpec is unavailable
- **WHEN** a linked OpenSpec change cannot be read
- **THEN** the workflow reports missing evidence and does not silently continue as COMPLETE

### Requirement: Durable replay-safe run evidence
The workflow SHALL persist context artifacts, runtime identity, events and
RunState under the configured run root with replay-safe event identifiers.

#### Scenario: A run is replayed
- **WHEN** an identical event with the same event or idempotency identifier is persisted again
- **THEN** the store returns the existing event without appending a duplicate

#### Scenario: A replay conflicts
- **WHEN** the same event or idempotency identifier carries different content
- **THEN** the store rejects the write with a conflict error

### Requirement: Safe local simulation
The initial executable mode SHALL declare simulation, SHALL use only an eligible
zero-incremental runtime proposal and SHALL perform no provider inference or paid API call.

#### Scenario: Simulation completes
- **WHEN** preflight and context coverage are complete and a zero-incremental proposal is eligible
- **THEN** the workflow records a simulated identity and transitions the run to VALIDATING

#### Scenario: Paid execution is configured
- **WHEN** paid API is enabled or incremental budget is greater than zero
- **THEN** the workflow blocks before runtime execution

### Requirement: External control plane isolation
The workflow SHALL accept Orca correlation metadata without deriving canonical
lifecycle status from Orca workspace, Run, Task, Dispatch or gate status.

#### Scenario: Orca metadata is present
- **WHEN** a run includes opaque Orca identifiers or aliases
- **THEN** they remain correlation evidence and Task Lifecycle remains the state authority

### Requirement: Zero-incremental semantic model policy
The workflow SHALL use a bounded-invocation-verified zero-incremental model line
for each enabled role without enabling paid API or granting model authority.

#### Scenario: Eligible MEDIUM implementation
- **WHEN** routing selects `coder_a` for a MEDIUM implementation
- **THEN** the resolver may select `opencode/big-pickle` from the included zero-incremental pool

#### Scenario: Enabled planning and complex implementation roles
- **WHEN** Planner or Coder Strong A is manually invoked inside its role ceiling
- **THEN** its explicit primary line is `opencode/big-pickle`

#### Scenario: Ox Alpha launch outage
- **WHEN** Ox Alpha is temporarily unavailable on its provider line
- **THEN** the resolver excludes it and preserves its registry identity for later re-verification

#### Scenario: HIGH operation lacks a task-specific decision
- **WHEN** a HIGH task reaches the conditional strong-coder route without a new Developer authorization
- **THEN** routing remains BLOCKED_HIGH_RISK and model availability does not bypass that gate
