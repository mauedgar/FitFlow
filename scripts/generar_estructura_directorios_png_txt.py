from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from shutil import move

# ============================================================
# CONFIGURACIÓN
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# DIRECTORIOS A IGNORAR
# ============================================================

IGNORAR_DIRECTORIOS: set[str] = {
    # Control de versiones
    ".git",
    "versions",

    # Entornos Python
    ".venv",
    ".venv_backend",
    ".venv_sourcetrail",
    "Fitflow.srctrlbm",
    "Fitflow.srctrldb",
    "Fitflow.srctrlprj",
    "venv",
    "env",

    # Scripts auxiliares
    "scripts",

    # Python / tooling
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".nox",

    # Node / frontend
    "node_modules",
    ".next",
    ".nuxt",
    ".turbo",

    # IDE
    ".idea",
    ".vscode",

    # Build / distribución
    "dist",
    "build",
    "out",
    "target",

    # Cachés
    ".cache",
    ".parcel-cache",

    # Coverage
    ".coverage",
    "htmlcov",
}


# ============================================================
# ARCHIVOS A IGNORAR
# ============================================================

IGNORAR_ARCHIVOS: set[str] = {
    ".DS_Store",
    "Thumbs.db",
}


IGNORAR_EXTENSIONES: set[str] = {
    ".pyc",
    ".pyo",
    ".log",
    ".tmp",
    ".temp",
}


# ============================================================
# RUTAS GENERADAS POR ESTE SISTEMA
# ============================================================

# Estas rutas NO deben aparecer dentro de los árboles.
#
# Especialmente importante para evitar que los TXT generados
# terminen describiéndose a sí mismos en la siguiente ejecución.
IGNORAR_RUTAS_RELATIVAS: set[Path] = {
    Path("docs/arquitectura/Estructura directorios"),
    Path("docs/historico/arquitectura"),
}


# ============================================================
# PROTECCIÓN CONTRA DIRECTORIOS EXTREMADAMENTE POBLADOS
# ============================================================

MAX_ELEMENTOS_POR_DIRECTORIO = 150


# ============================================================
# VALIDACIÓN DE FECHAS
# ============================================================

FECHA_RE = re.compile(r"^\d{2}-\d{2}-\d{2}$")


# ============================================================
# FILTROS
# ============================================================

def es_directorio_ignorado(
    path: Path,
    raiz: Path,
) -> bool:
    """Determina si un directorio debe excluirse del árbol."""
    if path.name in IGNORAR_DIRECTORIOS:
        return True

    try:
        relativa = path.relative_to(raiz)
    except ValueError:
        return False

    return any(
        relativa == ruta or ruta in relativa.parents
        for ruta in IGNORAR_RUTAS_RELATIVAS
    )


def es_archivo_ignorado(path: Path) -> bool:
    """Determina si un archivo debe excluirse del árbol."""
    if path.name in IGNORAR_ARCHIVOS:
        return True

    return path.suffix.lower() in IGNORAR_EXTENSIONES


# ============================================================
# LECTURA SEGURA DE DIRECTORIOS
# ============================================================

def obtener_hijos_visibles(
    carpeta: Path,
    raiz: Path,
) -> list[Path]:
    """Obtiene los elementos visibles de una carpeta.

    Los errores de permisos o filesystem no interrumpen
    todo el proceso.
    """
    try:
        hijos = list(carpeta.iterdir())

    except PermissionError:
        logger.warning(
            "Sin permisos para leer: %s",
            carpeta,
        )
        return []

    except FileNotFoundError:
        logger.warning(
            "La carpeta desapareció durante el recorrido: %s",
            carpeta,
        )
        return []

    except OSError as exc:
        logger.warning(
            "No se pudo leer %s: %s",
            carpeta,
            exc,
        )
        return []

    visibles: list[Path] = []

    for path in hijos:
        try:
            if path.is_dir():
                if es_directorio_ignorado(path, raiz):
                    continue

                visibles.append(path)
                continue

            if path.is_file() and not es_archivo_ignorado(path):
                visibles.append(path)

        except OSError as exc:
            logger.warning(
                "No se pudo inspeccionar %s: %s",
                path,
                exc,
            )

    return sorted(
        visibles,
        key=lambda p: (
            p.is_file(),
            p.name.lower(),
        ),
    )


# ============================================================
# CONSTRUCCIÓN DEL ÁRBOL
# ============================================================

