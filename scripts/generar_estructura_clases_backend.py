"""Genera diagramas UML de clases y paquetes del backend de FitFlow.

El script utiliza pyreverse desde el entorno virtual específico del backend
y almacena los diagramas generados en la documentación de arquitectura.
Los archivos anteriores se trasladan automáticamente al histórico según
su fecha de generación.
"""

import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from shutil import move

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE LOGGING
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE RUTAS
# ---------------------------------------------------------------------------

FECHA_HOY = datetime.now(tz=timezone.utc).strftime("%d-%m-%y")

# El script se encuentra directamente en:
# FitFlow/scripts/generar_estructura_clases_backend.py
CARPETA_SCRIPTS = Path(__file__).resolve().parent

# Desde scripts/ se alcanza la raíz del proyecto FitFlow.
RAIZ_PROYECTO = CARPETA_SCRIPTS.parent

CARPETA_BACKEND = RAIZ_PROYECTO / "backend"

# El entorno virtual pertenece actualmente al backend.
CARPETA_ENTORNO = CARPETA_BACKEND / ".venv_backend"

CARPETA_DESTINO = (
    RAIZ_PROYECTO
    / "docs"
    / "arquitectura"
    / "Estructura de Clases"
)

CARPETA_HISTORICO_BASE = (
    RAIZ_PROYECTO
    / "docs"
    / "historico"
    / "arquitectura"
    / "Estructura de Clases"
)

PYREVERSE = CARPETA_ENTORNO / "Scripts" / "pyreverse.exe"

PATRON_FECHA = re.compile(r"(\d{2}-\d{2}-\d{2})$")


# ---------------------------------------------------------------------------
# PREPARACIÓN DE DIRECTORIOS
# ---------------------------------------------------------------------------

CARPETA_DESTINO.mkdir(parents=True, exist_ok=True)
CARPETA_HISTORICO_BASE.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------------------------


def mover_a_historico_si_corresponde(
    carpeta_origen: Path,
    carpeta_hist_base: Path,
    fecha_hoy: str,
) -> None:
    """Mueve al histórico los archivos generados en fechas anteriores.

    Los archivos de la fecha actual se eliminan para permitir que la nueva
    ejecución genere una versión actualizada. Los archivos cuyo nombre no
    contiene una fecha válida al final del nombre se conservan y generan
    una advertencia en el registro.

    Args:
        carpeta_origen: Directorio donde se encuentran los archivos actuales.
        carpeta_hist_base: Directorio raíz donde se almacenan los históricos.
        fecha_hoy: Fecha de la ejecución en formato ``DD-MM-YY``.

    """
    for archivo in carpeta_origen.iterdir():
        if not archivo.is_file():
            continue

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
    """Valida que el backend y pyreverse estén disponibles.

    Raises:
        FileNotFoundError: Si no existe el backend, el entorno virtual o
            el ejecutable de pyreverse.

    """
    rutas_requeridas = {
        "backend": CARPETA_BACKEND,
        "entorno virtual": CARPETA_ENTORNO,
        "pyreverse": PYREVERSE,
    }

    for nombre, ruta in rutas_requeridas.items():
        if not ruta.exists():
            msg = f"No se encontró {nombre}: {ruta}"
            raise FileNotFoundError(
                msg,
            )


def generar_diagramas() -> None:
    """Ejecuta pyreverse para generar los diagramas UML del backend.

    El análisis se realiza sobre ``backend`` utilizando el ejecutable
    pyreverse perteneciente al entorno virtual del backend.

    Raises:
        subprocess.CalledProcessError: Si pyreverse finaliza con un código
            de error.
        FileNotFoundError: Si el ejecutable de pyreverse no está disponible.

    """
    comando = [
        str(PYREVERSE),
        str(CARPETA_BACKEND),
        "-f",
        "ALL",
        "-o",
        "puml",
        "-p",
        "FitFlow",
        "--output-directory",
        str(CARPETA_DESTINO),
    ]

    entorno = os.environ.copy()
    entorno["PYTHONPATH"] = str(RAIZ_PROYECTO)

    logger.info("Ejecutando pyreverse...")
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
    """Renombra un diagrama generado agregando la fecha de ejecución.

    Args:
        nombre_original: Nombre generado automáticamente por pyreverse.
        nombre_final: Nombre que tendrá el archivo documentado.

    Returns:
        ``True`` si el archivo fue encontrado y renombrado; ``False`` si
        el archivo original no existe.

    """
    archivo_origen = CARPETA_DESTINO / nombre_original

    if not archivo_origen.exists():
        logger.warning(
            "No se encontró el archivo generado: %s",
            archivo_origen,
        )
        return False

    archivo_destino = (
        CARPETA_DESTINO
        / f"{nombre_final}_{FECHA_HOY}.puml"
    )

    archivo_origen.rename(archivo_destino)

    logger.info(
        "Diagrama generado: %s",
        archivo_destino.name,
    )

    return True


# ---------------------------------------------------------------------------
# PROCESO PRINCIPAL
# ---------------------------------------------------------------------------


def main() -> None:
    """Genera y organiza los diagramas UML del backend de FitFlow.

    El proceso realiza las siguientes operaciones:

    1. Valida la estructura requerida del proyecto.
    2. Mueve al histórico los diagramas de ejecuciones anteriores.
    3. Ejecuta pyreverse utilizando el entorno virtual del backend.
    4. Renombra los diagramas agregando la fecha de generación.
    """
    logger.info(
        "Analizando el backend para extraer clases y paquetes...",
    )

    validar_entorno()

    mover_a_historico_si_corresponde(
        CARPETA_DESTINO,
        CARPETA_HISTORICO_BASE,
        FECHA_HOY,
    )

    generar_diagramas()

    renombrar_diagrama(
        "classes_FitFlow.puml",
        "FitFlow_estructura_clases",
    )

    renombrar_diagrama(
        "packages_FitFlow.puml",
        "FitFlow_estructura_paquetes",
    )
        # ---------------------------------------------------------
    # GENERAR VERSIONES .TXT DE LOS DIAGRAMAS
    # ---------------------------------------------------------
    for nombre_base in ("FitFlow_estructura_clases", "FitFlow_estructura_paquetes"):
        archivo_puml = CARPETA_DESTINO / f"{nombre_base}_{FECHA_HOY}.puml"
        archivo_txt = CARPETA_DESTINO / f"{nombre_base}_{FECHA_HOY}.txt"

        if archivo_puml.exists():
            try:
                contenido = archivo_puml.read_text(encoding="utf-8")
                archivo_txt.write_text(contenido, encoding="utf-8")
                logger.info("Archivo TXT generado: %s", archivo_txt.name)
            except Exception:
                logger.exception("Error generando TXT para: %s", archivo_puml.name)
        else:
            logger.warning("No se encontró el archivo PUML para convertir: %s", archivo_puml.name)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        logger.exception(
            "Pyreverse finalizó con código %s.",
            error.returncode,
        )

        if error.stdout:
            logger.exception(
                "STDOUT:\n%s",
                error.stdout,
            )

        if error.stderr:
            logger.exception(
                "STDERR:\n%s",
                error.stderr,
            )

    except FileNotFoundError:
        logger.exception(
            "No se pudo completar la generación de diagramas: %s",

        )

    except OSError:
        logger.exception(
            "Error del sistema de archivos o del proceso: %s",

        )
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


