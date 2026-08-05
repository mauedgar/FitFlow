import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------
# CONFIGURACIÓN DE FECHA Y RUTAS BASE
# ---------------------------------------------------------

fecha_hoy = datetime.now(tz=timezone.utc).strftime("%d-%m-%y")

CARPETA_SCRIPTS = Path(__file__).resolve().parent
RAIZ_PROYECTO = CARPETA_SCRIPTS.parent

# Carpeta temporal histórica profesional
CARPETA_TEMP_BASE = RAIZ_PROYECTO / "docs" / "historico" / "temp" / fecha_hoy
CARPETA_TEMP_BASE.mkdir(parents=True, exist_ok=True)

print("📄 Conversor de carpeta FitFlow → TXT")
print("Ingresa el path completo de la carpeta que querés convertir:")
ruta_input = input("👉 Carpeta origen: ").strip()

carpeta_origen = Path(ruta_input)

# ---------------------------------------------------------
# VALIDACIÓN DE LA CARPETA
# ---------------------------------------------------------

if not carpeta_origen.exists() or not carpeta_origen.is_dir():
    print(f"❌ Error: No se encontró la carpeta indicada: {carpeta_origen}")
    raise SystemExit(1)

# Carpeta destino temporal
CARPETA_DESTINO = CARPETA_TEMP_BASE / carpeta_origen.name
CARPETA_DESTINO.mkdir(parents=True, exist_ok=True)

# Nombre del script actual para ignorarlo
este_script = Path(__file__).name
script_sin_carpeta = este_script.replace("Carpeta.py", ".py")

contador = 0

# ---------------------------------------------------------
# CONVERSIÓN DE ARCHIVOS
# ---------------------------------------------------------

for archivo_py in carpeta_origen.glob("*.py"):

    # Ignorar este script y su versión sin sufijo
    if archivo_py.name in (este_script, script_sin_carpeta):
        continue

    archivo_txt = CARPETA_DESTINO / archivo_py.with_suffix(".txt").name

    try:
        contenido = archivo_py.read_text(encoding="utf-8")
        archivo_txt.write_text(contenido, encoding="utf-8")
    except UnicodeDecodeError:
        contenido = archivo_py.read_bytes()
        archivo_txt.write_bytes(contenido)

    print(f"✔ {archivo_py.name} -> {archivo_txt.name}")
    contador += 1

# ---------------------------------------------------------
# RESUMEN
# ---------------------------------------------------------

print("\nProceso terminado.")
print(f"Se procesaron {contador} archivo(s).")
print(f"Los .txt se guardaron en:\n{CARPETA_DESTINO}")

# ---------------------------------------------------------
# PREGUNTA ANTES DE ABRIR EXPLORADOR
# ---------------------------------------------------------

respuesta = input("¿Querés abrir la carpeta en el explorador? (s/n): ").strip().lower()

if respuesta == "s":
    try:
        subprocess.run(["explorer", str(CARPETA_DESTINO)], check=False)
        print("🪟 Explorador de Windows abierto en la carpeta temporal.")
    except OSError as e:
        print(f"⚠️ No se pudo abrir el explorador automáticamente: {e}")
else:
    print("👌 Perfecto, no se abrirá el explorador.")
