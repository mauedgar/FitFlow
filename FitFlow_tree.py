from pathlib import Path

IGNORAR = {
    ".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", ".idea", ".vscode"
}

def build_tree(root: Path, prefix: str = "") -> list[str]:
    lines = [root.name]
    children = sorted(
        [p for p in root.iterdir() if p.name not in IGNORAR],
        key=lambda p: (p.is_file(), p.name.lower())
    )

    for i, path in enumerate(children):
        last = i == len(children) - 1
        branch = "└── " if last else "├── "
        lines.append(prefix + branch + path.name)

        if path.is_dir():
            extension = "    " if last else "│   "
            sub = build_tree(path, prefix + extension)
            lines.extend(sub[1:])  # evita repetir nombre raíz
    return lines

if __name__ == "__main__":
    root = Path.cwd()
    lines = build_tree(root)
    out = "\n".join(lines)

    with open("arbol_proyecto.txt", "w", encoding="utf-8") as f:
        f.write(out)

    print(out)
    print("\nGenerado: arbol_proyecto.txt")