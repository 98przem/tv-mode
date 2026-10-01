# Work history

This is a reconstructed project history. The complete raw chat transcript is
not stored in the repository. Detailed command and decision records from the
system are included in the migration archive as `.docs/actions.md` and
`.docs/daily/*.md`.

## Main decisions

1. TV mode became one controller-first Steam shortcut instead of many loosely
   managed browser launchers.
2. Services use isolated Chrome profiles so login state persists separately.
3. Steam Input is disabled so TV mode can read the physical controller.
4. Netflix required a dedicated navigation engine instead of the generic DOM
   walker.
5. Netflix catalog, detail modal, player HUD, timeline, language, speed, and
   episode pickers were iterated through physical-controller feedback.
6. Direct writes to `video.currentTime` caused Netflix M7375. Seeking now uses
   trusted timeline clicks.
7. Volume, report, player back, and fullscreen controls were removed from the
   Netflix controller focus set. Television or SteamOS controls volume.
8. Focus styling changed from bright blue to a restrained gray highlight.
9. Chrome uses a dark startup background and hidden browser scrollbars.
10. Steam Stop Game shutdown was changed to terminate the child process group
    without blocking on Chrome DevTools.
11. Xbox Cloud was separated from all controller translation. It receives the
    physical controller natively after TV mode releases SDL.
12. A safe uninstaller, SteamOS guide, handoff, and offline archive were added
    before the planned disk replacement.
13. Apple TV+ and Canal+ generic navigation was improved with unrestricted
    directional scoring, trusted DevTools clicks, iframe key forwarding,
    LB/RB page movement, and the gray focus style.

## Accepted state

The user accepted the final Netflix navigation after several regressions were
removed. Episode selection works. A cosmetic focus jump to the first episode
after expansion can remain. Xbox native input and the latest Apple TV+/Canal+
changes require physical-controller confirmation.

## Collaboration rules

- Work in Polish.
- Make small changes and ask for short physical-controller tests.
- Avoid long turns and deep synthetic UI testing.
- Keep secrets, cookies, browser profiles, and authentication screens out of
  logs, Git, screenshots, and migration archives.
- Commit and push accepted batches with the user's Git identity and no AI
  attribution.
