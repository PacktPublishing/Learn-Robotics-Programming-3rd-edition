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

