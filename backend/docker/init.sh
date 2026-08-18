#!/bin/bash
# PID 1 of the container: start the two processes and tie their lifetimes together.
#
# This replaces supervisor, and not out of minimalism for its own sake. supervisor
# is a Debian Python package: it pulls a complete second python3 into the runtime
# image, 58 MB measured, in order to watch two processes that need one page of
# shell. On the 4 GB ARM box this app targets, that is a third of the image for a
# job the shell already does.
#
# What is given up is automatic restarting of a crashed program, and giving it up
# is deliberate. A container that exits gets restarted by Docker or by AppAPI with
# its state reset and one line in the log that says why. A process silently
# restarted inside a container that keeps answering its heartbeat is exactly the
# failure mode this project already pays attention to elsewhere: healthy on the
# outside, broken on the inside.
#
# bash rather than sh on purpose: `wait -n -p` is what makes this loop correct.
# The POSIX shell of this image cannot wait for "whichever child exits first", and
# polling with `kill -0` cannot tell a live child from an unreaped zombie.
set -uo pipefail

APP_COMMAND=/app/docker/entrypoint.sh
FRPC_COMMAND=/app/docker/harp_connect.sh

stopping=0

# Signals are forwarded instead of swallowed, so "docker stop" reaches uvicorn and
# frpc. Without this, PID 1 dies first and both children are left to the kill
# timeout, which turns every stop into a ten second wait.
forward_stop() {
	stopping=1
	if [[ -n "${frpc_pid:-}" ]]; then
		kill -TERM "${frpc_pid}" 2>/dev/null || true
	fi
	if [[ -n "${app_pid:-}" ]]; then
		kill -TERM "${app_pid}" 2>/dev/null || true
	fi
}
trap forward_stop INT TERM

"${FRPC_COMMAND}" &
frpc_pid=$!

"${APP_COMMAND}" &
app_pid=$!

status=0
while :; do
	# `wait -p` unsets the variable before it waits and only assigns it when a
	# child was actually reaped, so the reference below has to tolerate an unset
	# name. A signal that interrupts the wait leaves it unset, which is the case
	# every "docker stop" produces.
	wait -n -p finished_pid
	child_status=$?

	if [[ -z "${finished_pid:-}" ]]; then
		if ((child_status == 127)); then
			# No children left to wait for. Both are gone, the loop is done.
			break
		fi
		# A signal interrupted the wait and the trap above has run. The children
		# are on their way out; keep waiting for them.
		continue
	fi

	if [[ "${finished_pid}" == "${app_pid}" ]]; then
		if ((stopping == 1)); then
			# We asked for this exit, so whatever code the signal produced is not
			# a failure of the container.
			status=0
			echo "init: stop requested, the application exited with status ${child_status}"
		else
			status=${child_status}
			echo "init: the application exited with status ${child_status}, stopping the container"
		fi
		kill -TERM "${frpc_pid}" 2>/dev/null || true
		wait "${frpc_pid}" 2>/dev/null || true
		break
	fi

	if [[ "${finished_pid}" == "${frpc_pid}" ]]; then
		if ((stopping == 1)); then
			# Same signal, the tunnel simply went down first. Wait for the
			# application to follow instead of reporting a broken tunnel.
			continue
		fi
		if ((child_status == 0)); then
			# Without HP_SHARED_KEY harp_connect.sh logs one line and exits 0.
			# That is the manual install and the plain "docker run" case, and the
			# application alone keeps the container alive there.
			echo "init: no HaRP tunnel in this deployment, watching the application only"
			continue
		fi
		echo "init: the HaRP tunnel died with status ${child_status}, stopping the container" >&2
		# Under HaRP the application binds a unix socket, so without the tunnel the
		# container is running and unreachable at the same time. That state must
		# not look healthy.
		kill -TERM "${app_pid}" 2>/dev/null || true
		wait "${app_pid}" 2>/dev/null || true
		status=${child_status}
		break
	fi
done

exit "${status}"
