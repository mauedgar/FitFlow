"""Genera diagramas UML de clases y paquetes del backend de FitFlow en formato Mermaid.

El script utiliza pyreverse desde el entorno virtual específico del backend y almacena
los diagramas generados en la documentación de arquitectura. Los archivos anteriores
se trasladan automáticamente al histórico según su fecha de generación.
"""

import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from shutil import move

# --------------------------------------------------------------------------- #
# CONFIGURACIÓN DE LOGGING
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# --------------------------------------------------------------------------- #
# CONFIGURACIÓN DE RUTAS
# --------------------------------------------------------------------------- #
FECHA_HOY = datetime.now(tz=timezone.utc).strftime("%d-%m-%y")

# El script se encuentra directamente en: FitFlow/scripts/
CARPETA_SCRIPTS = Path(__file__).resolve().parent
RAIZ_PROYECTO = CARPETA_SCRIPTS.parent
CARPETA_BACKEND = RAIZ_PROYECTO / "backend"
CARPETA_ENTORNO = CARPETA_BACKEND / ".venv_backend"
CARPETA_DESTINO = (
    RAIZ_PROYECTO / "docs" / "arquitectura" / "Estructura de Clases"
)
CARPETA_HISTORICO_BASE = (
    RAIZ_PROYECTO / "docs" / "historico" / "arquitectura" / "Estructura de Clases"
)
PYREVERSE = CARPETA_ENTORNO / "Scripts" / "pyreverse.exe"
PATRON_FECHA = re.compile(r"(\d{2}-\d{2}-\d{2})$")

# --------------------------------------------------------------------------- #
# PREPARACIÓN DE DIRECTORIOS
# --------------------------------------------------------------------------- #
CARPETA_DESTINO.mkdir(parents=True, exist_ok=True)
CARPETA_HISTORICO_BASE.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# FUNCIONES AUXILIARES
# --------------------------------------------------------------------------- #
def mover_a_historico_si_corresponde(
    carpeta_origen: Path,
    carpeta_hist_base: Path,
    fecha_hoy: str,
) -> None:
    """Mueve al histórico los archivos generados en fechas anteriores.

    Los archivos de la fecha actual se eliminan para permitir que la nueva
    ejecución genere una versión actualizada.
    """
    for archivo in carpeta_origen.iterdir():
        if not archivo.is_file():
            continue

        # Volvemos al método nativo y correcto de pathlib
        match = PATRON_FECHA.search(archivo.stem)
        if not match:
            logger.warning(
                "Archivo ignorado (sin fecha válida): %s",
                archivo.name,
            )
            continue

        fecha_archivo = match.group(1)
        if fecha_archivo != fecha_hoy:
            carpeta_hist = carpeta_hist_base / fecha_archivo
            carpeta_hist.mkdir(parents=True, exist_ok=True)
            destino = carpeta_hist / archivo.name
            move(str(archivo), destino)
            logger.info(
                "Movido a histórico (%s): %s",
                fecha_archivo,
                archivo.name,
            )
        else:
            archivo.unlink()
            logger.info(
                "Reemplazado archivo del mismo día: %s",
                archivo.name,
            )


def validar_entorno() -> None:
    """Valida que el backend y pyreverse estén disponibles."""
    rutas_requeridas = {
        "backend": CARPETA_BACKEND,
        "entorno virtual": CARPETA_ENTORNO,
        "pyreverse": PYREVERSE,
    }
    for nombre, ruta in rutas_requeridas.items():
        if not ruta.exists():
            msg = f"No se encontró {nombre}: {ruta}"
            raise FileNotFoundError(msg)


