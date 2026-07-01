#!/usr/bin/env bash
# Helper: commit all changes and push to remote
# Usage: ./git-push.sh "commit message"
set -euo pipefail

MSG="${1:-}"
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$MSG" ]; then
    echo "Uso: $0 \"mensaje del commit\""
    exit 1
fi

cd "$DIR"
git add -A
git commit -m "$MSG"
git push

echo "✓ Commit + push done: $MSG"
