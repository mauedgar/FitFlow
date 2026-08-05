from datetime import datetime, timezone
from pathlib import Path
from shutil import move

from PIL import Image, ImageDraw, ImageFont

IGNORAR = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    ".idea",
    ".vscode",
}


# ---------------------------------------------------------
# Construcción del árbol de directorios
# ---------------------------------------------------------
def build_tree(root: Path, prefix: str = "") -> list[str]:
    lines = [root.name]
    children = sorted(
        [p for p in root.iterdir() if p.name not in IGNORAR],
        key=lambda p: (p.is_file(), p.name.lower()),
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


# ---------------------------------------------------------
# Generación de imagen PNG
# ---------------------------------------------------------
def generar_imagen(lines: list[str], destino: Path):
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

    img.save(destino)


# ---------------------------------------------------------
# Mover archivos antiguos al histórico
# ---------------------------------------------------------
def mover_a_historico_si_corresponde(carpeta_origen: Path, carpeta_hist_base: Path, fecha_hoy: str):
    for archivo in carpeta_origen.iterdir():
        if not archivo.is_file():
            continue

        # Extraer fecha del archivo: FitFlow_estructura_general_03-08-26.txt
        partes = archivo.stem.split("_")
        fecha_archivo = partes[-1] if len(partes) >= 3 else None

        # Si no tiene fecha o es de otro día → mover al histórico
        if fecha_archivo != fecha_hoy:
            carpeta_hist = carpeta_hist_base / fecha_archivo
            carpeta_hist.mkdir(parents=True, exist_ok=True)

            subcarpeta = "TXT" if archivo.suffix == ".txt" else "PNG"
            destino_final = carpeta_hist / subcarpeta
            destino_final.mkdir(exist_ok=True)

            move(str(archivo), destino_final / archivo.name)
            print(f"📦 Movido a histórico ({fecha_archivo}): {archivo.name}")

        else:
            # Si es del mismo día → reemplazar (borrar antes)
            archivo.unlink()
            print(f"♻ Reemplazado archivo del mismo día: {archivo.name}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    # 1. Rutas base
    CARPETA_SCRIPTS = Path(__file__).resolve().parent
    RAIZ_PROYECTO = CARPETA_SCRIPTS.parent

    BASE = RAIZ_PROYECTO / "docs" / "arquitectura" / "Estructura directorios"
    BASE.mkdir(parents=True, exist_ok=True)

    CARPETA_TXT = BASE / "TXT"
    CARPETA_PNG = BASE / "PNG"
    CARPETA_TXT.mkdir(exist_ok=True)
    CARPETA_PNG.mkdir(exist_ok=True)

    # 2. Fecha
    fecha_hoy = datetime.now(tz=timezone.utc).strftime("%d-%m-%y")

    # 3. Carpeta histórico base
    HISTORICO_BASE = RAIZ_PROYECTO / "docs" / "historico" / "arquitectura"
    HISTORICO_BASE.mkdir(parents=True, exist_ok=True)

    # 4. Mover archivos existentes si corresponde
    mover_a_historico_si_corresponde(CARPETA_TXT, HISTORICO_BASE, fecha_hoy)
    mover_a_historico_si_corresponde(CARPETA_PNG, HISTORICO_BASE, fecha_hoy)

    # 5. Generar árboles
    arbol_general = build_tree(RAIZ_PROYECTO)
    arbol_frontend = build_tree(RAIZ_PROYECTO / "frontend")
    arbol_backend = build_tree(RAIZ_PROYECTO / "backend")

    estructuras = {
        "general": arbol_general,
        "frontend": arbol_frontend,
        "backend": arbol_backend,
    }

    # 6. Guardar TXT y PNG
    for nombre, arbol in estructuras.items():
        # TXT
        archivo_txt = CARPETA_TXT / f"FitFlow_estructura_{nombre}_{fecha_hoy}.txt"
        archivo_txt.write_text("\n".join(arbol), encoding="utf-8")
        print(f"📄 TXT generado: {archivo_txt.name}")

        # PNG
        archivo_png = CARPETA_PNG / f"FitFlow_estructura_{nombre}_{fecha_hoy}.png"
        generar_imagen(arbol, archivo_png)
        print(f"🖼️ PNG generado: {archivo_png.name}")

    print("\n✅ Proceso completado con histórico y nuevas estructuras generadas.")
