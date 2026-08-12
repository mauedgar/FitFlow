---
description: Preserve the existing FitFlow architecture and domain model unless a change is explicitly required.
---

# Architecture

FitFlow is a gym management system.

Respect the existing architecture and domain model.

## Existing design

Treat the current implementation as authoritative unless verified evidence shows
that it is inconsistent, incorrect, or explicitly being changed.

Do not assume that FitFlow follows a conventional architecture merely because
the project uses a particular framework or technology.

Do not introduce:
- new abstractions;
- new entities;
- new relationships;
- new architectural layers;
- new design patterns;

unless they are required by the current task or supported by sufficient evidence.

## Existing responsibilities

Before changing an existing component, understand its current responsibility
and its relationships with relevant components.

Prefer extending or correcting existing mechanisms over creating parallel
implementations.

Do not silently change domain rules or architectural boundaries.

## Architectural uncertainty

If the architecture cannot be established from the available evidence:

- investigate the relevant implementation;
- identify the missing evidence;
- do not invent the intended architecture.