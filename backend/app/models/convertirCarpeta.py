from pathlib import Path  # noqa: N999

# --------------------------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------------------------

# Carpeta donde está este script
carpeta_actual = Path(__file__).parent

# Nombre del script actual
este_script = Path(__file__).name

# Si el script termina en "Carpeta.py", también ignorará el archivo
# equivalente sin ese sufijo (ej.: ConvertirCarpeta.py -> Convertir.py)
script_sin_carpeta = este_script.replace("Carpeta.py", ".py")

# Nombre de la carpeta que se está convirtiendo
nombre_carpeta = carpeta_actual.name

# Carpeta destino
CARPETA_DESTINO = (
    Path(r"C:\Users\maued\Downloads\FitFlow Docs\Datos")
    / nombre_carpeta
)

# Crear la carpeta destino si no existe
CARPETA_DESTINO.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------
# CONVERSIÓN
# --------------------------------------------------------------------

contador = 0

for archivo_py in carpeta_actual.glob("*.py"):

    # Ignorar este script y su versión sin el sufijo "Carpeta"
    if archivo_py.name in (este_script, script_sin_carpeta):
        continue

    # Archivo de salida
    archivo_txt = CARPETA_DESTINO / archivo_py.with_suffix(".txt").name

    # Copiar el contenido
    codigo = archivo_py.read_text(encoding="utf-8")
    archivo_txt.write_text(codigo, encoding="utf-8")

    print(f"✔ {archivo_py.name} -> {archivo_txt.name}")
    contador += 1

# --------------------------------------------------------------------
# RESUMEN
# --------------------------------------------------------------------

print(f"\nProceso terminado.")  # noqa: F541
print(f"Se procesaron {contador} archivo(s).")
print(f"Los .txt se guardaron en:\n{CARPETA_DESTINO}")