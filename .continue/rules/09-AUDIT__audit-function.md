---
description: audit function
---

# CODEBASE AUDIT — TOOL USAGE RULES

## 1. Evidence over inference

The audit must be based on actual repository evidence.

Never present assumptions as verified facts.

Every important finding must be classified as:

VERIFIED
- Directly confirmed by source code or tool output.

INFERRED
- Strongly supported by evidence but not directly confirmed.

NOT FOUND
- Searched for but no sufficient evidence was found.

If something can be verified with a tool, verify it instead of guessing.

Do not use "likely", "probably", "perhaps", or conventional framework assumptions
when the repository can be inspected.

---

## 2. Search → Inspect → Record → Move on

For each audit topic:

1. Search for the relevant evidence.
2. Identify the most relevant file(s).
3. Read the most relevant file(s).
4. Record the finding.
5. Move to the next topic.

Do not keep investigating a topic after sufficient evidence has been obtained.

---

## 3. Never repeat an investigation

Before using a tool, review the previous tool results and reasoning.

Do NOT repeat:

- the same codebase query;
- a nearly identical codebase query;
- a search for a file whose exact path is already known;
- a read_file call for a file that was already read;
- an investigation whose evidence is already sufficient.

If previous evidence already answers the question, use it.

---

## 4. Known file paths must be read directly

If a previous tool result identifies a concrete file path, do not search
for that file again.

For example, if:

backend/app/main.py

has already been identified, use read_file directly.

Do not run another semantic search asking where main.py is.

---

## 5. Prefer targeted searches

Codebase queries must answer ONE concrete question.

Prefer:

"Where is the FastAPI application instance created?"

over:

"Find the main entry point, database configuration, ORM, authentication,
routers, tests, and documentation."

Do not combine unrelated investigations into one large query.

---

## 6. Tool budget

For each audit topic, prefer:

- 1 codebase search;
- 1-2 read_file calls.

Use additional tool calls only when the evidence is genuinely ambiguous
or contradictory.

Do not use tools merely to obtain redundant confirmation.

---

## 7. Stop searching when evidence is sufficient

Once the relevant implementation has been identified and inspected,
STOP SEARCHING.

Do not continue searching because another conventional location might exist.

If something remains uncertain, mark it as INFERRED or NOT FOUND and move on.

Do not sacrifice the entire audit to prove a minor detail.

---

## 8. No speculative repository structure

Never assume that conventional FastAPI/Python structure exists.

Do not assume files such as:

main.py
session.py
config.py
tests/
README.md

exist until tools confirm them.

However, if a previous tool result already confirmed a path, use that
evidence directly.

---

## 9. No repeated reasoning

Do not repeatedly reconsider the same plan.

Do not generate multiple alternative investigation strategies for the same
question.

Choose the most appropriate next tool action, execute it, evaluate the
result, and continue.

Do not spend multiple reasoning cycles deciding what tool to call next.

---

## 10. Context preservation

The available context is limited.

Prioritize high-value evidence over exhaustive exploration.

Do not load large files unless they are directly relevant.

Do not read entire unrelated modules.

Prefer the smallest number of files required to establish the architecture.

If sufficient evidence has been obtained, stop using tools and produce the
finding.

---

## 11. Avoid context loops

Never enter a loop such as:

search → think → search same topic → think → search same topic.

If a search does not provide enough evidence:

1. inspect the best result;
2. perform ONE more targeted search if necessary;
3. otherwise mark the finding INFERRED or NOT FOUND;
4. move on.

---

## 12. Evidence tracking

For every audit section, internally track:

- What is already known?
- Which files have already been inspected?
- What remains unknown?
- What is the single best next action?

Do not lose previously established facts.

---

## 13. No modifications

This is an audit.

DO NOT:

- edit files;
- create files;
- delete files;
- refactor code;
- install dependencies;
- change configuration;
- run destructive commands.

Read-only investigation only.

---

## 14. Audit completion rule

The audit is considered complete when every requested audit section has
either:

- VERIFIED evidence;
- INFERRED evidence with its limitation clearly stated; or
- NOT FOUND after a reasonable targeted search.

Do not continue investigating indefinitely.

When all sections have been classified, STOP USING TOOLS and produce the
audit.

---

## 15. Final output discipline

The final audit must:

- distinguish VERIFIED / INFERRED / NOT FOUND;
- cite concrete file paths;
- avoid unsupported claims;
- avoid repeating the same finding;
- clearly separate facts from architectural interpretation;
- identify evidence gaps;
- provide concise architectural conclusions.

Do not perform additional searches merely while writing the final report.