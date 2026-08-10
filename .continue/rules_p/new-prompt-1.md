---
name: Analyze Before Acting
description: Analyze the requested task before making any changes.
invokable: false
---

First determine:
- What is being requested.
- Which parts of the system are affected.
- Which files are likely relevant.
- Which business rules apply.
- Which existing implementations must be preserved.
- What dependencies may be affected.

Use targeted search to locate the relevant code.

Read only the necessary files.

Do not modify anything during the analysis phase.

Then provide:

### Understanding
What you understand the task to require.

### Relevant components
The files, classes, models, schemas, services, endpoints, or frontend components involved.

### Existing behavior
How the current implementation works.

### Business rules
The rules that constrain the implementation.

### Problems or inconsistencies
Anything that appears incorrect, duplicated, outdated, or contradictory.

### Proposed approach
The smallest coherent implementation strategy.

### Risks
Potential side effects or dependencies.

If the task is ambiguous, ask for clarification instead of guessing.

Only begin implementation after the analysis is complete and the requested scope is clear.