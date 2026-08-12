---
description: Control modifications to the FitFlow codebase and preserve unrelated behavior.
---

# Changes

Do not modify files unless the current task explicitly requires modification.

## Before modifying

1. Read the current file.
2. Understand the relevant implementation and surrounding context.
3. Identify affected components and dependencies.
4. Determine the smallest coherent change required.

## During modification

- Make the smallest necessary change.
- Preserve unrelated existing behavior.
- Do not create duplicate implementations.
- Do not silently change business rules.
- Do not perform broad refactors unless explicitly requested.
- Preserve existing architectural boundaries unless the task requires changing
  them.

## After modification

- Review the resulting changes.
- Check consistency with related components.
- Run relevant tests or validation commands when appropriate.
- Clearly report what changed.
- Clearly report remaining uncertainty or failed validation.

## Audit restriction

If the current task explicitly states that it is an audit and that files must not
be modified, do not modify files.