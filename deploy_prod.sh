#!/bin/bash
set -x
PROJECT_DIR="/home/triyono/pondok-django"

cd $PROJECT_DIR

echo "========================================"
echo "   STARTING PRODUCTION DEPLOYMENT"
echo "========================================"

echo "[1/5] Pulling latest code..."
git pull origin main

echo "[2/5] Updating dependencies..."
.venv/bin/pip install -r requirements.txt

echo "[3/5] Running database migrations..."
.venv/bin/python manage.py migrate

echo "[4/5] Collecting static files..."
.venv/bin/python manage.py collectstatic --noinput

echo "[5/5] Restarting Application..."
./deploy_restart.sh

echo "========================================"
echo "   PRODUCTION DEPLOYMENT COMPLETE"
echo "========================================"
