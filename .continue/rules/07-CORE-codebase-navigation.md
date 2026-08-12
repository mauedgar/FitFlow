---
description: use Codebase Navigation
---

## Codebase Navigation

Use the `codebase` semantic search tool as the primary method for
discovering and locating relevant code.

Do NOT recursively explore the project directory with repeated
directory listings when the task is about understanding code.

Before reading files manually:
1. Use codebase to search for the relevant concept.
2. Identify the most relevant files from the search results.
3. Read only those files or specific sections needed for the task.

Use directory listing only when:
- codebase cannot locate the required information,
- the task explicitly requires filesystem structure,
- or you need to verify a specific path.

Avoid repeatedly listing the same directories.
Do not re-verify paths that have already been established.