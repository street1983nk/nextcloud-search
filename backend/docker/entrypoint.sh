#!/bin/sh
# Start the application out of the baked virtual environment.
#
# The first line of output names the binding mode. It costs one line and it
# answers the single most expensive question in an ExApp deployment: is the
# process unreachable because it crashed, or because it is listening somewhere
# nobody is looking? Neither the shared key nor the app secret is printed.
set -eu

if [ -n "${HP_SHARED_KEY:-}" ]; then
	echo "entrypoint: binding mode unix socket ${HP_EXAPP_SOCK:-/tmp/exapp.sock} (HaRP)"
else
	echo "entrypoint: binding mode tcp ${APP_HOST:-127.0.0.1}:${APP_PORT:-unset}"
fi

exec /app/.venv/bin/python -m findling.main
