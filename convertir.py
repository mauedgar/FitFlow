from pathlib import Path

# 1. Configura el archivo .py de origen (debe estar en la misma carpeta que este script)
NOMBRE_ARCHIVO_PY = "README.md"

# 2. CONFIGURA AQUÍ TU CARPETA DE DESTINO
# Opción B (Alternativa): Una ruta exacta de tu PC (ejemplo para Windows)
CARPETA_DESTINO = Path(r"C:\Users\maued\Downloads\FitFlow Docs")


# --- PROCESO DE COPIA ---
archivo_origen = Path(__file__).parent / NOMBRE_ARCHIVO_PY

if archivo_origen.exists():
    # Crea la carpeta de destino si no existe
    CARPETA_DESTINO.mkdir(parents=True, exist_ok=True)
    
    # Define la ruta final del archivo .txt
    archivo_destino = CARPETA_DESTINO / Path(NOMBRE_ARCHIVO_PY).with_suffix(".txt").name
    
    # Lee el código y genera el archivo .txt en la nueva ubicación
    codigo = archivo_origen.read_text(encoding="utf-8")
    archivo_destino.write_text(codigo, encoding="utf-8")
    
    print(f"¡Éxito! Archivo guardado en: {archivo_destino}")
else:
    print(f"Error: No se encontró el archivo '{NOMBRE_ARCHIVO_PY}' en esta carpeta.")