# TV mode handoff

## Goal

TV mode is a controller-first GTK 4 launcher for Steam Game Mode. It starts
VacuumTube and isolated Chrome profiles for streaming services.

The target is a polished television interface that works with a physical
controller and does not require a mouse or keyboard after sign-in.

## Current state

- The dashboard and service launcher work.
- Netflix catalog and player navigation were rebuilt and accepted by the user.
- Netflix seeking uses trusted clicks. Direct `video.currentTime` writes caused
  Netflix error M7375 and must not return.
- Browser profiles are isolated and persistent.
- Xbox Cloud uses native gamepad input. TV mode closes SDL before launch, does
  not install a userscript, and does not translate any Xbox Cloud buttons.
- TV mode restores SDL after Xbox Cloud closes.
- The Xbox Cloud change still needs a physical-controller test on the target
  Game Mode session.
- Installation is user-local. Uninstall keeps configuration and login profiles
  unless a purge option is selected.

## Non-negotiable rules

1. Do not place a userscript, key map, virtual controller, or input translator
   between the physical controller and Xbox Cloud.
2. Keep Steam Input disabled for the TV mode shortcut.
3. Use quick iterations. Make a small change and ask the user for one short
   physical-controller test.
4. Do not perform long synthetic user-interface tests.
5. Do not capture screens during sign-in or password entry.
6. Never store passwords, tokens, cookies, or browser profiles in Git or the
   handoff archive.
7. Preserve user changes in a dirty worktree.
8. Use Git identity `98przem <98przem@users.noreply.github.com>`.
9. Use short lowercase commit messages. Do not add AI attribution or a
   `Co-authored-by` line. Do not force-push unless the user requests it.
10. Document system actions in `/var/home/niusia/.docs` when that directory and
    its local instructions exist.

## Important files

- `tv_mode.py`: GTK dashboard, SDL polling, process control, Chrome DevTools.
- `scripts/netflix-focus.js`: Netflix catalog and player navigation.
- `scripts/browser-focus.js`: generic browser-service navigation.
- `services.json`: default services and per-service input mode.
- `install.sh`: user-local installer.
- `uninstall.sh`: safe uninstaller.
- `steam_shortcut.py`: adds or removes the Steam shortcut.
- `docs/STEAMOS.md`: clean-system setup.
- `docs/DECKY_PLAN.md`: feasibility and phased Decky Loader plan.
- `docs/SERVICE_AUDIT.md`: per-service controller and scaling audit.
- `handoff/WORK_HISTORY.md`: reconstructed discussion and decision history.

## Xbox Cloud design

The Xbox service has `"input": "native_gamepad"`. `load_services()` enforces
this value for old preserved configurations. Before launch, TV mode closes all
SDL controller handles and calls `SDL_Quit()`. During the Xbox child process,
controller polling, B handling, View plus Menu handling, browser forwarding,
and userscript installation are disabled. When the child exits, TV mode creates
a new `Controllers` instance.

Do not weaken this separation to improve Xbox web-page navigation. Native game
input has priority. Improve the page only with Xbox's own native interface or
an explicitly separate mode approved by the user.

## Known constraints

- Browser control depends on Chrome DevTools and page DOM outside Xbox Cloud.
- Streaming sites can change their DOM without notice.
- Netflix episode expansion can move focus to the first episode. This cosmetic
  behavior was accepted after selection started working.
- A SteamOS base update can remove packages installed with `pacman`.
- Browser login profiles are deliberately excluded from migration material.

## First checks on the new system

1. Read `README.md`, `docs/STEAMOS.md`, and this file.
2. Run `git status --short` and `git log -5 --oneline`.
3. Run the static checks listed in `handoff/AI_PROMPT.md`.
4. Install with `./install.sh`.
5. Disable Steam Input for the shortcut.
6. Ask the user to test Xbox Cloud native controller detection first.
7. If it fails, inspect device access and process ownership. Do not add input
   translation as a workaround.
