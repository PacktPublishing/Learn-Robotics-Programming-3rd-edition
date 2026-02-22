#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker is required but not found in PATH"
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required but not found in PATH"
    exit 1
fi

echo "[1/4] Starting MQTT broker"
docker compose up -d mqtt

# Give the broker a moment to bind and accept connections.
sleep 2

echo "[2/4] Starting pygame simulation"
uv sync --extra simulation
uv run python simulation.py &
SIM_PID=$!

echo "[3/4] Starting web control interface"
docker compose --profile web-interface up -d --build web-control

echo "[4/4] Starting robot services"
docker compose --profile robot-services up -d --build robot-services

cleanup() {
    if kill -0 "$SIM_PID" >/dev/null 2>&1; then
        echo
        echo "Stopping pygame simulation"
        kill "$SIM_PID" >/dev/null 2>&1 || true
        wait "$SIM_PID" 2>/dev/null || true
    fi
}

trap cleanup INT TERM EXIT

echo

echo "Simulation stack is running."
echo "- Pygame simulation: foreground process in this terminal"
echo "- Web control: http://localhost:8080"
echo "- Docker services stay running after this script exits"
echo

echo "Press Ctrl+C to stop the pygame simulation process."
echo "To stop Docker services later, run:"
echo "  cd local_tools/simulation && docker compose --profile web-interface --profile robot-services down"

wait "$SIM_PID"
