#!/bin/sh
# MQTT monitoring script - subscribes to broker statistics

set -e

# Install jq if not present
command -v jq >/dev/null 2>&1 || apk add --no-cache jq

# Read MQTT credentials from .env.json
USER=$(jq -r .MQTT_USERNAME /app/.env.json)
PASS=$(jq -r .MQTT_PASSWORD /app/.env.json)
echo "Using MQTT user: $USER"
# Subscribe to broker statistics topics with timestamps
mosquitto_sub -h mqtt -u "$USER" -P "$PASS" \
  -t '$SYS/broker/load/#' \
  -t '$SYS/broker/messages/#' \
  -t '$SYS/broker/clients/#' \
  -t '$SYS/broker/messages/stored' \
  -t '$SYS/broker/publish/messages/dropped' \
  -v | awk '{print strftime("%H:%M:%S"), $0; fflush()}'
