#!/bin/bash
set -e

INTERFACE=${ZEEK_INTERFACE:-eth0}
echo "[AegisNet-Zeek] Starting Zeek on interface: $INTERFACE"

zeek -i "$INTERFACE" /usr/local/zeek/share/zeek/site/local.zeek &

echo "[AegisNet-Zeek] Starting log forwarder to Redis..."
python3 /scripts/log_forwarder.py
