---
description: Rules for distinguishing verified evidence, inference, uncertainty, and contradictions.
---

# Evidence

The current source code and actual tool results are the primary evidence for
the project.

## Evidence levels

Distinguish explicitly between:

- VERIFIED FACT
  Directly established by source code, tool output, project documentation, or
  explicit user-provided information.

- INFERENCE
  A conclusion derived from verified evidence but not directly established by
  a source.

- UNVERIFIED
  A claim that could not be established with the available evidence.

- CONTRADICTION
  Two or more verified sources provide conflicting information.

## Evidence rules

Never present an inference as a verified fact.

Never present an unverified assumption as a project fact.

When evidence is insufficient:
- obtain additional evidence when practical;
- otherwise state that the information remains unverified.

When sources disagree:
- identify the contradiction;
- do not silently choose one source;
- determine which source reflects the current implementation when possible.

## Source priority

For the current implementation, prefer:

1. actual source code;
2. actual filesystem and tool results;
3. current project configuration;
4. current project documentation;
5. historical documentation.

Historical documentation may explain previous decisions but does not prove the
current implementation.

## Reporting

When a conclusion materially depends on inference, make that distinction clear
in the result.