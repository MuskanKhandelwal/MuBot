#!/usr/bin/env bash
# Install the MuBot heartbeat as a twice-daily launchd agent (macOS).
#
# What it does:
#   1. Generates a .plist with the current project path
#   2. Installs it to ~/Library/LaunchAgents/
#   3. Loads it so it runs once now (RunAtLoad), then at 09:00 and 18:00 daily
#
# To change times: edit the StartCalendarInterval entries below and re-run.
# To check status: launchctl list | grep mubot
# To view logs:    tail -f logs/heartbeat.log logs/heartbeat.err.log
# To uninstall:    scripts/launchd/uninstall_heartbeat.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LABEL="com.muskan.mubot.heartbeat"
PLIST_NAME="${LABEL}.plist"
TARGET="${HOME}/Library/LaunchAgents/${PLIST_NAME}"

if [ ! -x "${PROJECT_ROOT}/venv/bin/python" ]; then
  echo "❌ venv not found at ${PROJECT_ROOT}/venv — create it first with: python -m venv venv && pip install -e ."
  exit 1
fi

mkdir -p "${PROJECT_ROOT}/logs"
mkdir -p "${HOME}/Library/LaunchAgents"

# Unload any existing version so we can refresh it
if [ -f "${TARGET}" ]; then
  echo "→ Unloading existing agent"
  launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
fi

cat > "${TARGET}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${PROJECT_ROOT}/venv/bin/python</string>
        <string>${PROJECT_ROOT}/src/mubot/scripts/run_heartbeat.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${PROJECT_ROOT}</string>

    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>9</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>18</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${PROJECT_ROOT}/logs/heartbeat.log</string>

    <key>StandardErrorPath</key>
    <string>${PROJECT_ROOT}/logs/heartbeat.err.log</string>

    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF

echo "→ Installed plist at ${TARGET}"

launchctl bootstrap "gui/$(id -u)" "${TARGET}"

echo ""
echo "✅ Heartbeat scheduled — runs once now, then daily at 09:00 and 18:00."
echo ""
echo "   View status:   launchctl list | grep mubot"
echo "   View logs:     tail -f ${PROJECT_ROOT}/logs/heartbeat.log"
echo "   Stop / remove: ${PROJECT_ROOT}/scripts/launchd/uninstall_heartbeat.sh"
