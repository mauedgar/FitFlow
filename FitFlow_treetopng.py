from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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
            lines.extend(sub[1:])
    return lines

if __name__ == "__main__":
    root = Path.cwd()
    lines = build_tree(root)

    font = ImageFont.load_default()
    padding = 20
    line_height = 16
    width = max(font.getlength(line) for line in lines) + padding * 2
    height = len(lines) * line_height + padding * 2

    img = Image.new("RGB", (int(width), int(height)), "white")
    draw = ImageDraw.Draw(img)

    y = padding
    for line in lines:
        draw.text((padding, y), line, fill="black", font=font)
        y += line_height

    img.save("arbol_proyecto.png")
    print("Generado: arbol_proyecto.png")