---
description: Do not modify files unless the user explicitly requests implementation or modification.

---


For analysis, auditing, investigation, architecture review, or planning tasks:
- Read-only operation only.
- Do not create, delete, rename, move, or modify files.
- Do not run destructive commands.

Before a significant modification:
- Explain what is going to change if the task is ambiguous.
- Verify the affected dependencies.
- Check whether the change affects database models, schemas, API contracts, or business rules.

Never:
- Delete code merely because it appears unused without verification.
- Rewrite an entire module to fix a localized issue.
- Change database models without considering migrations and dependent schemas.
- Change business rules based solely on assumptions.
- Replace existing architecture with a different pattern without explicit justification.

If a required decision is ambiguous, stop and ask rather than guessing.