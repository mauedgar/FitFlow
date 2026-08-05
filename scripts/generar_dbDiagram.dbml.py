import logging  # noqa: INP001
from datetime import datetime, timezone
from pathlib import Path
from shutil import move

from sqlalchemy import MetaData, create_engine
from sqlalchemy.exc import OperationalError

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
# CONFIGURACIÓN DE RUTAS Y CONEXIÓN
# ---------------------------------------------------------
URL_CONEXION = "postgresql://fitflow_admin:159753Lu@127.0.0.1:5432/fitflow_db"
fecha_hoy = datetime.now(tz=timezone.utc).strftime("%d-%m-%y")

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_DIAGRAMA = RAIZ_PROYECTO / "docs" / "arquitectura" / "Diagrama BD"
CARPETA_DIAGRAMA.mkdir(parents=True, exist_ok=True)

CARPETA_HISTORICO_BASE = (
    RAIZ_PROYECTO / "docs" / "historico" / "arquitectura" / "Diagrama BD"
)
CARPETA_HISTORICO_BASE.mkdir(parents=True, exist_ok=True)

ARCHIVO_DBML = CARPETA_DIAGRAMA / f"FitFlow_diagrama_{fecha_hoy}.dbml"
ARCHIVO_DBDIAGRAM = CARPETA_DIAGRAMA / f"FitFlow_diagrama_{fecha_hoy}.dbdiagram"

# ---------------------------------------------------------
# FUNCIÓN: Mover archivos antiguos al histórico
# ---------------------------------------------------------
def mover_a_historico_si_corresponde(
    carpeta_origen: Path, carpeta_hist_base: Path, fecha_hoy: str,
) -> None:
    """Mueve archivos antiguos al histórico según la fecha actual."""
    for archivo in carpeta_origen.iterdir():
        if not archivo.is_file():
            continue

        partes = archivo.stem.split("_")
        fecha_archivo = partes[-1] if len(partes) >= 3 else None  # noqa: PLR2004

        if fecha_archivo != fecha_hoy:
            carpeta_hist = carpeta_hist_base / (fecha_archivo or "sin_fecha")
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
logger.info("Conectando a PostgreSQL...")

try:
    engine = create_engine(URL_CONEXION)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    mover_a_historico_si_corresponde(CARPETA_DIAGRAMA, CARPETA_HISTORICO_BASE, fecha_hoy)

    if not metadata.tables:
        logger.warning("No se encontraron tablas en la base de datos.")
    else:
        logger.info("Generando DBML...")

        lineas_dbml: list[str] = []

        for nombre_tabla, tabla in metadata.tables.items():
            lineas_dbml.append(f"Table {nombre_tabla} {{")

            for columna in tabla.columns:
                tipo_dato = str(columna.type).lower()
                propiedades = ["primary key"] if columna.primary_key else []
                props = f" [{', '.join(propiedades)}]" if propiedades else ""
                lineas_dbml.append(f"  {columna.name} {tipo_dato}{props}")

            lineas_dbml.append("}\n")

            for fk in tabla.foreign_keys:
                tabla_destino = fk.column.table.name
                columna_destino = fk.column.name
                lineas_dbml.append(
                    f"Ref: {nombre_tabla}.{fk.parent.name} > {tabla_destino}.{columna_destino}",
                )

        contenido = "\n".join(lineas_dbml)
        ARCHIVO_DBML.write_text(contenido, encoding="utf-8")
        ARCHIVO_DBDIAGRAM.write_text(contenido, encoding="utf-8")

        logger.info("DBML generado con éxito: %s", ARCHIVO_DBML.name)
        logger.info("Archivo .dbdiagram generado: %s", ARCHIVO_DBDIAGRAM.name)

except OperationalError as e:
    logger.exception("Error de conexión con PostgreSQL. Verifica Docker y puerto 5432.")
    logger.error("Detalle técnico: %s", e.orig)  # noqa: TRY400
# ---------------------------------------------------------
# MOVER Y RENOMBRAR ARCHIVOS PUML DE PYREVERSE
# ---------------------------------------------------------

CARPETA_PUML = RAIZ_PROYECTO / "docs" / "arquitectura"

archivo_clases = CARPETA_PUML / "classes_FitFlow.puml"
archivo_paquetes = CARPETA_PUML / "packages_FitFlow.puml"

if archivo_clases.exists():
    destino_clases = CARPETA_DIAGRAMA / f"FitFlow_clases_{fecha_hoy}.puml"
    move(str(archivo_clases), destino_clases)
    logger.info("Diagrama de clases movido: %s", destino_clases.name)

if archivo_paquetes.exists():
    destino_paquetes = CARPETA_DIAGRAMA / f"FitFlow_paquetes_{fecha_hoy}.puml"
    move(str(archivo_paquetes), destino_paquetes)
    logger.info("Diagrama de paquetes movido: %s", destino_paquetes.name)