def generar_diagramas() -> None:
    """Ejecuta pyreverse para generar los diagramas UML en formato Mermaid (MMD)."""
    comando = [
        str(PYREVERSE),
        str(CARPETA_BACKEND),
        "-S",  # No asocia ancestros/dependencias externas ruidosas
        "-f", "PUB_ONLY",  # Muestra atributos y métodos públicos
        "-o", "mmd",  # Formato Mermaid compacto en texto plano
        "-p", "FitFlow",
        "--output-directory", str(CARPETA_DESTINO),
        "--ignore", "frontend,tests,migrations,static,media,scripts,utils,historico,.venv_backend,venv,env,build,dist,.venv_tools,._venv_sourcetrail",
    ]
    entorno = os.environ.copy()
    entorno["PYTHONPATH"] = str(RAIZ_PROYECTO)

    logger.info("Ejecutando pyreverse optimizado (Salida MMD)...")
    logger.info("Backend analizado: %s", CARPETA_BACKEND)
    logger.info("Salida: %s", CARPETA_DESTINO)

    resultado = subprocess.run(  # noqa: S603
        comando,
        cwd=RAIZ_PROYECTO,
        env=entorno,
        capture_output=True,
        text=True,
        check=True,
    )
    if resultado.stdout:
        logger.info("Salida de pyreverse:\n%s", resultado.stdout)
    if resultado.stderr:
        logger.warning("Advertencias de pyreverse:\n%s", resultado.stderr)


def renombrar_diagrama(
    nombre_original: str,
    nombre_final: str,
) -> bool:
    """Renombra un diagrama MMD generado agregando la fecha de ejecución."""
    archivo_origen = CARPETA_DESTINO / nombre_original
    if not archivo_origen.exists():
        logger.warning(
            "No se encontró el archivo generado: %s",
            archivo_origen,
        )
        return False

    archivo_destino = (
        CARPETA_DESTINO / f"{nombre_final}_{FECHA_HOY}.mmd"
    )
    archivo_origen.rename(archivo_destino)
    logger.info(
        "Diagrama Mermaid generado: %s",
        archivo_destino.name,
    )
    return True


# --------------------------------------------------------------------------- #
# PROCESO PRINCIPAL
# --------------------------------------------------------------------------- #
def main() -> None:
    """Genera y organiza los diagramas Mermaid del backend de FitFlow."""
    logger.info(
        "Analizando el backend para extraer clases y paquetes en MMD...",
    )
    validar_entorno()
    mover_a_historico_si_corresponde(
        CARPETA_DESTINO,
        CARPETA_HISTORICO_BASE,
        FECHA_HOY,
    )
    generar_diagramas()

    # pyreverse genera por defecto archivos con extensión .mmd
    renombrar_diagrama(
        "classes_FitFlow.mmd",
        "FitFlow_estructura_clases",
    )
    renombrar_diagrama(
        "packages_FitFlow.mmd",
        "FitFlow_estructura_paquetes",
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        logger.exception("Pyreverse finalizó con código %s.", error.returncode)
        if error.stdout:
            logger.exception("STDOUT:\n%s", error.stdout)
        if error.stderr:
            logger.exception("STDERR:\n%s", error.stderr)
    except FileNotFoundError:
        logger.exception("No se pudo completar la generación de diagramas.")
    except OSError:
        logger.exception("Error del sistema de archivos o del proceso.")

    # ---------------------------------------------------------
    # PREGUNTAR SI ABRIR CARPETA DE RESULTADOS
    # ---------------------------------------------------------
    try:
        respuesta = input("¿Querés abrir la carpeta donde se guardaron los archivos? (s/n): ").strip().lower()
        if respuesta == "s":
            import platform
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(str(CARPETA_DESTINO))  # noqa: S606
            elif sistema == "Darwin":
                subprocess.run(["open", str(CARPETA_DESTINO)], check=False)  # noqa: S603, S607
            else:
                subprocess.run(["xdg-open", str(CARPETA_DESTINO)], check=False)  # noqa: S603, S607
            logger.info("Carpeta abierta: %s", CARPETA_DESTINO)
        else:
            logger.info("No se abrirá la carpeta de resultados.")
    except Exception:
        logger.exception("Error al intentar abrir la carpeta de resultados.")
