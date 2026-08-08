import logging
from datetime import datetime, timezone
from pathlib import Path
from shutil import move

from PIL import Image, ImageDraw, ImageFont  # pyright: ignore[reportMissingImports]

# ruff: noqa: BLE001

IGNORAR = {
    ".git",
    ".venv",
    ".venv_backend",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".cache",
    ".ruff_cache",
    ".coverage",
}
# ---------------------------------------------------------
# Configuración del logger
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Construcción del árbol de directorios
# ---------------------------------------------------------
def build_tree(root: Path, prefix: str = "") -> list[str]:
    """Construye un árbol de directorios en formato texto.

    Args:
        root (Path): Directorio raíz desde donde se construye el árbol.
        prefix (str): Prefijo visual para representar niveles del árbol.

    Returns:
        list[str]: Líneas que representan el árbol completo.

    """
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
def generar_imagen(lines: list[str], destino: Path) -> None:
    """Genera una imagen PNG con el contenido del árbol de directorios.

    Args:
        lines (list[str]): Líneas del árbol de directorios.
        destino (Path): Ruta donde se guardará la imagen.

    """
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
def mover_a_historico_si_corresponde(carpeta_origen: Path, carpeta_hist_base: Path, fecha_hoy: str) -> None:
    """Mueve archivos antiguos al histórico según su fecha en el nombre.

    Args:
        carpeta_origen (Path): Carpeta donde están los archivos actuales.
        carpeta_hist_base (Path): Carpeta base del histórico.
        fecha_hoy (str): Fecha actual en formato dd-mm-yy.

    """
    for archivo in carpeta_origen.iterdir():
        if not archivo.is_file():
            continue

        partes = archivo.stem.split("_")
        fecha_archivo = partes[-1] if len(partes) >= 3 else None  # noqa: PLR2004

        if fecha_archivo != fecha_hoy:
            carpeta_hist = carpeta_hist_base / fecha_archivo # pyright: ignore[reportOperatorIssue]
            carpeta_hist.mkdir(parents=True, exist_ok=True)

            subcarpeta = "TXT" if archivo.suffix == ".txt" else "PNG"
            destino_final = carpeta_hist / subcarpeta
            destino_final.mkdir(exist_ok=True)

            move(str(archivo), destino_final / archivo.name)
            msg2 = f"Movido a histórico ({fecha_archivo}): {archivo.name}"
            logger.info(msg2)

        else:
            archivo.unlink()
            msg3=f"Reemplazado archivo del mismo día: {archivo.name}"
            logger.info(msg3)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    CARPETA_SCRIPTS = Path(__file__).resolve().parent
    RAIZ_PROYECTO = CARPETA_SCRIPTS.parent

    BASE = RAIZ_PROYECTO / "docs" / "arquitectura" / "Estructura directorios"
    BASE.mkdir(parents=True, exist_ok=True)

    CARPETA_TXT = BASE / "TXT"
    CARPETA_PNG = BASE / "PNG"
    CARPETA_TXT.mkdir(exist_ok=True)
    CARPETA_PNG.mkdir(exist_ok=True)

    fecha_hoy = datetime.now(tz=timezone.utc).strftime("%d-%m-%y")

    HISTORICO_BASE = RAIZ_PROYECTO / "docs" / "historico" / "arquitectura"
    HISTORICO_BASE.mkdir(parents=True, exist_ok=True)

    mover_a_historico_si_corresponde(CARPETA_TXT, HISTORICO_BASE, fecha_hoy)
    mover_a_historico_si_corresponde(CARPETA_PNG, HISTORICO_BASE, fecha_hoy)

    estructuras = {
        "general": build_tree(RAIZ_PROYECTO),
        "frontend": build_tree(RAIZ_PROYECTO / "frontend"),
        "backend": build_tree(RAIZ_PROYECTO / "backend"),
    }

    for nombre, arbol in estructuras.items():
        archivo_txt = CARPETA_TXT / f"FitFlow_estructura_{nombre}_{fecha_hoy}.txt"
        archivo_txt.write_text("\n".join(arbol), encoding="utf-8")
        msg4=f"TXT generado: {archivo_txt.name}"
        logger.info(msg4)

        archivo_png = CARPETA_PNG / f"FitFlow_estructura_{nombre}_{fecha_hoy}.png"
        generar_imagen(arbol, archivo_png)
        msg5=f"PNG generado: {archivo_png.name}"
        logger.info(msg5)

    logger.info("Proceso completado con histórico y nuevas estructuras generadas.")

    respuesta = input(f"\n¿Querés abrir la carpeta destino?\n{BASE}\n(S/N): ").strip().lower()
    if respuesta == "s":
        try:
            import os
            os.startfile(BASE)  # Windows  # noqa: S606
        except Exception:
            try:
                import subprocess
                subprocess.run(["open", BASE])  # macOS  # noqa: PLW1510, S603, S607
            except Exception:
                subprocess.run(["xdg-open", BASE])  # Linux  # noqa: PLW1510, S603, S607
