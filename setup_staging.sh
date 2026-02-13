#!/bin/bash
set -x
TARGET_DIR="/home/triyono/pondok-staging"
REPO_URL="git@github.com:rumahitindonesia/pondokindonesia.git"

echo "Starting Staging Setup..."

# Clean previous attempt
if [ -d "$TARGET_DIR" ]; then
    echo "Removing existing directory..."
    rm -rf $TARGET_DIR
fi

# Clone repository
echo "Cloning repository..."
git clone $REPO_URL $TARGET_DIR

# Verify clone
if [ ! -d "$TARGET_DIR" ]; then
    echo "ERROR: Clone failed! Directory not created."
    exit 1
fi

if [ ! -f "$TARGET_DIR/manage.py" ]; then
    echo "ERROR: Clone incomplete! manage.py not found."
    ls -la $TARGET_DIR
    exit 1
fi

cd $TARGET_DIR

# Setup Environment
echo "Configuring .env..."
cp /home/triyono/pondok-django/.env .env
sed -i 's/DEBUG=False/DEBUG=True/g' .env
# Remove existing DATABASE_URL if present to avoid conflict, relying on appended one
sed -i '/DATABASE_URL/d' .env
echo "DATABASE_URL=sqlite:///$TARGET_DIR/db.sqlite3" >> .env

# Setup Python Environment
echo "Setting up venv..."
python3 -m venv .venv

echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

echo "Running migrations..."
.venv/bin/python manage.py migrate

echo "Staging Setup Completed Successfully!"
