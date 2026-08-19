import logging
from pathlib import Path

# ---------------------------------------------------------
# CONFIGURACIÓN DE LOGGER
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ---------------------------------------------------------
# CONFIGURACIÓN DE RUTAS
# ---------------------------------------------------------

CARPETA_BASE = Path(r"C:\Proyectos Web\FitFlow\.continue\rules")
ARCHIVO_SALIDA = CARPETA_BASE / "concat_rules.txt"

# ---------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------------------------------------

def concatenar_archivos(origen: Path, destino: Path) -> None:
    if not origen.exists() or not origen.is_dir():
        logging.error(f"La carpeta no existe: {origen}")
        raise SystemExit(1)

    logging.info(f"Buscando archivos en: {origen}")

    # Crear archivo vacío (reemplaza si existe)
    destino.write_text("", encoding="utf-8")
    logging.info(f"Archivo de salida creado: {destino}")

    # Recorrer recursivamente
    for archivo in origen.rglob("*"):
        if archivo.is_file():
            try:
                contenido = archivo.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                contenido = archivo.read_bytes().decode("latin-1", errors="ignore")

            logging.info(f"Concatenando: {archivo.name}")

            with destino.open("a", encoding="utf-8") as f:
                f.write(f"# {archivo.name}\n")
                f.write(contenido)
                f.write("\n\n")  # separación entre archivos

    logging.info("Proceso completado correctamente.")


# ---------------------------------------------------------
# EJECUCIÓN
# ---------------------------------------------------------

if __name__ == "__main__":
    concatenar_archivos(CARPETA_BASE, ARCHIVO_SALIDA)
