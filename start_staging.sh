#!/bin/bash
set -x
PROJECT_DIR="/home/triyono/pondok-staging"
SOCK_FILE="$PROJECT_DIR/pondok_staging.sock"
PID_FILE="$PROJECT_DIR/gunicorn_staging.pid"
LOG_FILE="$PROJECT_DIR/gunicorn_staging.log"

cd $PROJECT_DIR

# Kill existing staging gunicorn
pkill -f "pondok_staging.sock"
sleep 2

# Cleanup
rm -f $SOCK_FILE $PID_FILE

# Start Gunicorn in background
# We bind to UNIX socket for potential Nginx proxy, 
# AND also bind to local tcp port 8001 for easy testing via curl if needed (optional, gunicorn supports multiple binds)
# But simpler: just Unix socket if we plan Nginx. 
# Or just TCP port 8001 if we want to bypass Nginx for now.
# User mentioned "dev.pondokindonesia...".
# Let's bind to 8001 for internal check, and sock for Nginx.
nohup .venv/bin/gunicorn \
    --bind unix:$SOCK_FILE \
    --bind 0.0.0.0:8001 \
    pondokindonesia.wsgi:application \
    --workers 2 \
    --log-level debug \
    --access-logfile $LOG_FILE \
    --error-logfile $LOG_FILE \
    > $LOG_FILE 2>&1 &

echo "Staging Gunicorn started. PID: $!"
sleep 2
ps aux | grep gunicorn
