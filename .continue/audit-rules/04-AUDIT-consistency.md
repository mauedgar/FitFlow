---
description: Defines how to detect inconsistencies, contradictions, duplication, and architectural gaps across FitFlow.
---

# Consistency Audit

This rule applies when evaluating consistency across FitFlow components.

The purpose is to identify contradictions between different representations of
the same behavior, domain concept, or architectural responsibility.

## Cross-component consistency

Compare relevant relationships between:

- ORM models;
- schemas;
- services;
- repositories;
- API routes;
- authentication and authorization;
- configuration;
- migrations;
- tests;
- domain workflows.

Only compare components when they represent related behavior or concepts.

## Inconsistencies

Look for:

- mismatched names;
- mismatched responsibilities;
- missing relationships;
- contradictory relationships;
- duplicated business rules;
- inconsistent validation;
- inconsistent lifecycle behavior;
- incompatible assumptions between layers;
- unused or bypassed abstractions;
- implementation that contradicts documented behavior.

## Contradictions

When two sources appear to disagree:

1. identify both sources;
2. determine what each source actually establishes;
3. determine whether the disagreement is real;
4. identify which source reflects the current implementation when possible;
5. do not silently resolve the contradiction.

A contradiction must be supported by evidence from both sides.

## Duplication

Identify duplicated logic when the duplication has architectural or maintenance
impact.

Do not report every repeated line of code as a finding.

Focus on duplicated:

- business rules;
- validation;
- persistence logic;
- domain behavior;
- authorization logic;
- architectural responsibilities.

## Missing connections

Identify potentially missing relationships only when existing implementation
provides evidence that two components are expected to interact.

Do not classify an absent file, class, endpoint, or relationship as a defect merely
because it would be conventional to have one.

## Severity

Consider the impact of an inconsistency on:

- correctness;
- maintainability;
- extensibility;
- scalability;
- data integrity;
- business behavior.

Do not assign high severity solely because a design differs from a preferred
architecture.

## Verification

Before reporting a significant inconsistency:

- inspect the relevant source;
- trace the affected relationship when necessary;
- distinguish confirmed inconsistencies from hypotheses;
- identify unresolved uncertainty.

Every significant finding must be traceable to concrete evidence.