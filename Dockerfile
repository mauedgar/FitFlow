# 1. Usar una imagen oficial de Python como base
FROM python:3.11-slim

# 2. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar el archivo de dependencias y el script de inicio
COPY ./backend/requirements.txt /app/
COPY ./backend/start.sh /app/

# 4. Instalar las dependencias de Python
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 5. Copiar todo el código de tu backend al contenedor
COPY ./backend /app

# 6. Dar permisos de ejecución al script de inicio
RUN chmod +x /app/start.sh

# 7. Exponer el puerto que usará Uvicorn
EXPOSE 8000

# 8. El comando que se ejecutará cuando el contenedor inicie
CMD ["/app/start.sh"]