# FitFlow — Claude Code Instructions

## 1. Purpose

This repository contains **FitFlow**, a gym management system.

These instructions define how Claude Code must operate when working on this repository.

The objective is to preserve architectural integrity, domain consistency, maintainability, and controlled evolution of the project.

---

# 2. Fundamental Rules

### 2.1 Inspect before acting

Before modifying code, Claude MUST inspect the relevant existing implementation and its dependencies.

Never assume:

* file paths;
* module names;
* architecture;
* class names;
* endpoint locations;
* database relationships;
* current sprint status;
* implementation status.

Use the actual repository as the source of truth for implementation details.

### 2.2 Do not invent architecture

Do not introduce architectural components, patterns, abstractions, or technologies merely because they are common or preferred elsewhere.

If the existing implementation is valid, preserve it.

### 2.3 Minimal change principle

Prefer the smallest change that correctly solves the requested problem.

Do not perform unrelated refactoring.

Do not reorganize files, rename modules, or change architectural boundaries unless explicitly required.

### 2.4 No speculative refactoring

Do not refactor code merely because an alternative implementation appears cleaner.

A refactor should have a concrete justification such as:

* correctness;
* data integrity;
* security;
* architectural violation;
* type safety;
* maintainability;
* performance with demonstrated relevance;
* explicit project requirement.

---

# 3. Modification Policy

Unless the user explicitly authorizes implementation:

DO NOT:

* modify source files;
* create new source files;
* delete files;
* rename files;
* execute database migrations;
* modify database data;
* change environment configuration;
* install dependencies;
* commit changes;
* push changes;
* reset or restore Git changes.

Analysis and inspection are allowed.

When the user explicitly requests implementation, modify only the necessary files.

Before potentially destructive operations, explain what will happen and request confirmation.

---

# 4. Repository Is the Source of Truth

The current repository is authoritative for the implementation.

Documentation may describe intended architecture, historical architecture, or previous decisions.

Always distinguish:

CURRENT CODE

from:

CURRENT DOCUMENTATION

from:

HISTORICAL DOCUMENTATION.

Do not assume that historical documentation represents the current implementation.

Directories such as:

docs/historico/

must be treated as historical unless the repository clearly indicates otherwise.

Generated files and temporary files should not automatically be considered authoritative.

---

# 5. Environment and Paths

Before performing filesystem analysis, determine the actual repository/workspace available to the agent.

Do not assume that a path mentioned by the user is directly accessible from the current execution environment.

Do not invent paths.

Use paths discovered from the actual workspace.

When the repository structure is unknown, inspect it before attempting to access specific files.

---

# 6. Architecture

The official backend architectural boundary is:

Router
↓
Service
↓
CRUD
↓
SQLAlchemy Model
↓
PostgreSQL

Pydantic schemas represent API contracts.

The responsibility of each layer is:

### FastAPI / Router

Responsible for:

* HTTP;
* routing;
* dependencies;
* authentication;
* authorization;
* HTTP parameters;
* response models;
* HTTP status codes;
* OpenAPI.

Routers should not contain business logic.

### Pydantic

Responsible for:

* API contracts;
* structural validation;
* serialization;
* deserialization;
* request models;
* response models.

Pydantic must not become the owner of business rules that depend on database state.

### Services

Services own business logic.

They are responsible for:

* business validation;
* domain rules;
* calculations;
* orchestration;
* transformations;
* availability;
* membership rules;
* booking rules;
* session generation;
* domain-level decisions.

### CRUD

CRUD is responsible for:

* database access;
* queries;
* persistence;
* filters;
* relationship loading;
* atomic data operations.

CRUD should not decide whether a business operation is allowed.

### SQLAlchemy

SQLAlchemy is responsible for:

* ORM mapping;
* relationships;
* persistence;
* queries;
* transactions;
* database representation.

### PostgreSQL

PostgreSQL should enforce structural integrity where appropriate:

* primary keys;
* foreign keys;
* NOT NULL;
* UNIQUE;
* CHECK;
* indexes;
* constraints.

---

# 7. Domain Rules

FitFlow's core domain currently includes:

User
Person
Client
Teacher
Membership

and:

GymClass
ClassSchedule
ClassSession
Booking

The conceptual operational flow is:

Client
↓
Membership

GymClass
↓
ClassSchedule
↓
ClassSession
↓
Booking
↓
Client

Do not create duplicate domain entities merely to support a presentation or operational view.

---

# 8. ClassSchedule

RRULE is the source of truth for schedule recurrence.

`days_of_week` is NOT part of the target architecture.

Do not automatically delete `days_of_week`.

First determine whether it is:

* actively used;
* referenced by schemas;
* referenced by services;
* referenced by CRUD;
* referenced by tests;
* referenced by queries;
* only residual;
* historical;
* documentation-only.

Only modify or remove it when explicitly authorized or when the user requests implementation of the architectural cleanup.

---

# 9. ClassSession

ClassSession represents a concrete occurrence of a ClassSchedule.

`capacity_snapshot` represents the historical capacity of the session.

Derived availability must not become the primary transactional source of truth.

Distinguish:

PERSISTED STATE

from:

DERIVED / TEMPORAL STATE.

---

# 10. Booking

Booking represents a client's reservation for a ClassSession.

Expected states:

* confirmed
* cancelled
* attended
* no_show

Cancellation preserves the booking history.

`cancelled` does NOT mean deleted.

Do not introduce soft-delete as a replacement for normal booking cancellation.

When booking through either schedule or session:

class_schedule_id XOR class_session_id

Exactly one must be supplied.

