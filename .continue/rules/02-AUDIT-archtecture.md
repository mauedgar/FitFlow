---
description: Defines the architectural dimensions to evaluate during FitFlow audits.
---

# Architectural Audit

This rule applies only when performing an architectural audit of FitFlow.

The purpose is to evaluate the architecture that actually exists in the source
code, not the architecture the project is expected or assumed to have.

## Architectural evaluation

Evaluate the following dimensions when relevant to the audit scope:

- component responsibilities;
- separation of concerns;
- dependency direction;
- coupling;
- cohesion;
- architectural boundaries;
- dependency relationships;
- layering;
- abstraction boundaries;
- module organization;
- extensibility;
- maintainability;
- scalability;
- consistency of architectural patterns.

Do not assume that FitFlow follows a specific architectural pattern unless the
source code provides evidence for it.

## Responsibilities

For important components, determine:

- what responsibility the component currently has;
- whether that responsibility is coherent;
- which other components it depends on;
- which components depend on it;
- whether responsibilities are duplicated or unnecessarily distributed;
- whether a component appears to contain unrelated responsibilities.

Do not classify a responsibility as an architectural problem merely because the
component is large.

The problem must be supported by evidence of inappropriate coupling, unclear
boundaries, duplication, inconsistency, or another concrete architectural
consequence.

## Dependencies

Trace relevant dependencies between:

- modules;
- packages;
- application layers;
- services;
- repositories;
- models;
- schemas;
- API components;
- infrastructure components.

Identify:

- unexpected dependencies;
- unnecessary dependencies;
- circular dependencies;
- inappropriate dependency direction;
- excessive coupling;
- duplicated dependency paths.

Only report a dependency problem when the actual implementation supports the
finding.

## Boundaries

Evaluate whether architectural boundaries are clear and consistently respected.

Look for cases where:

- one layer directly performs responsibilities belonging to another;
- domain logic is duplicated across layers;
- infrastructure concerns leak into domain logic;
- API concerns are unnecessarily coupled to persistence;
- unrelated modules directly depend on implementation details.

Do not impose a preferred architecture without evidence that the existing
boundary causes a concrete problem.

## Patterns and consistency

Identify repeated architectural patterns in the current implementation.

Evaluate whether those patterns are:

- consistently applied;
- inconsistently applied;
- unnecessarily duplicated;
- contradicted by other parts of the system.

Do not recommend introducing a design pattern solely because it is commonly used
in similar projects.

## Findings

A significant architectural finding should identify:

1. affected components;
2. observed implementation;
3. architectural concern;
4. evidence;
5. impact;
6. confidence.

Distinguish verified architectural facts from interpretation.

## Recommendations

Recommendations must follow from the observed architecture.

Prefer recommendations that:

- address the identified architectural cause;
- preserve existing valid design decisions;
- minimize unnecessary complexity;
- improve maintainability or scalability;
- can be justified by the evidence.

Do not redesign the entire system merely because another architecture would also
be possible.