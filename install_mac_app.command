#!/bin/zsh
set -e

APP_NAME="Job Agent"
PROJECT_DIR="/Users/anvikmacbookair/job_auto_agent"
SCRIPT_PATH="${PROJECT_DIR}/desktop_window.py"
FALLBACK_SCRIPT_PATH="${PROJECT_DIR}/desktop_app.py"
APP_DIR="${HOME}/Applications/${APP_NAME}.app"
LOG_PATH="${PROJECT_DIR}/data/runtime_logs/app_launch.log"

mkdir -p "${HOME}/Applications"
mkdir -p "${PROJECT_DIR}/data/runtime_logs"

/usr/bin/osacompile -o "${APP_DIR}" -e "do shell script \"/bin/zsh -lc '/usr/bin/env python3 \\\"${SCRIPT_PATH}\\\" start >> \\\"${LOG_PATH}\\\" 2>&1 || /usr/bin/env python3 \\\"${FALLBACK_SCRIPT_PATH}\\\" start >> \\\"${LOG_PATH}\\\" 2>&1'\""

echo "Installed: ${APP_DIR}"
echo "You can pin it in Dock and use like a normal app."
