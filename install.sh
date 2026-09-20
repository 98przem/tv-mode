#!/usr/bin/env bash
set -euo pipefail

PREFIX="${TV_MODE_PREFIX:-$HOME/.local/share/tv-mode}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/tv-mode"
SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

say() { printf 'tv-mode: %s\n' "$*"; }
die() { printf 'tv-mode: error: %s\n' "$*" >&2; exit 1; }

command -v python3 >/dev/null || die "python3 is required"

if [[ ! -e /usr/lib64/libSDL2-2.0.so.0 && ! -e /usr/lib/x86_64-linux-gnu/libSDL2-2.0.so.0 ]]; then
  say "SDL2 runtime was not detected; install SDL2 before launching TV mode."
fi

browser=""
for candidate in google-chrome google-chrome-stable chromium chromium-browser; do
  if command -v "$candidate" >/dev/null; then browser="$candidate"; break; fi
done
if [[ -z "$browser" ]] && command -v flatpak >/dev/null && flatpak info com.google.Chrome >/dev/null 2>&1; then
  browser="Flatpak Google Chrome"
fi
if [[ -z "$browser" ]]; then
  printf 'No supported browser was detected. Install Google Chrome Flatpak now? [Y/n] '
  read -r answer
  if [[ "${answer:-Y}" =~ ^[Yy]$ ]]; then
    command -v flatpak >/dev/null || die "Flatpak is unavailable; install a browser manually and rerun."
    flatpak install --user -y flathub com.google.Chrome
    browser="Flatpak Google Chrome"
  else
    die "A Chromium-compatible browser is required for browser services."
  fi
fi

mkdir -p "$PREFIX/scripts" "$CONFIG_DIR"
install -m 0755 "$SOURCE_DIR/launch" "$PREFIX/launch"
install -m 0755 "$SOURCE_DIR/tv_mode.py" "$PREFIX/tv_mode.py"
install -m 0755 "$SOURCE_DIR/steam_shortcut.py" "$PREFIX/steam_shortcut.py"
install -m 0644 "$SOURCE_DIR/scripts/netflix-focus.js" "$PREFIX/scripts/netflix-focus.js"
install -m 0644 "$SOURCE_DIR/scripts/browser-focus.js" "$PREFIX/scripts/browser-focus.js"
mkdir -p "$PREFIX/assets"
install -m 0644 "$SOURCE_DIR"/assets/*.svg "$PREFIX/assets/"
if [[ ! -e "$CONFIG_DIR/services.json" ]]; then
  install -m 0644 "$SOURCE_DIR/services.json" "$CONFIG_DIR/services.json"
fi
install -m 0644 "$SOURCE_DIR/99-tv-mode-8bitdo-input.rules" "$PREFIX/99-tv-mode-8bitdo-input.rules"

python3 "$SOURCE_DIR/configure_services.py" "$CONFIG_DIR/services.json"
if [[ "${TV_MODE_SKIP_STEAM_SHORTCUT:-0}" == 1 ]]; then
  say "Steam shortcut registration skipped by request."
else
  python3 "$PREFIX/steam_shortcut.py" || say "Steam shortcut registration was skipped; run it after starting Steam."
fi
say "installed to $PREFIX"
say "browser: $browser"
say "edit $CONFIG_DIR/services.json to change the selected services"