def build_tree(
    root: Path,
    raiz_proyecto: Path | None = None,
    prefix: str = "",
) -> list[str]:
    """Construye el árbol de una carpeta.

    Se excluyen:
        - caches
        - entornos virtuales
        - node_modules
        - builds
        - IDEs
        - históricos
        - documentación generada

    Las carpetas extremadamente pobladas se resumen.
    """
    if raiz_proyecto is None:
        raiz_proyecto = root

    lines = [root.name]

    hijos = obtener_hijos_visibles(
        root,
        raiz_proyecto,
    )

    total_hijos = len(hijos)

    # --------------------------------------------------------
    # Directorio excesivamente poblado
    # --------------------------------------------------------

    if total_hijos > MAX_ELEMENTOS_POR_DIRECTORIO:

        logger.info(
            "Directorio muy poblado: %s (%d elementos). "
            "Se mostrará resumido.",
            root,
            total_hijos,
        )

        elementos_mostrados = hijos[
            :MAX_ELEMENTOS_POR_DIRECTORIO
        ]

        for index, path in enumerate(
            elementos_mostrados,
        ):
            last = (
                index
                == len(elementos_mostrados) - 1
            )

            branch = (
                "└── "
                if last
                else "├── "
            )

            lines.append(
                prefix
                + branch
                + path.name,
            )

        restantes = (
            total_hijos
            - MAX_ELEMENTOS_POR_DIRECTORIO
        )

        lines.append(
            prefix
            + "└── "
            + f"[... {restantes} elementos omitidos]",
        )

        return lines

    # --------------------------------------------------------
    # Recorrido normal
    # --------------------------------------------------------

    for index, path in enumerate(hijos):

        last = index == len(hijos) - 1

        branch = (
            "└── "
            if last
            else "├── "
        )

        lines.append(
            prefix
            + branch
            + path.name,
        )

        if not path.is_dir():
            continue

        extension = (
            "    "
            if last
            else "│   "
        )

        try:
            sub = build_tree(
                path,
                raiz_proyecto=raiz_proyecto,
                prefix=prefix + extension,
            )

            lines.extend(sub[1:])

        except RecursionError:
            logger.exception(
                "Se alcanzó el límite de recursión en: %s",
                path,
            )

            lines.append(
                prefix
                + extension
                + "└── [... recorrido interrumpido]",
            )

        except OSError as exc:
            logger.warning(
                "Error recorriendo %s: %s",
                path,
                exc,
            )

            lines.append(
                prefix
                + extension
                + "└── [... acceso no disponible]",
            )

    return lines


# ============================================================
# HISTÓRICO
# ============================================================

def extraer_fecha_desde_nombre(
    archivo: Path,
) -> str | None:
    """Extrae la fecha dd-mm-yy del final del nombre.

    Ejemplo:
        FitFlow_estructura_backend_08-08-26.txt
    """
    partes = archivo.stem.split("_")

    if len(partes) < 3:  # noqa: PLR2004
        return None

    fecha = partes[-1]

    if not FECHA_RE.fullmatch(fecha):
        return None

    return fecha


def mover_a_historico_si_corresponde(  # noqa: C901, PLR0912
    carpeta_origen: Path,
    carpeta_hist_base: Path,
    fecha_hoy: str,
) -> None:
    """Mueve TXT anteriores al histórico.

    Los archivos del día actual se eliminan para poder
    regenerarlos.

    Los archivos con nombres inesperados se conservan.
    """
    try:
        archivos = list(
            carpeta_origen.iterdir(),
        )

    except FileNotFoundError:
        logger.info(
            "No existe todavía la carpeta: %s",
            carpeta_origen,
        )
        return

    except PermissionError:
        logger.exception(
            "Sin permisos para leer: %s",
            carpeta_origen,
        )
        return

    except OSError as exc:
        logger.exception(
            "No se pudo leer %s: %s",
            carpeta_origen,
            exc,  # noqa: TRY401
        )
        return

    for archivo in archivos:

        if not archivo.is_file():
            continue

        # ----------------------------------------------------
        # Solo procesar TXT
        # ----------------------------------------------------

        if archivo.suffix.lower() != ".txt":
            continue

        fecha_archivo = (
            extraer_fecha_desde_nombre(
                archivo,
            )
        )

        # ----------------------------------------------------
        # Nombre inesperado
        # ----------------------------------------------------

        if fecha_archivo is None:

            logger.warning(
                "Archivo ignorado por no contener "
                "una fecha válida: %s",
                archivo.name,
            )

            continue

        # ----------------------------------------------------
        # Archivo del día actual
        # ----------------------------------------------------

        if fecha_archivo == fecha_hoy:

            try:
                archivo.unlink()

                logger.info(
                    "Archivo actual eliminado: %s",
                    archivo.name,
                )

            except FileNotFoundError:
                logger.warning(
                    "El archivo ya no existe: %s",
                    archivo,
                )

            except PermissionError:
                logger.exception(
                    "Sin permisos para eliminar: %s",
                    archivo,
                )

            except OSError as exc:
                logger.exception(
                    "No se pudo eliminar %s: %s",
                    archivo,
                    exc,  # noqa: TRY401
                )

            continue

        # ----------------------------------------------------
        # Archivo histórico
        # ----------------------------------------------------

        carpeta_hist = (
            carpeta_hist_base
            / fecha_archivo
            / "TXT"
        )

        try:
            carpeta_hist.mkdir(
                parents=True,
                exist_ok=True,
            )

            destino = (
                carpeta_hist
                / archivo.name
            )

            # No sobrescribir históricos existentes.
            if destino.exists():

                logger.warning(
                    "El archivo histórico ya existe: %s",
                    destino,
                )

                continue

            move(
                str(archivo),
                str(destino),
            )

            logger.info(
                "Movido a histórico (%s): %s",
                fecha_archivo,
                archivo.name,
            )

        except FileNotFoundError:
            logger.warning(
                "El archivo desapareció antes de moverlo: %s",
                archivo,
            )

        except PermissionError:
            logger.exception(
                "Sin permisos para mover: %s",
                archivo,
            )

        except OSError as exc:
            logger.exception(
                "No se pudo mover %s: %s",
                archivo,
                exc,  # noqa: TRY401
            )