Structural validation belongs to the schema.

Business resolution and authorization belong to the service.

Capacity checks and booking creation must be treated as one protected transactional operation where required by the domain.

---

# 11. Membership

Current conceptual plans include:

* gym_only
* classes
* premium
* personalized

Membership status includes:

* active
* expired
* paused
* cancelled

Distinguish:

"Does the client have a valid membership?"

from:

"Does that membership allow access to this schedule/class?"

These are separate business decisions.

Membership authorization belongs to the service/domain layer.

---

# 12. SQLAlchemy

The target implementation uses modern SQLAlchemy 2.x patterns.

Prefer:

* DeclarativeBase
* Mapped[T]
* mapped_column()
* relationship()

When auditing or modifying models, inspect:

* type annotations;
* relationships;
* foreign keys;
* nullable;
* uniqueness;
* indexes;
* constraints;
* cascades;
* loading behavior;
* async database access.

Do not treat every deviation from the preferred style as an error.

Classify findings by actual impact.

---

# 13. Pydantic

Use Pydantic v2 consistently.

Where appropriate distinguish:

* Create
* Update
* Public
* Internal
* specialized views

Do not confuse ORM models with Pydantic schemas.

Avoid circular response structures that unnecessarily serialize entire relationship graphs.

---

# 14. Errors

Domain errors should remain conceptually separated from HTTP concerns.

Expected conceptual hierarchy:

DomainError
├── NotFoundError
├── BusinessValidationError
├── ConflictError
├── PermissionDeniedError
├── AuthError
└── ExternalServiceError

Services should operate in domain terms.

Routers/application boundaries should translate domain errors into HTTP responses.

Do not introduce HTTP-specific business logic into domain services.

---

# 15. Time and Timezones

FitFlow distinguishes local schedule times from timestamps.

Do not mix naive local times and UTC timestamps arbitrarily.

When working with dates or time:

* inspect the existing timezone strategy first;
* respect the project's configured local timezone;
* preserve the established UTC strategy;
* avoid introducing a second incompatible timezone strategy.

---

# 16. Testing

Before changing behavior, inspect relevant tests.

When implementing a non-trivial behavior change:

1. identify existing tests;
2. determine expected behavior;
3. implement the smallest change;
4. run the relevant tests;
5. report the result.

Do not rewrite tests merely to make an implementation pass.

Tests should represent intended behavior.

---

# 17. Static Analysis and Quality

Respect the project's existing tooling.

Relevant tools may include:

* Ruff;
* Pyright/Pylance;
* pytest;
* pytest-asyncio.

Do not silence warnings simply to obtain a clean output.

For `pyright: ignore`:

* determine why it exists;
* determine whether it is still necessary;
* prefer correcting the underlying typing problem when appropriate;
* do not remove a valid ignore merely for cosmetic reasons.

---

# 18. Documentation

Documentation should explain important architectural decisions and reasons.

Do not document trivial implementation details unnecessarily.

When changing architecture or domain behavior, update the relevant documentation if explicitly requested or if the documentation is part of the requested change.

Do not treat historical documentation as current architecture without verification.

---

# 19. Auditing Mode

When the user requests an audit, analysis, review, or architectural inspection:

DO NOT modify the repository.

Use this sequence:

Repository discovery
↓
Architecture map
↓
Domain map
↓
Implementation inspection
↓
Comparison against target architecture
↓
Findings
↓
Recommendations

Do not begin by analyzing whichever file happens to be open in the IDE.

The open IDE file is not necessarily the task target.

For repository-wide audits, inspect the repository structure first.

---

# 20. Finding Classification

When reporting technical findings, classify them as:

P0 — critical / blocking

P1 — important architecture, integrity, security, or correctness issue

P2 — necessary for the current project objective

P3 — minor improvement

P4 — future improvement / outside current scope

Distinguish real problems from stylistic alternatives.

---

# 21. Sprint Scope

The project should not enter an endless refactoring cycle.

Before recommending a change, determine whether it is relevant to the current objective.

Do not introduce:

* microservices;
* CQRS;
* event sourcing;
* unnecessary WebSockets;
* unnecessary infrastructure;
* speculative abstractions;
* premature optimization;
* unrelated frontend redesign;
* advanced analytics;
* unrelated AI functionality;

unless explicitly requested.

---

# 22. Git Safety

Git is part of the project's history and must be treated carefully.

Do not:

* reset;
* checkout over local modifications;
* restore files;
* delete branches;
* rewrite history;
* commit;
* push;

without explicit authorization.

When analyzing Git status, do not assume that deleted files are disposable artifacts.

Verify whether files are tracked and whether the change is intentional.

---

# 23. Communication

When uncertain about the implementation:

* inspect first;
* state the uncertainty;
* do not invent facts.

When multiple valid approaches exist:

* explain the relevant trade-offs;
* recommend the smallest approach consistent with the architecture.

When the requested task is ambiguous and the ambiguity materially affects implementation, ask for clarification before modifying code.

For analysis tasks, prefer inspecting the repository over asking the user to provide information that can be discovered locally.

---

# 24. Priority Rule

The goal is not to maximize the amount of code changed.

The goal is to maintain a correct, understandable, stable FitFlow system.

Prefer:

Correctness

>

Domain integrity

>

Architectural consistency

>

Security

>

Maintainability

>

Performance

>

Style

Avoid changes whose primary justification is stylistic preference.

---

# 25. Final Principle

**First understand the domain and the existing implementation. Then change the technology that represents it.**

FitFlow should evolve by extending the existing domain rather than duplicating responsibilities or introducing unrelated architectural complexity.
