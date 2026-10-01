# Install on SteamOS

## Before you replace the disk

1. Push the current repository to its remote.
2. Copy the handoff archive to another disk or cloud storage.
3. Keep your passwords in your password manager.

The archive does not contain browser profiles, login sessions, passwords, or
tokens. Sign in to each service again on the new system.

## Prepare SteamOS

1. Install SteamOS with the official recovery image.
2. Complete the Steam first-run setup.
3. Open Desktop Mode.
4. Install all system updates.
5. Open Konsole.

Do not disable the SteamOS read-only system only to install TV mode. Prefer
Flatpak and user-local files. SteamOS updates can replace system changes.

## Install the applications

Install Google Chrome from Discover. You can also use these commands:

```bash
flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user flathub com.google.Chrome
```

Install VacuumTube only if you want the YouTube tile:

```bash
flatpak install --user flathub rocks.shy.VacuumTube
```

## Restore TV mode

Clone the repository:

```bash
git clone https://github.com/98przem/tv-mode.git
cd tv-mode
./install.sh
```

If the launcher reports a missing host dependency, install these Arch packages
only after you confirm that they are absent:

```bash
sudo steamos-readonly disable
sudo pacman -S --needed python python-gobject gtk4 python-websockets sdl2-compat xdotool git flatpak
sudo steamos-readonly enable
```

This package step changes the immutable base system. A SteamOS update can undo
it. Record the exact missing package and repeat only that part after an update.

## Configure Steam

1. Restart Steam after installation.
2. Open the `TV mode` shortcut properties.
3. Disable Steam Input for the shortcut.
4. Start TV mode.
5. Sign in to each browser service.

Steam Input must stay disabled. TV mode reads the controller through SDL for
its dashboard and supported browser navigation. Xbox Cloud is different: TV
mode closes SDL and sends no translated input while Xbox Cloud runs. Chrome
and Xbox Cloud receive the physical controller directly.

Use the Steam menu and Stop Game to leave Xbox Cloud. The View and Menu return
shortcut is intentionally inactive there.

## Optional 8BitDo rule

Use the included udev rule only if one physical controller exposes an extra
keyboard or mouse interface that causes duplicate input:

```bash
sudo install -m 0644 99-tv-mode-8bitdo-input.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Disconnect and reconnect the controller after installation. Review the rule
before use because its device identifiers can be model-specific.

Remove the rule with:

```bash
sudo rm /etc/udev/rules.d/99-tv-mode-8bitdo-input.rules
sudo udevadm control --reload-rules
```

## Verify

1. Confirm dashboard navigation with the physical controller.
2. Start Netflix and confirm its TV mode controls.
3. Start Xbox Cloud.
4. Confirm that Xbox Cloud detects the controller as a native gamepad.
5. Confirm that the Steam menu can stop Xbox Cloud.
6. Confirm that dashboard navigation resumes after Xbox Cloud closes.

## Remove

Run:

```bash
~/.local/share/tv-mode/uninstall.sh
```

The default removal keeps configuration and login profiles. See
`docs/INSTALL.md` for purge options.
