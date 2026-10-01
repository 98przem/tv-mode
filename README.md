# TV mode

TV mode is a controller-first launcher for Steam Game Mode. It presents a
simple service dashboard and forwards controller navigation to browser-based
streaming services through a private Chrome DevTools connection.

Xbox Cloud is an exception. TV mode releases SDL before Xbox Cloud starts and
does not install a userscript or translate controller input for that service.
Chrome receives the physical controller directly.

## Documentation

- Read [`docs/INSTALL.md`](docs/INSTALL.md) for installation.
- Read [`docs/STEAMOS.md`](docs/STEAMOS.md) for a clean SteamOS setup.
- Read [`docs/SERVICE_AUDIT.md`](docs/SERVICE_AUDIT.md) for input and scaling status.
- Read [`docs/DECKY_PLAN.md`](docs/DECKY_PLAN.md) for the optional Decky plan.
- Read [`handoff/HANDOFF.md`](handoff/HANDOFF.md) before system migration.
- Read [`handoff/START_HERE_PL.md`](handoff/START_HERE_PL.md) after reinstalling SteamOS.
- Read [`docs/README.md`](docs/README.md) for documentation rules.

The project is designed for user-local installation on SteamOS, Bazzite, and
other Linux systems with Steam Game Mode, GTK4, SDL2, Python 3, and a
Chromium-compatible browser.

## Install

From a checkout:

```bash
./install.sh
```

The installer:

- detects native Chrome/Chromium or Flatpak Google Chrome;
- optionally installs the Chrome Flatpak when no browser is present;
- installs the launcher under `~/.local/share/tv-mode`;
- writes the service selection to `~/.config/tv-mode/services.json`;
- preserves the browser profiles and login state across reinstalls.

The service list is intentionally plain JSON so it can be edited without
rebuilding the application. Remove entries you do not want to show, or copy
one of the existing browser entries and change its URL, profile, and port.

## Requirements

The host needs Python 3 with GTK4 introspection and the `websockets` package,
SDL2, Steam, and a working X11-compatible Game Mode session. The installer
does not change system packages silently. On distributions without the
runtime dependencies, install the distribution packages first.

For the optional VacuumTube tile, install the `rocks.shy.VacuumTube` Flatpak.
Browser services remain available without VacuumTube.

## Steam shortcut

The launcher can be added as a non-Steam shortcut using:

```bash
python3 steam_shortcut.py
```

Steam Input should be disabled for the shortcut when the physical controller
is expected to be read directly by SDL.

## Project layout

- `tv_mode.py` — GTK dashboard, SDL polling, browser process management
- `scripts/netflix-focus.js` — Netflix DOM focus and player controls
- `services.json` — example service selection
- `install.sh` — repeatable user-local installation
- `uninstall.sh` — safe removal with optional data purge
- `steam_shortcut.py` — Steam shortcut registration

The installer and launcher contain no credentials. Authentication happens in
the isolated browser profiles on the local machine.
