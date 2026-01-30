#!/bin/bash
# PA_install.sh
# Robust Auto-Installation Script for PythonAnywhere

# Exit immediately if a command exits with a non-zero status
set -e

echo "======================================================="
echo "   HEXAFOX - PythonAnywhere Auto-Installer"
echo "======================================================="

# Detect Environment Variables
USER=$(whoami)
PROJECT_DIR=$(pwd)
VENV_PATH="$PROJECT_DIR/venv"
WSGI_FILE="/var/www/${USER}_pythonanywhere_com_wsgi.py"
DOMAIN="${USER}.pythonanywhere.com"

echo "[*] Detected Configuration:"
echo "    User: $USER"
echo "    Project Dir: $PROJECT_DIR"
echo "    Domain: $DOMAIN"
echo "    WSGI File: $WSGI_FILE"

# 1. Setup Virtual Environment
if [ ! -d "$VENV_PATH" ]; then
    echo -e "\n[*] Creating virtual environment..."
    python3 -m venv venv
else
    echo -e "\n[*] Virtual environment found."
fi

# 2. Activate & Install
echo "[*] Activating venv and installing dependencies..."
source "$VENV_PATH/bin/activate"
pip install -r requirements.txt --upgrade

# 3. Database Migrations
echo -e "\n[*] Running Database Migrations..."
python manage.py migrate

# 4. Static Files
echo -e "\n[*] Collecting Static Files..."
# Ensure static assets dir exists
mkdir -p staticfiles
python manage.py collectstatic --noinput

# 5. Create Admin User (Optional / Interactive check)
# Check if admin exists to avoid errors or prompts
echo -e "\n[*] Verifying Superuser..."
# We run a small python snippet to create superuser if not exists
python << END
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hexafox_project.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    print("Creating default admin user (admin/jomberykaso)...")
    User.objects.create_superuser('admin', 'admin@example.com', 'jomberykaso')
else:
    print("Superuser already exists.")
END

# 6. Auto-Configure WSGI File
echo -e "\n[*] Configuring WSGI file..."
if [ -f "$WSGI_FILE" ]; then
    # Backup original
    cp "$WSGI_FILE" "${WSGI_FILE}.bak"
    
    # Overwrite with correct config
    cat > "$WSGI_FILE" <<EOF
import os
import sys

# Add project directory to the sys.path
path = '$PROJECT_DIR'
if path not in sys.path:
    sys.path.append(path)

# Set environment variable
os.environ['DJANGO_SETTINGS_MODULE'] = 'hexafox_project.settings'

# Import Django WSGI handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
EOF
    echo "[OK] WSGI file updated successfully."
else
    echo "[!] Warning: WSGI file not found at $WSGI_FILE."
    echo "    Please check the 'Web' tab to create it automatically first."
fi

echo "======================================================="
echo "   INSTALLATION COMPLETE"
echo "======================================================="
echo "IMPORTANT: Go to the PythonAnywhere 'Web' tab and configure:"
echo ""
echo "1. Virtualenv:"
echo "   Enter path: $VENV_PATH"
echo ""
echo "2. Static files:"
echo "   URL:        /static/"
echo "   Directory:  $PROJECT_DIR/staticfiles"
echo ""
echo "3. Click the Green 'Reload' button at the top."
echo ""
echo "Your site should be live at: https://$DOMAIN"
echo "======================================================="

