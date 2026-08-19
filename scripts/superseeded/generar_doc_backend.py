import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from shutil import move

# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# RUTAS
# ---------------------------------------------------------
FECHA = datetime.now(timezone.utc).strftime("%d-%m-%y")

RAIZ_PROYECTO = Path(r"C:\Proyectos Web\FitFlow")
CARPETA_BACKEND_APP = RAIZ_PROYECTO / "backend" / "app"

CARPETA_DESTINO_BASE = RAIZ_PROYECTO / "docs" / "utilidades_web" / "pdoc"
CARPETA_DESTINO_HOY = CARPETA_DESTINO_BASE / FECHA
CARPETA_HISTORICO_BASE = RAIZ_PROYECTO / "docs" / "historico" / "utilidades_web" / "pdoc"

CARPETA_DESTINO_HOY.mkdir(parents=True, exist_ok=True)
CARPETA_HISTORICO_BASE.mkdir(parents=True, exist_ok=True)

NOMBRE_ARCHIVO = f"fitflow_backend_doc_{FECHA}.html"
ARCHIVO_FINAL = CARPETA_DESTINO_HOY / NOMBRE_ARCHIVO

# ---------------------------------------------------------
def mover_previos_al_historico() -> None:  # noqa: D103
    logger.info("Buscando documentación previa para mover al histórico...")
    for carpeta in CARPETA_DESTINO_BASE.iterdir():
        if carpeta.is_dir() and carpeta.name != FECHA:
            destino = CARPETA_HISTORICO_BASE / carpeta.name
            destino.mkdir(parents=True, exist_ok=True)
            move(str(carpeta), destino)
            logger.info("Movido a histórico: %s", carpeta.name)

# ---------------------------------------------------------
def generar_documentacion() -> None:  # noqa: D103
    logger.info("Generando documentación con pdoc...")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(RAIZ_PROYECTO)

    comando = [
        "pdoc",
        "--include-undocumented",
        "-o", str(CARPETA_DESTINO_HOY),
        str(CARPETA_BACKEND_APP),
    ]

    try:
        subprocess.run(comando, check=True, env=env)  # noqa: S603
        logger.info("Documentación generada correctamente.")

        archivo_generado = CARPETA_DESTINO_HOY / "app" / "index.html"

        if archivo_generado.exists():
            archivo_generado.rename(ARCHIVO_FINAL)
            logger.info("Archivo final generado: %s", ARCHIVO_FINAL)
        else:
            logger.warning("No se encontró el archivo generado por pdoc.")

    except subprocess.CalledProcessError:
        logger.exception("Error al ejecutar pdoc.")

# ---------------------------------------------------------
if __name__ == "__main__":
    mover_previos_al_historico()
    generar_documentacion()

    respuesta = input("¿Deseás abrir la carpeta con la documentación generada? (s/n): ").strip().lower()
    if respuesta == "s":
        os.startfile(CARPETA_DESTINO_HOY)  # noqa: S606
