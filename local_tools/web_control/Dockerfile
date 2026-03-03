FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY local_tools/pyproject.toml /app/pyproject.toml

RUN cd /app && uv pip install --system ".[web]"

COPY local_tools/web_control /app/local_tools/web_control

RUN mkdir -p /opt/web-libs && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    curl -L https://github.com/bobboteck/JoyStick/raw/master/joy.js -o /opt/web-libs/joy.js && \
    curl -L https://unpkg.com/mqtt@5.7.0/dist/mqtt.esm.js -o /opt/web-libs/mqtt.js && \
    curl -L https://cdn.jsdelivr.net/npm/chart.js -o /opt/web-libs/chart.js && \
    curl -L https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2 -o /opt/web-libs/chartjs-plugin-datalabels.js

EXPOSE 8080

CMD ["uvicorn", "local_tools.web_control.app:app", "--host", "0.0.0.0", "--port", "8080", "--reload", "--reload-dir", "/app/robot_control", "--reload-dir", "/app/local_tools/web_control"]