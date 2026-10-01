# Service input and scaling audit

## Scope

This audit reviews the controller and layout paths in the source. A physical
controller test is still required because the services can change their web
interfaces without notice.

## Results

| Service | Controller path | Scaling path | State |
| --- | --- | --- | --- |
| YouTube | Native VacuumTube controller support | Native application window | Previously confirmed |
| Netflix | Dedicated DOM focus and trusted DevTools clicks | Native page scale; player menus limited to 82% and 76 viewport height | Confirmed by user |
| Emby | DevTools keyboard events | Native responsive web layout | Previously confirmed |
| Apple TV+ | Generic spatial focus, trusted clicks, iframe key forwarding | Chrome kiosk viewport | Needs short physical test |
| Canal+ | Generic spatial focus and trusted clicks | Chrome kiosk viewport | Needs short physical test |
| Xbox Cloud | Direct physical gamepad; no SDL, userscript, or translation while active | Native Xbox Cloud responsive layout | Needs short physical test |

## Generic browser improvements

- Directional movement considers all controls in the requested half-plane.
- Distance scoring favors the nearest item in the intended direction without a
  narrow row or column restriction.
- A uses a trusted Chrome DevTools click.
- Cross-origin sign-in frames receive directional key events after focus.
- LB and RB move one page and select a visible item.
- Initial focus is retried during page startup.
- Focus uses the restrained gray TV mode style.
- Visible modal content isolates navigation from controls behind it.

## Scaling decision

Do not force a fixed browser zoom. Chrome kiosk mode supplies the actual
viewport and the services use their responsive layouts. A forced device scale
can clip cookie dialogs, sign-in frames, and player menus.

The GTK dashboard uses a maximum of three 340 by 190 logical-pixel tiles and
two rows for the six default services. The complete grid is 1068 logical pixels
wide and 404 logical pixels high before the header and legend. It fits the
1280 by 720 Game Mode baseline. GTK and Gamescope apply display scaling to
logical pixels on higher-density displays.

Netflix is the only page with a targeted size correction. Its player pickers
were too large, so those containers use 82% zoom and a maximum height of 76% of
the viewport. Catalog modals retain the site's native scale.

## Physical test sequence

For Apple TV+ and Canal+:

1. Confirm that the initial gray highlight appears.
2. Move through two rows in all four directions.
3. Open and close one detail modal.
4. Start one item and return with B.
5. Open a sign-in or consent frame only if it is already safe to show.

For Xbox Cloud:

1. Confirm native controller detection.
2. Confirm game and Xbox interface input.
3. Stop the application through the Steam menu.
4. Confirm dashboard controller input after return.
