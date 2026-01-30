#!/bin/bash
# PA_install.sh
# Script de auto-instalacion para PythonAnywhere

echo "[*] Iniciando instalacion..."

# 1. Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "[*] Creando entorno virtual..."
    python3 -m venv venv
fi

# 2. Activar entorno
echo "[*] Activando entorno virtual..."
source venv/bin/activate

# 3. Instalar dependencias
echo "[*] Instalando dependencias (versiones compatibles)..."
pip install -r requirements.txt

# 4. Migraciones
echo "[*] Ejecutando migraciones de base de datos..."
python manage.py migrate

# 5. Collect Static
echo "[*] Recopilando archivos estaticos..."
python manage.py collectstatic --noinput

echo "---------------------------------------------------"
echo "[OK] Instalacion completada con exito."
echo "Ahora ve a la pestaña 'Web' en PythonAnywhere y pulsa 'Reload'."
