---
description: Rules for discovering, resolving, and accessing project files without inventing paths.
---

# Filesystem

The filesystem is authoritative for determining the actual project structure.

## Workspace

Project workspace root:

C:\Proyectos Web\FitFlow

Backend root:

C:\Proyectos Web\FitFlow\backend

When a relative workspace path is required, backend files normally begin with:

backend\

The workspace path contains a space. This is valid and must not be treated as
an error.

## Path discovery

Never invent or guess a file path from:

- filename conventions;
- framework conventions;
- common project structures;
- assumptions about how the project should be organized.

If the exact path of a required file is unknown:

1. prefer Codebase/semantic search when locating functionality or symbols;
2. use filesystem search when locating a specific file or directory;
3. inspect the returned result;
4. use the actual returned path.

If a tool returns an exact path, reuse that path instead of reconstructing it.

## Known paths

A path may be treated as known when it was:

- explicitly provided by the user;
- returned by a filesystem or search tool;
- established by reading an existing file or directory result.

Do not reinterpret a known path based on conventional project structure.

## File existence

Failure to find a file at one path proves only that the file was not found at that
specific path.

Never conclude that a file does not exist in the project after checking only one
guessed or unverified path.

If a referenced file cannot be found:
- search for the filename;
- search for the relevant symbol or import;
- inspect the actual project structure;
- then determine whether the file is genuinely missing.

## Imports and module paths

Python imports are evidence about the intended module structure.

For example:

    from app.db.base_class import Base

indicates the module:

    app.db.base_class

and normally corresponds to:

    app\db\base_class.py

Do not reinterpret it as:

    app\models\base.py

unless filesystem evidence establishes that location.

## Directory exploration

When the relevant location is unknown:
1. inspect the appropriate parent directory;
2. identify relevant files and directories;
3. read only the files required for the current task.

Never assume that a conventional directory such as `models`, `services`, or
`repositories` exists.