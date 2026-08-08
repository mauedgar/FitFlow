#!/usr/bin/env python3
"""convertir_carpeta.py.

Convierte recursivamente archivos .py a .txt manteniendo la estructura de subcarpetas.
Guarda los resultados en docs/historico/temp/<fecha>/<nombre_carpeta_origen>.
"""  # noqa: N999

from __future__ import annotations

import argparse
import logging
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ruff:noqa: S603
# ruff: noqa: S606
# ---------------------------------------------------------
# LOGGER DE MÓDULO (usar siempre este logger, no el root directamente)
# ---------------------------------------------------------
logger = logging.getLogger(__name__)

DEFAULT_DATE_FORMAT = "%d-%m-%y"


def setup_logging(log_file: Path) -> None:
    """Configura el logging con salida a consola y a archivo."""
    # Configuramos handlers para root logger; las llamadas posteriores deben usar `logger`.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def parse_args() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Convertir recursivamente .py a .txt manteniendo estructura",
    )
    parser.add_argument("origen", nargs="?", help="Ruta de la carpeta origen a convertir")
    parser.add_argument(
        "--fecha",
        help="Fecha a usar en la carpeta temporal en formato dd-mm-yy (por defecto: hoy UTC)",
    )
    parser.add_argument("--no-open", action="store_true", help="No abrir la carpeta destino al finalizar")
    return parser.parse_args()


def es_mi_script(path: Path, este_script_path: Path, script_sin_carpeta: str) -> bool:
    """Determina si la ruta corresponde al script actual (para evitar copiarlo)."""
    try:
        return path.resolve() == este_script_path.resolve()
    except (OSError, RuntimeError):
        return path.name in (este_script_path.name, script_sin_carpeta)


def abrir_explorador(path: Path) -> None:
    """Abre el explorador de archivos en la ruta indicada, de forma segura."""
    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(str(path))
            logger.info("Explorador abierto en: %s", path)
            return

        if sistema == "Darwin":
            exe = shutil.which("open")
            if exe:
                subprocess.run([exe, str(path)], check=False)
                logger.info("Explorador abierto en: %s", path)
                return
            logger.warning("Comando 'open' no encontrado en el sistema")

        exe = shutil.which("xdg-open")
        if exe:
            subprocess.run([exe, str(path)], check=False)
            logger.info("Explorador abierto en: %s", path)
            return

        logger.warning("No se encontró un comando para abrir el explorador en este sistema")
    except OSError:
        logger.exception("Error al intentar abrir el explorador para: %s", path)


def convertir_recursivo(carpeta_origen: Path, carpeta_destino: Path, este_script_path: Path) -> int:
    """Recorre recursivamente carpeta_origen y convierte cada .py a .txt en carpeta_destino."""
    contador = 0
    script_sin_carpeta = este_script_path.name.replace("Carpeta.py", ".py")

    logger.info("Iniciando recorrido recursivo en: %s", carpeta_origen)

    for archivo_py in carpeta_origen.rglob("*.py"):
        if es_mi_script(archivo_py, este_script_path, script_sin_carpeta):
            logger.debug("Ignorado (es el script actual): %s", archivo_py)
            continue

        try:
            relative_path = archivo_py.relative_to(carpeta_origen)
        except ValueError:
            relative_path = Path(archivo_py.name)

        destino_dir = carpeta_destino / relative_path.parent
        destino_dir.mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------
        # NUEVO: prefijo basado en la carpeta donde está el archivo
        # ---------------------------------------------------------
        carpeta_padre = relative_path.parent.name or carpeta_origen.name
        prefijo = carpeta_padre[:4].lower()  # primeras 4 letras
        nombre_txt = f"{prefijo}.{archivo_py.stem}.txt"

        archivo_txt = destino_dir / nombre_txt

        try:
            contenido = archivo_py.read_text(encoding="utf-8")
            archivo_txt.write_text(contenido, encoding="utf-8")
            logger.info(
                "Convertido: %s -> %s",
                archivo_py.relative_to(carpeta_origen),
                archivo_txt.relative_to(carpeta_destino),
            )
        except UnicodeDecodeError:
            try:
                contenido_bytes = archivo_py.read_bytes()
                archivo_txt.write_bytes(contenido_bytes)
                logger.info(
                    "Convertido (bytes): %s -> %s",
                    archivo_py.relative_to(carpeta_origen),
                    archivo_txt.relative_to(carpeta_destino),
                )
            except OSError:
                logger.exception("Error escribiendo bytes para: %s", archivo_py)
                continue
        except OSError:
            logger.exception("Error procesando: %s", archivo_py)
            continue

        contador += 1

    return contador



def main() -> None:
    """Punto de entrada principal del script."""
    args = parse_args()

    fecha_hoy = args.fecha or datetime.now(tz=timezone.utc).strftime(DEFAULT_DATE_FORMAT)

    try:
        este_script_path = Path(__file__).resolve()
    except NameError:
        este_script_path = Path(sys.argv[0]).resolve()

    carpeta_scripts = este_script_path.parent
    raiz_proyecto = carpeta_scripts.parent

    carpeta_temp_base = raiz_proyecto / "docs" / "historico" / "temp" / fecha_hoy
    carpeta_temp_base.mkdir(parents=True, exist_ok=True)

    log_file = carpeta_temp_base / "conversor_fitflow.log"
    setup_logging(log_file)

    # Usar el logger de módulo (no logging.info)
    logger.info("Inicio del conversor FitFlow → TXT")

    if args.origen:
        ruta_input = args.origen
    else:
        logger.info("Ingresá el path completo de la carpeta que querés convertir")
        ruta_input = input("👉 Carpeta origen: ").strip()

    carpeta_origen = Path(ruta_input).expanduser().resolve()
    if not carpeta_origen.exists() or not carpeta_origen.is_dir():
        logger.error("No se encontró la carpeta indicada: %s", carpeta_origen)
        raise SystemExit(1)

    carpeta_destino = carpeta_temp_base / carpeta_origen.name
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    procesados = convertir_recursivo(carpeta_origen, carpeta_destino, este_script_path)

    logger.info("Proceso terminado. Se procesaron %d archivo(s).", procesados)
    logger.info("Los .txt se guardaron en: %s", carpeta_destino)

    if not args.no_open:
        respuesta = "s" if args.origen else input("¿Querés abrir la carpeta en el explorador? (s/n): ").strip().lower()
        if respuesta == "s":
            abrir_explorador(carpeta_destino)
        else:
            logger.info("No se abrirá el explorador")


if __name__ == "__main__":
    main()
