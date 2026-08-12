---
description: Defines how FitFlow's business domain model and domain responsibilities are evaluated during audits.
---

# Domain Audit

This rule applies only when auditing FitFlow's business and domain model.

The purpose is to determine whether the implemented domain model accurately
represents the responsibilities and relationships required by the system.

## Domain entities

For relevant entities, evaluate:

- responsibility;
- identity;
- attributes;
- relationships;
- lifecycle;
- ownership;
- dependencies;
- business significance.

Do not assume that a class is a domain entity solely because it is located in a
`models` directory.

Evaluate its actual responsibility from the implementation.

## Relationships

Verify important relationships between domain entities.

Determine:

- whether the relationship exists in the source code;
- its direction;
- cardinality where applicable;
- ownership;
- lifecycle dependency;
- whether the relationship is implemented consistently.

Do not infer relationships solely from names.

## Responsibilities

Identify:

- duplicated responsibilities;
- responsibilities assigned to the wrong component;
- entities containing unrelated responsibilities;
- missing responsibilities required by existing workflows;
- business rules implemented in inconsistent locations.

A missing domain concept should only be reported when existing behavior or
requirements provide evidence that the concept is required.

## Identity and boundaries

Evaluate whether related concepts are unnecessarily combined or incorrectly
separated.

Pay particular attention to distinctions such as:

- user identity;
- person information;
- client information;
- teacher information;
- membership;
- booking;
- class;
- schedule;
- session.

These names are examples from the FitFlow domain and must be validated against
the actual implementation.

Do not assume that two concepts require separate entities merely because they
have different names.

## Lifecycle

Where relevant, determine how domain objects are:

- created;
- associated;
- modified;
- deactivated;
- deleted;
- referenced by other objects.

Identify lifecycle inconsistencies only when supported by implementation
evidence.

## Domain findings

For each significant domain finding, identify:

1. affected entities;
2. observed behavior;
3. relevant relationships;
4. evidence;
5. domain impact;
6. confidence.

Do not propose new entities, relationships, or business rules without sufficient
evidence.