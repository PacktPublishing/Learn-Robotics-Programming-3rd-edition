# Multi-stage Dockerfile for simulation services
FROM python:3.14-slim AS base

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy common files
COPY local_tools/pyproject.toml /app/pyproject.toml

# ===== Services target: Robot services =====
FROM base AS services

# Install supervisor for process management
RUN apt-get update && \
    apt-get install -y --no-install-recommends supervisor && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/log/supervisor

COPY robot/ /app/robot/

# Install dependencies from the services group
# This includes paho-mqtt, ujson, and numpy for robot services
RUN cd /app && uv pip install --system ".[services]"

# Copy supervisord configuration and simulation-specific launcher service
COPY local_tools/simulation/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY local_tools/simulation/launcher_service_supervisor.py /app/simulation/launcher_service.py

# Set PYTHONPATH so robot modules can be imported
ENV PYTHONPATH=/app/robot

# Default command runs supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# ===== Web target: Web control interface =====
FROM base AS web

# Install jinja2 for template rendering and curl for downloading libs
RUN pip install --no-cache-dir jinja2 && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy robot_control files and template rendering script
COPY robot_control /app/robot_control
COPY local_tools/simulation/.env.json /app/robot_control/.env.json
COPY local_tools/simulation/render_templates.py /app/render_templates.py

# Create libs directory and download JavaScript libraries
RUN mkdir -p /app/robot_control/libs && \
    curl -L https://github.com/bobboteck/JoyStick/raw/master/joy.js \
         -o /app/robot_control/libs/joy.js && \
    curl -L https://unpkg.com/mqtt@5.7.0/dist/mqtt.esm.js \
         -o /app/robot_control/libs/mqtt.js && \
    curl -L https://cdn.jsdelivr.net/npm/chart.js \
         -o /app/robot_control/libs/chart.js && \
    curl -L https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2 \
         -o /app/robot_control/libs/chartjs-plugin-datalabels.js

# Expose HTTP port
EXPOSE 8080

# Render templates and start web server
CMD python render_templates.py && python -m http.server 8080 -d /app/robot_control
