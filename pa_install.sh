#!/bin/bash
# PA_install.sh
# Robust Auto-Installation Script for PythonAnywhere (Production Ready)

# Exit immediately if a command exits with a non-zero status
set -e

echo "======================================================="
echo "   HEXAFOX - PythonAnywhere Auto-Installer v2.0"
echo "======================================================="

# Detect Environment Variables
USER=$(whoami)
PROJECT_DIR=$(pwd)
VENV_PATH="$PROJECT_DIR/venv"
# We try to find the WSGI file. In PA it's usually at /var/www/<username>_pythonanywhere_com_wsgi.py
# But sometimes dashes are used. Usually it matches the domain name with underscores.
DOMAIN="${USER}.pythonanywhere.com"
WSGI_FILE="/var/www/${USER}_pythonanywhere_com_wsgi.py"

echo "[*] Detected Configuration:"
echo "    User:        $USER"
echo "    Project Dir: $PROJECT_DIR"
echo "    Domain:      $DOMAIN"
echo "    WSGI File:   $WSGI_FILE"

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
# Ensure python-dotenv is installed for env var management
pip install python-dotenv

# 3. Create .env file for Production Settings
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "\n[*] Creating Production .env file..."
    # Generate a random secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
    cat > "$ENV_FILE" <<EOF
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1
DJANGO_SECRET_KEY=$SECRET_KEY
EOF
    echo "    .env created with DEBUG=False and secure SECRET_KEY."
else
    echo -e "\n[*] .env file already exists. Skipping creation."
fi

# 4. Database Migrations
echo -e "\n[*] Running Database Migrations..."
python manage.py migrate

# 5. Static Files
echo -e "\n[*] Collecting Static Files..."
mkdir -p staticfiles
python manage.py collectstatic --noinput

# 6. Create Admin User (Optional / Interactive check)
echo -e "\n[*] Verifying Superuser..."
python << END
import os
import django
from dotenv import load_dotenv
# Explicitly load .env from current directory to avoid find_dotenv() error in stdin
load_dotenv(os.path.join(os.getcwd(), '.env'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hexafox_project.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    print("Creating default admin user (admin/jomberykaso)...")
    User.objects.create_superuser('admin', 'admin@example.com', 'jomberykaso')
else:
    print("Superuser already exists.")
END

# 7. Auto-Configure WSGI File
echo -e "\n[*] Configuring WSGI file..."
if [ -f "$WSGI_FILE" ]; then
    # Backup original
    cp "$WSGI_FILE" "${WSGI_FILE}.bak"
    
    # Overwrite with correct config that loads .env
    cat > "$WSGI_FILE" <<EOF
import os
import sys

# Add project directory to the sys.path
path = '$PROJECT_DIR'
if path not in sys.path:
    sys.path.append(path)

# Load .env file
from dotenv import load_dotenv
project_folder = os.path.expanduser('$PROJECT_DIR') 
load_dotenv(os.path.join(project_folder, '.env'))

# Set environment variable
os.environ['DJANGO_SETTINGS_MODULE'] = 'hexafox_project.settings'

# Import Django WSGI handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
EOF
    echo "[OK] WSGI file updated successfully."
else
    echo "[!] Warning: WSGI file not found at $WSGI_FILE."
    echo "    Please create the Web App in the PythonAnywhere 'Web' tab first."
    echo "    Once created, run this script again."
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

