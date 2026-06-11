#!/usr/bin/env bash
# Install skills from this repo into Kiro (~/.kiro/skills/).
#
# Usage:
#   ./install.sh <skill-name> [<skill-name>...]   # install specific skills
#   ./install.sh --all                            # install every skill
#   ./install.sh --list                           # list available skills
#   ./install.sh --workspace <skill-name>...      # install into .kiro/skills/ of the current repo instead
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_ROOT/skills/skills"
DEST="$HOME/.kiro/skills"

if [ "${1:-}" = "--workspace" ]; then
  DEST="$(pwd)/.kiro/skills"
  shift
fi

if [ $# -eq 0 ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

if [ "$1" = "--list" ]; then
  for d in "$SKILLS_SRC"/*/; do
    [ -f "$d/SKILL.md" ] && basename "$d"
  done
  exit 0
fi

if [ "$1" = "--all" ]; then
  set -- $(for d in "$SKILLS_SRC"/*/; do [ -f "$d/SKILL.md" ] && basename "$d"; done)
fi

mkdir -p "$DEST"
installed=0
for name in "$@"; do
  src="$SKILLS_SRC/$name"
  if [ ! -f "$src/SKILL.md" ]; then
    echo "skip: '$name' not found (run ./install.sh --list to see available skills)" >&2
    continue
  fi
  rm -rf "${DEST:?}/$name"
  cp -R "$src" "$DEST/$name"
  echo "installed: $name -> $DEST/$name"
  installed=$((installed + 1))
done

echo "$installed skill(s) installed. Restart or reload Kiro to pick them up."
