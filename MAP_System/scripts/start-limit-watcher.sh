#!/bin/sh
# Start the limit watcher (TASK-080) in the background with a pidfile guard.
# Usage: MAP_System/scripts/start-limit-watcher.sh [interval-seconds]
#
# The pidfile check verifies /proc/<pid>/cmdline actually contains
# limit_watcher.py -- a bare `kill -0` gives false positives on PID reuse
# and false negatives from inside PID-namespace sandboxes (both bit us
# during the TASK-080 review).
set -u

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PIDFILE="$ROOT/.locks/limit-watcher.pid"
LOG="$ROOT/../logs/limit-watcher.log"
INTERVAL="${1:-60}"

mkdir -p "$ROOT/.locks" "$(dirname "$LOG")"

is_watcher() {
    # true only if the PID exists AND is actually a limit_watcher process
    [ -r "/proc/$1/cmdline" ] && tr '\0' ' ' < "/proc/$1/cmdline" \
        | grep -q "limit_watcher.py"
}

if [ -f "$PIDFILE" ]; then
    OLD="$(cat "$PIDFILE")"
    if is_watcher "$OLD"; then
        echo "limit watcher already running (pid $OLD)"
        exit 0
    fi
    echo "removing stale pidfile (pid $OLD is not a limit_watcher process)"
    rm -f "$PIDFILE"
fi

# -u: unbuffered so the log reflects liveness immediately
nohup python3 -u "$ROOT/scripts/limit_watcher.py" --interval "$INTERVAL" \
    >> "$LOG" 2>&1 &
NEW=$!
echo "$NEW" > "$PIDFILE"

sleep 2
if is_watcher "$NEW"; then
    echo "limit watcher started and verified: pid $NEW, interval ${INTERVAL}s, log $LOG"
    echo "stop with: kill \$(cat $PIDFILE)"
else
    echo "ERROR: watcher exited immediately -- check $LOG" >&2
    rm -f "$PIDFILE"
    exit 1
fi
