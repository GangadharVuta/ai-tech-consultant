#!/bin/bash
set -e

PORT="${PORT:-7860}"
echo "[Deploy Orchestrator] Configuring Nginx on port $PORT..."
sed "s/LISTEN_PORT/$PORT/g" /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf

echo "[Deploy Orchestrator] Starting Task 1, Task 2, Task 3, and Web UI via Supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
