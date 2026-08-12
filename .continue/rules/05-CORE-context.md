---
description: Preserve verified progress and manage context during long-running tasks.
---

# Context Management

Long-running tasks may involve many files, tool calls, and intermediate findings.

## Preserve progress

Do not restart an investigation or implementation merely because the task is
large.

Before continuing a long-running task, determine:

- what has already been verified;
- which files have already been inspected;
- which components and relationships have been established;
- which findings remain unverified;
- which steps have been completed;
- which steps remain pending.

Do not reread files solely to reconstruct information that is already available
in the current context.

## Context pressure

If the available context becomes insufficient:

1. do not restart the task unnecessarily;
2. preserve the verified information required to continue;
3. reduce working context to:
   - verified facts;
   - relevant files;
   - important relationships;
   - confirmed inconsistencies;
   - unresolved questions;
   - completed steps;
   - pending steps;
4. continue from the last unresolved step.

Do not invent or claim knowledge that is no longer available in the current
context.

## Continuation

If asked to continue a previous task:

- resume from the available state;
- do not restart from the beginning unless necessary;
- retrieve only missing information that is required to continue.