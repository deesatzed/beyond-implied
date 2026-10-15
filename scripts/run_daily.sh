#!/bin/zsh
# Daily forward collection. Run by launchd after the close on weekdays (see scripts/launchd.plist).
# Pulls the latest code, refreshes the install, runs `bi daily`, and logs to data/logs/.
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
REPO="${BI_REPO:-$(cd "$(dirname "$0")/.." && pwd)}"

if [[ ! -d "$REPO/.git" ]]; then
  echo "$(date '+%F %T') repo not found at $REPO (volume not mounted?)" >&2
  exit 1
fi

cd "$REPO" || exit 1
mkdir -p data/logs
LOG="data/logs/daily-$(date +%F).log"
{
  echo "=== $(date '+%F %T %Z') start"
  git pull --ff-only -q || echo "git pull failed; running current checkout"
  uv pip install -q --python .venv/bin/python -e . || echo "install refresh failed"
  .venv/bin/bi daily
  echo "=== $(date '+%F %T %Z') exit $?"
} >> "$LOG" 2>&1
