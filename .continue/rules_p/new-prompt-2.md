---
name: Audit Architecture
description: Perform a read-only architectural audit of the requested area of FitFlow.

invokable: false
---

o not modify files.

The goal is to compare:

1. Current implementation
2. Current business rules
3. Existing architectural documentation
4. Related models and relationships
5. API schemas and contracts
6. Existing tests

Do not assume that historical documentation represents the current implementation.

For every relevant finding classify it as:

- CORRECT
- OUTDATED DOCUMENTATION
- IMPLEMENTATION INCONSISTENCY
- BUSINESS RULE VIOLATION
- DUPLICATION
- MISSING RELATIONSHIP
- POTENTIAL DESIGN PROBLEM
- REQUIRES CLARIFICATION

For each finding provide:
- Location
- Current behavior
- Expected behavior
- Evidence
- Impact
- Recommended action

Do not implement fixes.

Do not expand the investigation unnecessarily. Follow relationships only when they are relevant to the finding.