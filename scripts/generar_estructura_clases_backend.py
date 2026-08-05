import logging  # noqa: INP001
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from shutil import move

# ---------------------------------------------------------
# CONFIGURACIÓN DE LOGGING
# ---------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# ---------------------------------------------------------
# CONFIGURACIÓN DE RUTAS
# ---------------------------------------------------------
fecha_hoy = datetime.now(tz=timezone.utc).strftime("%d-%m-%y")

CARPETA_SCRIPTS = Path(__file__).resolve().parent
RAIZ_PROYECTO = CARPETA_SCRIPTS.parent
CARPETA_BACKEND = RAIZ_PROYECTO / "backend"

CARPETA_DESTINO = RAIZ_PROYECTO / "docs" / "arquitectura" / "Estructura de Clases"
CARPETA_DESTINO.mkdir(parents=True, exist_ok=True)

CARPETA_HISTORICO_BASE = (
    RAIZ_PROYECTO / "docs" / "historico" / "arquitectura" / "Estructura de Clases"
)
CARPETA_HISTORICO_BASE.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# FUNCIÓN: Mover archivos antiguos al histórico
# ---------------------------------------------------------
PATRON_FECHA = re.compile(r"(\d{2}-\d{2}-\d{2})$")

def mover_a_historico_si_corresponde(
    carpeta_origen: Path, carpeta_hist_base: Path, fecha_hoy: str,
) -> None:
    """Mueve archivos antiguos al histórico según la fecha actual."""
    for archivo in carpeta_origen.iterdir():
        if not archivo.is_file():
            continue

        match = PATRON_FECHA.search(archivo.stem)
        if not match:
            logger.warning("Archivo ignorado (sin fecha válida): %s", archivo.name)
            continue

        fecha_archivo = match.group(1)

        if fecha_archivo != fecha_hoy:
            carpeta_hist = carpeta_hist_base / fecha_archivo
            carpeta_hist.mkdir(parents=True, exist_ok=True)

            destino = carpeta_hist / archivo.name
            move(str(archivo), destino)
            logger.info("Movido a histórico (%s): %s", fecha_archivo, archivo.name)
        else:
            archivo.unlink()
            logger.info("Reemplazado archivo del mismo día: %s", archivo.name)

# ---------------------------------------------------------
# PROCESO PRINCIPAL
# ---------------------------------------------------------
logger.info("Analizando el backend para extraer clases y paquetes...")

mover_a_historico_si_corresponde(CARPETA_DESTINO, CARPETA_HISTORICO_BASE, fecha_hoy)
comando = [
    "pyreverse",
    str(CARPETA_BACKEND),
    "-f",
    "ALL",
    "-o",
    "puml",
    "-p",
    "FitFlow",
    "--output-directory", str(CARPETA_DESTINO),
]

try:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(RAIZ_PROYECTO)
    subprocess.run(  # noqa: S603
        comando,
        cwd=RAIZ_PROYECTO,
        env= env,
        capture_output=True,
        text=True,
        check=True,
    )

    archivo_clases = CARPETA_DESTINO / "classes_FitFlow.puml"
    if archivo_clases.exists():
        destino_clases = CARPETA_DESTINO / f"FitFlow_estructura_clases_{fecha_hoy}.puml"
        archivo_clases.rename(destino_clases)
        logger.info("Diagrama de clases generado: %s", destino_clases.name)

    archivo_paquetes = CARPETA_DESTINO / "packages_FitFlow.puml"
    if archivo_paquetes.exists():
        destino_paquetes = CARPETA_DESTINO / f"FitFlow_estructura_paquetes_{fecha_hoy}.puml"
        archivo_paquetes.rename(destino_paquetes)
        logger.info("Diagrama de paquetes generado: %s", destino_paquetes.name)

except subprocess.CalledProcessError:
    logger.exception("Error al procesar el backend")

except FileNotFoundError:
    logger.exception("No se encontró el comando 'pyreverse'. Activa tu entorno virtual.")
