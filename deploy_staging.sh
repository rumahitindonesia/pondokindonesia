#!/bin/bash
set -x
PROJECT_DIR="/home/triyono/pondok-staging"

cd $PROJECT_DIR

echo "Pulling latest changes..."
git pull origin main

echo "Updating dependencies..."
.venv/bin/pip install -r requirements.txt

echo "Running migrations..."
.venv/bin/python manage.py migrate

echo "Restarting Staging Server..."
/home/triyono/start_staging.sh