# ============================================================
# GENERACIÓN DE TXT
# ============================================================

def generar_estructura(
    nombre: str,
    raiz: Path,
    carpeta_txt: Path,
    fecha_hoy: str,
    raiz_proyecto: Path,
) -> None:
    """Genera un TXT para una estructura concreta."""
    if not raiz.exists():

        logger.warning(
            "La ruta no existe, se omite: %s",
            raiz,
        )

        return

    if not raiz.is_dir():

        logger.warning(
            "La ruta no es un directorio, se omite: %s",
            raiz,
        )

        return

    try:

        arbol = build_tree(
            raiz,
            raiz_proyecto=raiz_proyecto,
        )

    except Exception:
        logger.exception(
            "Error construyendo estructura: %s",
            raiz,
        )

        return

    archivo_txt = (
        carpeta_txt
        / f"FitFlow_estructura_{nombre}_{fecha_hoy}.txt"
    )

    try:

        archivo_txt.write_text(
            "\n".join(arbol),
            encoding="utf-8",
        )

        logger.info(
            "TXT generado: %s",
            archivo_txt.name,
        )

    except OSError as exc:

        logger.exception(
            "No se pudo escribir %s: %s",
            archivo_txt,
            exc,  # noqa: TRY401
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Punto de entrada principal."""
    carpeta_scripts = (
        Path(__file__).resolve().parent
    )

    raiz_proyecto = (
        carpeta_scripts.parent
    )

    # --------------------------------------------------------
    # Directorio de documentación
    # --------------------------------------------------------

    base = (
        raiz_proyecto
        / "docs"
        / "arquitectura"
        / "Estructura directorios"
    )

    carpeta_txt = base / "TXT"

    historico_base = (
        raiz_proyecto
        / "docs"
        / "historico"
        / "arquitectura"
    )

    # --------------------------------------------------------
    # Crear directorios necesarios
    # --------------------------------------------------------

    try:

        carpeta_txt.mkdir(
            parents=True,
            exist_ok=True,
        )

        historico_base.mkdir(
            parents=True,
            exist_ok=True,
        )

    except OSError as exc:

        logger.critical(
            "No se pudieron crear las carpetas necesarias: %s",
            exc,
        )

        return

    # --------------------------------------------------------
    # Fecha
    # --------------------------------------------------------

    fecha_hoy = datetime.now(
        tz=timezone.utc
    ).strftime("%d-%m-%y")

    # --------------------------------------------------------
    # Histórico
    # --------------------------------------------------------

    mover_a_historico_si_corresponde(
        carpeta_txt,
        historico_base,
        fecha_hoy,
    )

    # --------------------------------------------------------
    # SOLO BACKEND Y FRONTEND
    # --------------------------------------------------------

    estructuras = {
        "backend": raiz_proyecto / "backend",
        "frontend": raiz_proyecto / "frontend",
    }

    # --------------------------------------------------------
    # Generación
    # --------------------------------------------------------

    for nombre, raiz in estructuras.items():

        generar_estructura(
            nombre=nombre,
            raiz=raiz,
            carpeta_txt=carpeta_txt,
            fecha_hoy=fecha_hoy,
            raiz_proyecto=raiz_proyecto,
        )

    logger.info(
        "Proceso completado. "
        "Se generaron únicamente las estructuras "
        "de backend y frontend."
    )

    # --------------------------------------------------------
    # Abrir carpeta destino
    # --------------------------------------------------------

    try:

        respuesta = input(
            f"\n¿Querés abrir la carpeta destino?\n"
            f"{base}\n"
            "(S/N): "
        ).strip().lower()

    except (EOFError, KeyboardInterrupt):

        logger.info(
            "Ejecución finalizada sin abrir carpeta."
        )

        return

    if respuesta != "s":
        return

    try:

        if os.name == "nt":
            os.startfile(base)  # type: ignore[attr-defined]

        elif os.name == "darwin":
            os.system(f'open "{base}"')  # noqa: S605

        else:
            os.system(f'xdg-open "{base}"')  # noqa: S605

    except Exception:

        logger.exception(
            "No se pudo abrir automáticamente: %s",
            base,
        )


if __name__ == "__main__":
    main()

