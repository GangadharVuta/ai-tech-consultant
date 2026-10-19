# Stage 1: Build TypeScript Inbox Agent
FROM node:20-slim AS node-builder
WORKDIR /build/task2
COPY task2-inbox-agent/package*.json task2-inbox-agent/tsconfig.json ./
RUN npm ci
COPY task2-inbox-agent/src ./src
RUN npm run build

# Stage 2: Unified Production Runner
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install Node.js, Nginx, Supervisor, Curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    nginx \
    supervisor \
    ca-certificates \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Task 1: Knowledge Brain
COPY task1-knowledge-brain ./task1-knowledge-brain

# Copy Task 2: Inbox Agent (dependencies and compiled code)
COPY task2-inbox-agent/package*.json ./task2-inbox-agent/
WORKDIR /app/task2-inbox-agent
RUN npm ci --omit=dev
COPY --from=node-builder /build/task2/dist ./dist
COPY task2-inbox-agent/data ./data
WORKDIR /app

# Copy Task 3: Meeting to Scope
COPY task3-meeting-to-scope ./task3-meeting-to-scope

# Copy UI
COPY ui ./ui

# Configure Nginx & Supervisor
COPY deploy/nginx.conf.template /etc/nginx/nginx.conf.template
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY deploy/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && rm -f /etc/nginx/sites-enabled/default

# Default port: 7860 for Hugging Face Spaces; Render/Railway provide dynamic $PORT
ENV PORT=7860
EXPOSE 7860 8080 10000 80

CMD ["/app/entrypoint.sh"]
