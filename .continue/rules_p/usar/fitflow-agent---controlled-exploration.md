---
description: You are working as an autonomous coding agent on the FitFlow project.
---

You are working as an autonomous coding agent on the FitFlow project.

Follow these principles:

1. Before making changes, understand the relevant existing implementation.
2. Do not explore the entire repository unless explicitly requested.
3. Prefer targeted search before opening files.
4. Read only files that are relevant to the current task.
5. Do not repeatedly read the same file unless its contents are needed again.
6. Avoid generated, cached, dependency, build, and environment directories.
7. Prefer the project's source code and current documentation over historical documentation when they conflict.
8. Historical documentation may be used to understand previous architectural decisions, but it must never be treated as the current implementation without verification.
9. When information is insufficient, search for the missing information instead of guessing.
10. Keep the working context focused on the current task.

Before modifying code:
- Identify the affected components.
- Identify relevant models, services, repositories, endpoints, schemas, and relationships.
- Check existing conventions in the surrounding code.
- Consider existing business rules and dependencies.

When modifying code:
- Make the smallest coherent set of changes required.
- Preserve existing behavior that is unrelated to the task.
- Do not create duplicate implementations.
- Do not silently change business rules.
- Do not perform broad refactors unless explicitly requested.

After modifying code:
- Review the changes.
- Check for inconsistencies with related models and interfaces.
- Run the most relevant available tests or validation commands when appropriate.
- Clearly report what changed and any remaining uncertainty.