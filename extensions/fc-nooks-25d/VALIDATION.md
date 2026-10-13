# Validation — v1.10.0

Three browser fixture suites passed using Chromium 154 and Playwright 1.64.0. The integration suite fulfills a local MFL-shaped page at an MFL match URL and executes scripts in manifest order. No credentials or live match data were used. `tests/results.log` records this release's results; all runtime JavaScript syntax checks pass.

## Passed checks

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

No authenticated MFL Pro match was available. Actual live player motion, score/clock markup and ball/shadow structure remain unverified. Discovery uses source conventions from the supplied extension, with manual score/ball/shadow selection as fallbacks. Rendered scaling without a shadow gives only an approximate visual-height cue; that fallback is not the basis of the primary flight tests.

The pasted Minty avatar had no downloadable source file. No reconstructed face ships in this ZIP. Choose the original photo once using Minty's local photo chooser to activate face effects.

## Repeat the fixtures

From `extensions/fc-nooks-25d/tests`:

```sh
npm ci
node scoreboard.cjs
node flight.cjs
node test.cjs
```

The runner uses `/usr/bin/chromium` when available, otherwise Playwright's browser. If you need Playwright's browser, install it with `npx playwright install chromium`; to select another binary, set `CHROMIUM_PATH` to its full path. This environment verified the system-Chromium route. In the cloud workspace use `npm ci --cache /workspace/.onboarding/npm-cache --no-audit --no-fund`, since its home cache is not writable. Test dependencies are unnecessary for loading the extension.

The integration runner generates ignored desktop/mobile PNGs. Tests do not send MFL requests outside the locally fulfilled fixture route.

## Live acceptance checks

1. Load unpacked following README; verify toggle, keyboard controls and locally loaded art.
2. Compare players and ball against original MFL through passing, possession, restarts, flight, landing and goals. Use **Set ball shadow** if the native shadow is unlabelled.
3. Confirm score and clock keep changing with 2.5D open. Use **Select scoreboard** if automatic detection misses the native row.
4. Switch grounds during play and resize; geometry and motion must remain aligned. Reload to check preference persistence.
5. Navigate to another match and away/back without refreshing; old players, selections and scores must clear.
6. Choose Minty's original photo; verify heads/crowd/banner and reload persistence. Switch to another ground to confirm ordinary player heads return.
7. If detection fails, capture Diagnostics and actual source SVG/header markup for an adapter correction. Do not fabricate match time or substitute guessed player motion.
