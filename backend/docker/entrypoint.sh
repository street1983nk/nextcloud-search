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

# The container runs unprivileged, and a named volume keeps the ownership of the
# image directory it was mounted over. The image pre-creates the mount point AppAPI
# uses for this app id with the right owner, so the normal case is writable. A
# volume mounted anywhere else arrives owned by root, and then this process cannot
# write its index. Phase 1 stores nothing, so this is a warning and not a refusal
# to start, but it has to be one clear line now rather than a permission error in
# the middle of the first indexing run.
if [ -n "${APP_PERSISTENT_STORAGE:-}" ]; then
	# A plain "docker run" points the variable at a path that does not exist yet,
	# so creating it is part of the normal case and only its failure is news.
	mkdir -p "${APP_PERSISTENT_STORAGE}" 2>/dev/null || true
	if [ ! -w "${APP_PERSISTENT_STORAGE}" ]; then
		echo "entrypoint: warning, APP_PERSISTENT_STORAGE ${APP_PERSISTENT_STORAGE} is not writable by uid $(id -u)" >&2
	fi
fi

exec /app/.venv/bin/python -m findling.main
