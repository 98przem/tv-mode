#!/usr/bin/env bash
set -euo pipefail

PREFIX="${TV_MODE_PREFIX:-$HOME/.local/share/tv-mode}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/tv-mode"
PROFILE_ROOT="$HOME/.var/app/com.google.Chrome/config"
PURGE_CONFIG=0
PURGE_PROFILES=0

say() { printf 'tv-mode: %s\n' "$*"; }
die() { printf 'tv-mode: error: %s\n' "$*" >&2; exit 1; }

for argument in "$@"; do
  case "$argument" in
    --purge-config) PURGE_CONFIG=1 ;;
    --purge-profiles) PURGE_PROFILES=1 ;;
    --purge-all) PURGE_CONFIG=1; PURGE_PROFILES=1 ;;
    *) die "unknown option: $argument" ;;
  esac
done

case "$PREFIX" in
  ""|/|"$HOME") die "unsafe install prefix: $PREFIX" ;;
esac

shortcut_tool="$PREFIX/steam_shortcut.py"
if [[ ! -f "$shortcut_tool" ]]; then
  shortcut_tool="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/steam_shortcut.py"
fi
if [[ "${TV_MODE_SKIP_STEAM_SHORTCUT:-0}" != 1 ]]; then
  python3 "$shortcut_tool" --remove || say "Steam shortcut removal was skipped; remove TV mode in Steam."
fi

rm -rf -- "$PREFIX"
say "removed program files from $PREFIX"

if (( PURGE_CONFIG )); then
  rm -rf -- "$CONFIG_DIR"
  say "removed configuration from $CONFIG_DIR"
else
  say "kept configuration in $CONFIG_DIR"
fi

if (( PURGE_PROFILES )); then
  for profile in netflix emby apple canal xbox-cloud; do
    rm -rf -- "$PROFILE_ROOT/tv-mode-$profile-profile"
  done
  say "removed TV mode browser profiles and login sessions"
else
  say "kept browser profiles and login sessions"
fi

say "restart Steam if the shortcut is still visible"
