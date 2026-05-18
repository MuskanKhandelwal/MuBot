#!/usr/bin/env bash
# Uninstall the MuBot heartbeat launchd agent.
set -e

LABEL="com.muskan.mubot.heartbeat"
TARGET="${HOME}/Library/LaunchAgents/${LABEL}.plist"

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || echo "(agent was not loaded)"

if [ -f "${TARGET}" ]; then
  rm "${TARGET}"
  echo "✅ Removed ${TARGET}"
else
  echo "(no plist file to remove)"
fi
