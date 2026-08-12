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
CARPETA_TEMP = RAIZ_PROYECTO / "docs" / "historico" / "temp" / fecha_hoy
CARPETA_TEMP.mkdir(parents=True, exist_ok=True)

print("📄 Conversor FitFlow → TXT")
print("Ingresa el path completo del archivo que querés convertir:")
ruta_input = input("👉 Archivo origen: ").strip()

archivo_origen = Path(ruta_input)

# ---------------------------------------------------------
# VALIDACIÓN DEL ARCHIVO
# ---------------------------------------------------------

if not archivo_origen.exists():
    print(f"❌ Error: No se encontró el archivo en la ruta indicada: {archivo_origen}")
    raise SystemExit(1)

# Nombre final convertido
archivo_destino = CARPETA_TEMP / (archivo_origen.stem + ".txt")

# ---------------------------------------------------------
# CONVERSIÓN A TXT
# ---------------------------------------------------------

try:
    contenido = archivo_origen.read_text(encoding="utf-8")
    archivo_destino.write_text(contenido, encoding="utf-8")

    print(f"✅ Archivo convertido con éxito: {archivo_destino.name}")
    print(f"📍 Ubicación temporal: {CARPETA_TEMP}")

except UnicodeDecodeError:
    print("⚠️ El archivo no está en UTF-8. Intentando lectura binaria…")
    contenido = archivo_origen.read_bytes()
    archivo_destino.write_bytes(contenido)
    print(f"📄 Archivo convertido en modo binario: {archivo_destino.name}")

# ---------------------------------------------------------
# PREGUNTA ANTES DE ABRIR EXPLORADOR
# ---------------------------------------------------------

respuesta = input("¿Querés abrir la carpeta en el explorador? (s/n): ").strip().lower()

if respuesta == "s":
    try:
        subprocess.run(["explorer", str(CARPETA_TEMP)], check=False)
        print("🪟 Explorador de Windows abierto en la carpeta temporal.")
    except OSError as e:
        print(f"⚠️ No se pudo abrir el explorador automáticamente: {e}")
else:
    print("👌 Perfecto, no se abrirá el explorador.")