FROM python:3.14-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy simulation project file and robot code
COPY simulation/pyproject.toml /app/pyproject.toml
COPY robot/ /app/robot/

# Install dependencies from the internal group
# This includes paho-mqtt, ujson, and numpy for robot services
RUN cd /app && uv pip install --system ".[internal]"

# Set PYTHONPATH so robot modules can be imported
ENV PYTHONPATH=/app/robot

# Default command (can be overridden to run specific robot services)
CMD ["python3"]
