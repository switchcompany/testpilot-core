#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CENTRAL_PATH="$SCRIPT_DIR"

printf "\n🔄 Forge Core — Update\n"
printf "====================================\n\n"

if [[ -d "$CENTRAL_PATH/.git" ]]; then
  printf "Checking for central hub updates...\n"
  if git -C "$CENTRAL_PATH" pull --ff-only --quiet >/dev/null 2>&1; then
    printf "${GREEN}✅ Central hub updated from git${NC}\n"
  else
    printf "${YELLOW}ℹ️ Unable to fast-forward from git; using local files as-is${NC}\n"
  fi
else
  printf "${YELLOW}ℹ️ Not a git checkout; using local files as-is${NC}\n"
fi

if [[ $# -ge 1 ]]; then
  TARGET_PROJECT="$1"
  printf "\nRe-running setup for: %s\n\n" "$TARGET_PROJECT"
  "$CENTRAL_PATH/setup.sh" "$TARGET_PROJECT"
else
  printf "\nUsage: ./update.sh /path/to/project\n"
  printf "  - refreshes the central hub from git when possible\n"
  printf "  - reruns setup.sh for the provided project path\n"
  printf "\nRun without an argument when you only want to refresh the central hub.\n"
fi

printf "\n${GREEN}✅ Update complete${NC}\n\n"
