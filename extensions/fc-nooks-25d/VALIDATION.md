# Validation — v1.13.0

Integration, player-name/sprite, flight and goal-alignment browser suites passed for this release using Chromium 154 and Playwright 1.64.0. The unchanged scoreboard reader retains its previous passing standalone suite. The integration suite fulfills a local MFL-shaped page at an MFL match URL and executes scripts in manifest order. No credentials or live match data were used. `tests/results.log` records this release's results; all runtime JavaScript syntax checks pass.

## Passed checks

- A single native name below a player identifies possession directly, including when the ball is farther away; the overlay badge appears above the corresponding figure. Names inside player groups and separate SVG text are covered. Integration exercises this cue through the complete viewer.
- Surname attributes, full accessible names and exact lineup identities; compound surnames and missing-name hiding. Explicit possession markers/owner identities switch the badge; grounded-ball fallback suppresses loose balls, contests and aerial passes.
- Badge bounding height remains 21 screen pixels (20-pixel body plus stroke) at 1×, 1.75× and 2.5× and after resizing. Limbs follow actual native rendered travel, foot/ball anchors stay synchronized and stopped players return to a standing pose. Source replacement clears stale names.
- Injected name-reader errors hide only the surname badge while players, ball and score remain visible; restoring extraction recovers the label.

- New goal fixture reproduces a failure in v1.11: with a native `viewBox="-2 -2 109 72"` around an unmarked 105 × 68 field, native x=0 appears inside the overlay pitch. The corrected adapter uses the actual field and maps x=0/x=105 to the left/right goal mouths, including balls behind the nets.
- Correct goal-mouth placement across all eleven themes and three camera distances; translated fields, intermediate rendered movement and airborne balls behind both goals remain accurate. Hidden/defs shapes are excluded and replaced boundaries reconnect. A goal score update never overrides the native ball position.

- Close is the default. Actual rendered sprite height is 1.75× Full stadium, and Very close is 2.5×. Zoom preserves player transforms and nodes. Player/ball screen positions remain synchronized through camera changes during native CSS motion.
- Ball-following shots keep the ball visible at all four pitch corners, with camera bounds inside the local image. A 2.5× airborne shot retains the sphere and ground shadow together. Camera preference persists across reloads; invalid values fall back to Close and late reads cannot overwrite a newer user choice.

- Reliable toggle, opening/closing, keyboard controls, host replacement and SPA match navigation.
- All eleven packaged backdrops load. Switches during real 600 ms CSS transitions retain player/ball nodes, intermediate rendered coordinates and synchronization. Per-theme pitch calibration applies to both entities and static pitch geometry. Tiny grounds expose one physical display.
- 22-player discovery, desktop/mobile alignment, source parent transforms/scaling and explicit pitch bounds in a padded viewBox.
- Score/clock updates while the overlay stays open, goals propagated to all stadium displays, native top bar exposure and manual scoreboard selection. Separate tests cover glued React text, split clock/score digits, CSS-only separators, unnamed playback rows, full names, stoppage time, HT/FT and hidden stale copies. Replaced/hidden selected sources reconnect; unknown data clears rather than retaining stale scores.
- Flight through native shadow/sphere separation, nested SVG transforms and moving ground coordinates. One-frame source samples match the rendered lift without extra interpolation. Ball/shadow groups isolate the visible sphere; landing removes lift immediately. Ground coordinates and player-ball alignment remain consistent across all eleven themes. Unlabelled manually selected shadows work, including the UI picker for pointer-disabled decorative shadows; replacing the SVG clears stale selection.
- Minty photo input populates player heads, crowd pattern and banner without changing foot anchors. Photo preferences restore in another tab; other grounds hide face effects. Test input is a synthetic tiny PNG, not a substitute Minty likeness bundled in the release.
- Stadium preference persistence, invalid choices, late storage-response races, unavailable storage and missing-image recovery.
- Netted goal geometry, missing-ball hiding, manual ball selection and source replacement. No browser JavaScript exceptions in successful runs.

In the recorded motion run, all eight transition samples have player/ball projection errors below 0.001 scene units. This is fixture evidence, not a live MFL frame-rate or latency guarantee. Desktop/mobile screenshots and the new large/small/Minty backdrop renders were generated and inspected.

## Limits

Unpacked installation is blocked by this machine's browser administrator policy: `Loading of unpacked extensions is disabled by the administrator.` Tests mock `chrome.runtime.getURL` to locally fulfilled resources and `chrome.storage.local` to shared fixture state. They do not validate installed extension isolated-world execution, resource policy, actual Chrome/Edge installation or native extension storage permissions.

No authenticated MFL Pro match was available. Actual live player motion, score/clock markup, name/possession markup and ball/shadow structure remain unverified. The user confirms that the original ball is inside the goal in their screenshot; its exact native SVG bounds/anchors were unavailable, so the demonstrated padding defect is not claimed as the proven cause of that specific frame. Discovery uses source conventions from the supplied extension, with manual score/ball/shadow selection as fallbacks. Rendered scaling without a shadow gives only an approximate visual-height cue; that fallback is not the basis of the primary flight tests.

The pasted Minty avatar had no downloadable source file. No reconstructed face ships in this ZIP. Choose the original photo once using Minty's local photo chooser to activate face effects.

## Repeat the fixtures

From `extensions/fc-nooks-25d/tests`:

```sh
npm ci
node scoreboard.cjs
node flight.cjs
node goals.cjs
node players.cjs
node test.cjs
```

The runner uses `/usr/bin/chromium` when available, otherwise Playwright's browser. If you need Playwright's browser, install it with `npx playwright install chromium`; to select another binary, set `CHROMIUM_PATH` to its full path. This environment verified the system-Chromium route. In the cloud workspace use `npm ci --cache /workspace/.onboarding/npm-cache --no-audit --no-fund`, since its home cache is not writable. Test dependencies are unnecessary for loading the extension.

The integration runner generates ignored desktop/mobile PNGs. Tests do not send MFL requests outside the locally fulfilled fixture route.

## Live acceptance checks

1. Replay the reported goal after updating. Compare the same paused moment with original MFL and check Diagnostics `bounds` and `ball.source` if a discrepancy remains. Load unpacked following README; verify toggle, keyboard controls and locally loaded art.
2. Compare players and ball against original MFL through passing, possession, restarts, flight, landing and goals. Use **Set ball shadow** if the native shadow is unlabelled.
3. Confirm score and clock keep changing with 2.5D open. Use **Select scoreboard** if automatic detection misses the native row.
4. Try all three Camera choices, including flight and play near each goal; the shot should follow the ball and the broadcast scoreboard should stay visible. Switch grounds during play and resize; geometry and motion must remain aligned. Reload to check preference persistence.
5. Navigate to another match and away/back without refreshing; old players, selections and scores must clear.
6. Choose Minty's original photo; verify heads/crowd/banner and reload persistence. Switch to another ground to confirm ordinary player heads return.
7. Confirm the native surname shown below the carrier appears above the same player in 2.5D and switches on possession changes. Pause play to check figures stand still; test missing names and aerial passes.
8. If detection fails, capture Diagnostics and actual source SVG/header markup for an adapter correction. Do not fabricate match time or substitute guessed player motion.
