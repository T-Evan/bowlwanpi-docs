#!/bin/bash
# Shared secret/env loader for local automation scripts.

set -u

load_secret_env() {
    local env_file
    for env_file in \
        "/root/.openclaw/.env" \
        "$HOME/.openclaw/.env" \
        "/root/.openclaw/workspace/.env"; do
        if [ -f "$env_file" ]; then
            # shellcheck source=/dev/null
            set -a
            . "$env_file"
            set +a
        fi
    done
}

require_env_vars() {
    local missing=0
    local key
    for key in "$@"; do
        if [ -z "${!key:-}" ]; then
            echo "❌ missing required env: $key" >&2
            missing=1
        fi
    done
    return $missing
}
