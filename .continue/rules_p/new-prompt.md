---
name: Initialize Codebase
description: Analyze the FitFlow codebase and build a concise architectural understanding
invokable: false
---

Analyze the FitFlow codebase and build a concise architectural understanding.

Do not modify any files.

First identify the main backend and frontend structure.

Then identify:
- Backend architecture and main layers.
- Frontend architecture and main application areas.
- Domain models and their major relationships.
- Pydantic schemas and their relationship to ORM models.
- Main API areas/endpoints.
- Authentication and authorization structure.
- Important services and business logic.
- Database/repository patterns.
- Existing tests and validation mechanisms.
- Relevant current documentation.

Use targeted search and read only the files necessary to establish this map.

Do not read dependency directories, virtual environments, caches, generated files, build artifacts, or lock files unless specifically required.

Do not attempt to understand every file.

Produce a concise architectural map with:
1. Backend structure
2. Frontend structure
3. Domain model overview
4. Important relationships
5. API structure
6. Authentication/authorization
7. Documentation sources
8. Potential inconsistencies or areas requiring further investigation

Do not make assumptions where the code does not provide enough evidence.