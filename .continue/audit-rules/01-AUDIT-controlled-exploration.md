---
description: Define the controlled exploration process used during FitFlow architectural audits.
---

# Audit Exploration

This rule applies only when performing an architectural or technical audit of
FitFlow.

The purpose of exploration is to build a reliable understanding of the existing
system before forming conclusions.

## Audit principle

Do not begin the audit by assuming which files, modules, layers, entities, or
architectural patterns exist.

Discover the actual project structure first.

The current source code and filesystem are the primary evidence.

## Exploration sequence

Follow this general sequence:

1. Establish the actual project workspace and backend location.
2. Inspect the relevant top-level directory structure.
3. Identify the application entry point and major application packages.
4. Identify the major architectural areas present in the project.
5. Locate the files relevant to the audit scope.
6. Read the relevant files.
7. Follow important imports, dependencies, and relationships.
8. Expand exploration only when the existing evidence requires it.
9. Form architectural conclusions only after sufficient evidence has been
   collected.

Do not skip directly from a filename or directory name to an architectural
conclusion.

## Controlled exploration

Exploration should be broad enough to establish the relevant architecture but
narrow enough to avoid reading the entire repository without justification.

Start with structure.

Then inspect the components relevant to the current audit.

Expand the investigation when:

- a dependency leads to another important component;
- an entity relationship requires verification;
- an architectural boundary cannot be established;
- a finding depends on another module;
- two sources appear to contradict each other;
- the current implementation cannot be understood from the files already
  inspected.

Do not expand exploration merely because a file or directory exists.

## Relevant files

A file is relevant when it can materially contribute to answering the current
audit question.

Examples include:

- application entry points;
- configuration;
- routers or controllers;
- services;
- domain models;
- ORM models;
- schemas;
- repositories;
- authentication and authorization components;
- database configuration;
- migrations;
- dependency definitions;
- tests;
- integration boundaries.

These are examples, not assumptions that FitFlow necessarily contains all of
these components.

## Following dependencies

When an inspected component imports or depends on another component that is
important to the current finding:

1. locate the actual referenced component;
2. inspect it;
3. update the architectural understanding;
4. continue only as far as necessary to establish the relationship.

Do not infer the implementation of an imported component without inspecting it
when that implementation is relevant to the conclusion.

## Stopping conditions

Stop exploration of a particular area when:

- the relevant architecture is sufficiently established;
- additional files are no longer contributing evidence;
- the remaining uncertainty cannot be resolved from the available source;
- the audit scope does not require further investigation.

Do not continue exploring indefinitely after the required evidence has been
established.

## Audit state

Maintain a distinction between:

- files discovered;
- files inspected;
- relationships verified;
- findings identified;
- findings requiring further verification;
- questions that remain unresolved.

Do not treat a discovered file as an inspected file.

Do not treat an inspected file as proof of behavior that was not actually
observed.

## No implementation during exploration

Do not modify the project during audit exploration.

The purpose of this phase is to understand and evaluate the existing system,
not to correct it.

Implementation recommendations belong after the relevant evidence and
analysis have been established.