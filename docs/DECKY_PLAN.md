# Decky Loader feasibility plan

## Decision

A Decky Loader plugin is feasible and can become the primary installer and
configuration interface. It cannot replace the complete TV mode runtime.

The plugin can:

- enable or disable each service;
- select one dashboard shortcut or separate Steam shortcuts;
- add, update, and remove non-Steam shortcuts;
- install and update the user-local runtime payload;
- show dependency and browser status;
- remove TV mode while preserving or deleting profiles;
- apply Steam artwork.

The runtime payload must still contain the Python launcher, browser focus
scripts, and service configuration. Chrome and the browser profiles must stay
outside the plugin frontend. A Decky panel is destroyed when it closes and is
not a reliable long-running application host.

## Proposed modes

### Dashboard mode

Create one `TV mode` Steam shortcut. The shortcut opens the current GTK
dashboard. The Decky panel selects the services shown in it.

Use this as the default. It keeps one library item and the existing return
behavior.

### Separate-shortcut mode

Create one Steam shortcut for each enabled service. Each shortcut calls the
same runtime with a service identifier, for example:

```text
launch --service netflix
launch --service xbox-cloud
```

The launcher skips the GTK dashboard and starts the selected service. Netflix,
Apple TV+, Canal+, and Emby keep their service-specific controller behavior.
Xbox Cloud keeps the strict native-gamepad path.

The Decky plugin must remove shortcuts for disabled services and preserve
browser profiles. Switching modes must not create duplicates.

## Architecture

1. A TypeScript and React frontend uses Decky UI components.
2. A small Python backend manages the runtime files and configuration.
3. The frontend uses Steam's `SteamClient.Apps` API for shortcut creation and
   updates where possible.
4. The backend owns atomic JSON writes and dependency checks.
5. The runtime remains a versioned payload in a user-local data directory.
6. The plugin and runtime share one schema for service identifiers and modes.

Do not edit `shortcuts.vdf` while Steam is running when the supported frontend
API is available. Confirm shortcut changes by reading them back. Warn the user
when Steam must restart to persist changes.

## Configuration model

Store settings similar to:

```json
{
  "layout": "dashboard",
  "services": {
    "youtube": true,
    "netflix": true,
    "emby": true,
    "apple": false,
    "canal": false,
    "xbox-cloud": true
  }
}
```

Do not store credentials. Browser profiles remain in their existing isolated
directories.

## Xbox Cloud rule

The plugin must not introduce input handling for Xbox Cloud. A dedicated Xbox
shortcut must launch the same native-input code path as dashboard mode. Steam
Input must remain disabled for every shortcut that can start Xbox Cloud.

## Delivery phases

1. Add `launch --service ID` and test it without Decky.
2. Add a configuration schema and idempotent shortcut manager.
3. Build a local Decky development plugin with service switches.
4. Add dashboard versus separate-shortcut mode.
5. Add runtime installation, update, and uninstall actions.
6. Test Stable SteamOS and the current Steam client on physical hardware.
7. Package a signed or checksummed release ZIP.
8. Consider Decky Plugin Store submission only after local use is stable.

## Risks

- Decky relies on Steam UI internals that can change after Steam updates.
- Shortcut APIs can require a Steam restart before changes persist.
- A custom Python backend increases plugin review and maintenance work.
- Decky installation itself requires an initial Desktop Mode setup and elevated
  installation step.
- Direct-service shortcuts increase library clutter and artwork maintenance.
- Service DOM changes remain independent of Decky.

## Recommendation

Keep the current script installer as a recovery and developer path. Add Decky
as an optional control plane after TV mode runtime behavior is stable. Use
dashboard mode by default and let advanced users select separate shortcuts.

## Sources

- [Official Decky plugin template](https://github.com/SteamDeckHomebrew/decky-plugin-template)
- [Decky frontend SteamClient application API](https://github.com/SteamDeckHomebrew/decky-frontend-lib/blob/main/src/globals/steam-client/App.ts)
- [Decky Loader repository](https://github.com/SteamDeckHomebrew/decky-loader)
- [Working non-Steam shortcut plugin reference](https://github.com/danielcamilo1/decky-add-non-steam-games)
