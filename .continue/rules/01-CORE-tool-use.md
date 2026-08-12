---
description: Rules for using available agent tools correctly and reliably.
---

# Tool Use

Use available tools to obtain direct evidence whenever the required information
can be obtained through a tool.

## Available tools

Only use tools that are actually available in the current agent environment.

Never:
- invent a tool name;
- assume a tool exists because it is common in other agent environments;
- simulate a tool call;
- describe a tool call as successful when it was not executed;
- fabricate tool output.

A tool operation is considered successful only when the actual tool returns a
result.

## Tool selection

Use the most appropriate available tool for the operation.

Prefer:
- directory listing for discovering filesystem structure;
- file search for locating unknown files or symbols;
- file reading for inspecting known files;
- terminal commands for execution, diagnostics, tests, and operations when
  appropriate.

Do not use a terminal command when an available dedicated file tool can perform
the same read-only operation.

## Tool failures

If a tool call fails, is rejected, or is unavailable:

1. Read the actual error.
2. Do not assume the intended operation succeeded.
3. Do not treat the expected result as evidence.
4. Do not invent an alternative result.
5. Determine whether another available tool can provide the required evidence.
6. If appropriate, retry using a path or argument justified by known evidence.

A failed tool call does not prove that the requested file, directory, or symbol
does not exist.

## Tool reasoning

Do not spend reasoning time constructing hypothetical tool calls when an actual
tool can be executed.

Execute the tool and use its returned result as the basis for the next step.