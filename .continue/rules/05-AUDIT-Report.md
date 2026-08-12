---
description: Defines the structure and evidence requirements for FitFlow audit findings and reports.
---

# Audit Reporting

This rule applies when producing the final result of a FitFlow audit.

The report must distinguish verified implementation facts from interpretation and
recommendations.

## Report structure

Unless the user requests another format, organize the audit as:

1. Executive Summary
2. Verified Architecture
3. Domain Model
4. Key Relationships
5. Findings
6. Contradictions
7. Risks
8. Missing or Unverified Information
9. Recommendations
10. Priority Summary

## Findings

Each significant finding should contain:

### Finding

A concise description of the issue.

### Evidence

Identify the relevant files, classes, methods, relationships, or tool results.

Use exact paths and names established during the investigation.

### Analysis

Explain why the evidence represents an architectural, domain, consistency, or
implementation concern.

Clearly distinguish direct evidence from inference.

### Impact

Describe the practical consequence, such as:

- maintainability;
- scalability;
- correctness;
- coupling;
- data integrity;
- extensibility;
- complexity.

### Confidence

Classify the finding as:

- HIGH: directly established by strong evidence;
- MEDIUM: supported by evidence but dependent on some interpretation;
- LOW: plausible but insufficiently verified.

Low-confidence findings must not be presented as confirmed defects.

### Recommendation

Provide a recommendation only when the evidence supports one.

Recommendations should address the identified cause rather than merely treating
the symptom.

## Severity

Where useful, classify findings as:

- CRITICAL
- HIGH
- MEDIUM
- LOW
- INFORMATIONAL

Severity should reflect practical impact, not how easy the issue is to fix.

## Positive findings

Report important architectural strengths when they are supported by evidence.

Do not produce a report containing only defects.

## Uncertainty

Explicitly identify:

- areas not inspected;
- information that could not be verified;
- assumptions required for an interpretation;
- tool limitations;
- unresolved contradictions.

Do not hide uncertainty to make the report appear more complete.

## No invented evidence

Never fabricate:

- files;
- classes;
- methods;
- relationships;
- tool results;
- test results;
- architectural decisions;
- project requirements.

If something could not be verified, report it as unverified.

## Recommendations versus implementation

An audit report may recommend changes, but it must not silently implement them.

Implementation should occur only in a separate task explicitly requesting
changes.