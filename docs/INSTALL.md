# Install TV mode

## Purpose

Use this guide to install TV mode on a new Linux system.

The guide uses short steps. It does not install system packages without your
approval.

## Supported systems

TV mode is designed for:

- SteamOS
- Bazzite
- Other Linux systems with Steam Game Mode or a similar full-screen session

The system must provide:

- Steam
- Python 3
- GTK 4 and GObject introspection
- SDL2
- The Python `websockets` package
- A Chromium-based browser, or Flatpak

## Install from a local checkout

1. Open a terminal.
2. Change to the project directory.
3. Run:

   ```bash
   ./install.sh
   ```

4. Select the services that you want to use.
5. Read the installer result.
6. Restart Steam if the new shortcut does not appear.

The installer uses these locations:

- Program files: `~/.local/share/tv-mode`
- Service list: `~/.config/tv-mode/services.json`
- Browser profiles: `~/.var/app/com.google.Chrome/config`

The installer keeps an existing service list. It does not replace your
selection during a later install.

## Browser install

The installer checks for these browsers:

1. Google Chrome
2. Google Chrome Stable
3. Chromium
4. Chromium Browser
5. Flatpak Google Chrome

If no browser is found, the installer asks if it can install Flatpak Google
Chrome. Answer `Y` to install it or `n` to stop.

## Select services

The example list includes:

- YouTube through VacuumTube
- Netflix
- Emby
- Apple TV+
- Canal+
- Xbox Cloud

The installer asks for service numbers. For example:

```text
2 4 6
```

This selects Netflix, Apple TV+, and Xbox Cloud.

You can edit the file after the install:

```bash
nano ~/.config/tv-mode/services.json
```

Restart TV mode after you change the file.

## Steam shortcut

The installer adds a non-Steam shortcut named `TV mode`.

If the shortcut does not appear:

1. Close Steam.
2. Run the installer again.
3. Start Steam.

Disable Steam Input for this shortcut when TV mode must read the controller
directly through SDL.

## First test

1. Start the `TV mode` shortcut in Steam.
2. Move left and right on the dashboard.
3. Press A to start a service.
4. Press B to return or exit.
5. Hold View and Menu for about 1.2 seconds to return to the dashboard.

## Remove TV mode

Remove the user-local program and configuration:

```bash
rm -rf ~/.local/share/tv-mode
rm -rf ~/.config/tv-mode
```

Remove the `TV mode` non-Steam shortcut from Steam.

Do not remove browser profiles if you want to keep service login sessions.

## Common problems

### The shortcut is not visible

Restart Steam. The shortcut is stored in the Steam user configuration.

### The controller does not work

Check that the controller is visible to Steam. Disable Steam Input for the
TV mode shortcut. Then restart TV mode.

### A browser service does not start

Check that Chrome or Chromium is installed. Check that the selected service
has a valid URL in `services.json`.

### Netflix controls do not work

Check that the Netflix profile is logged in. Start Netflix from TV mode, not
from a different browser profile.

### A service asks for login

Log in in the browser window. TV mode does not store passwords or tokens.
