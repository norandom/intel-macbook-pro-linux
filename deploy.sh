#!/usr/bin/env bash
# Run as the desktop user. pyinfra requests sudo only for privileged operations.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if (( EUID == 0 )); then
    echo "Run ./deploy.sh as your desktop user, without sudo." >&2
    exit 1
fi
if [[ ! -x .venv/bin/pyinfra ]]; then
    echo "Missing .venv/bin/pyinfra; set up the project environment first (see README.md)." >&2
    exit 1
fi
# Do not proactively request a password for previews; privileged facts may still need it.
for arg in "$@"; do
    if [[ "$arg" == --dry ]]; then
        exec .venv/bin/pyinfra @local deploy.py "$@"
    fi
done
exec .venv/bin/pyinfra @local deploy.py --use-sudo-password "$@"
