---
description: audit function 
---
## AUDIT TOOL USAGE RULES

When auditing the codebase:

1. Evidence over inference.
   Never present an assumption as verified evidence.
   Explicitly label findings as VERIFIED, INFERRED, or NOT FOUND.

2. Avoid repeated searches.
   Before calling codebase, check whether the same question has already
   been answered by previous tool output or a file already identified.

3. Search once, then inspect.
   If codebase identifies a relevant file, prefer read_file on that file
   instead of performing the same semantic search again.

4. Do not search for a known file.
   If a previous tool result identified a concrete path such as
   backend/app/main.py, read that file directly.

5. Do not speculate about conventional locations.
   Do not say "likely", "probably", or "perhaps" when the repository
   can be inspected to verify the fact.

6. One investigation pass per topic.
   For each audit item:
   - search for the relevant evidence;
   - read the most relevant files;
   - record the finding;
   - move to the next item.

7. Stop when sufficient evidence exists.
   Do not continue searching merely to obtain redundant confirmation.

8. Tool budget.
   Prefer a maximum of 2-3 tool calls per audit item unless the evidence
   is genuinely ambiguous.

9. Never repeat the same tool call with the same or nearly identical query
   unless the previous result was insufficient or failed.

10. The final audit must distinguish:
    VERIFIED — directly confirmed by source code.
    INFERRED — supported indirectly but not directly verified.
    NOT FOUND — searched but no evidence was found.