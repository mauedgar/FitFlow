---
description: FitFlow is a gym management system.
---



Treat the current source code as the source of truth for implementation.

The project contains historical architectural documentation. Historical documentation is useful for understanding previous decisions, relationships, and intended architecture, but it may be outdated.

When documentation and implementation disagree:

1. Detect the discrepancy.
2. Do not silently choose one.
3. Verify the current implementation.
4. Report the discrepancy explicitly.
5. Follow the current task's stated business rules when they are authoritative.

When analyzing architecture:
- Prefer existing domain models and their actual relationships.
- Trace relationships through the relevant layers instead of assuming them.
- Distinguish ORM relationships from Pydantic schemas.
- Distinguish database models from API/request/response schemas.
- Do not infer a relationship solely from a class name.
- Verify important relationships in the actual code.

When proposing refactoring:
- Preserve established business rules unless the task explicitly changes them.
- Identify affected dependencies before changing shared models.
- Consider database constraints, ORM mappings, schemas, services, endpoints, and tests.
- Prefer coherent domain-wide changes over isolated fixes that create inconsistencies.