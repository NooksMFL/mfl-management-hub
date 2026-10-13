# Validation — v1.8.0

Executed in Chromium 154, with Playwright 1.64.0, against a locally fulfilled MFL-shaped page at an MFL match URL. No credentials or live match data were used. JavaScript syntax checks pass for all five runtime modules.

## Passed fixture checks

- Scripts execute in manifest order, create one toggle, and open the scene.
- Original header score and clock are extracted; all three stadium displays update from the same source.
- Player and ball rendered SVG matrices are sampled during a real 600 ms CSS transition, with nested parent translation and CSS-scaled source SVG. Intermediate positions are observed, so the renderer does not jump to the inline target.
- A player and ball at the same source coordinate remain aligned at all eight transition samples. Projection errors are below 0.001 scene units in the saved run; this is fixture evidence, not a live MFL timing guarantee.
- 22 player nodes are discovered and rendered.
- Responsive desktop/mobile scene mapping preserves player-ball alignment.
- The packaged photographic backdrop loads and is calibrated to the live pitch and screens.
- A deliberately missing stadium asset displays a clear notice while the inline pitch, players, ball and scoreboard continue rendering.
- Padded source viewBox with an explicit pitch bounds marker preserves coordinates.
- Manual selection recovers when the source SVG is replaced.
- Removed ball is hidden instead of retaining a phantom ball.
- SPA match changes update scores and clocks; an unrecognised scoreboard clears previous values.
- Leaving the match closes the viewer; removing its host restores it without duplicates.
- Alt+Shift+M and Escape operate the viewer.
- Both goal frames and their net geometry are present.
- No browser JavaScript exceptions occur in the successful run.

Desktop and mobile screenshots were generated and inspected. `tests/results.log` records the completed fixture run.

## Not verified here

Unpacked extension installation is blocked by this machine's browser administrator policy. The browser returned `Loading of unpacked extensions is disabled by the administrator.` The fixture therefore executes the packaged scripts with only `chrome.runtime.getURL` mocked to locally fulfilled packaged stylesheet and image URLs. It does not validate Chrome extension isolated-world execution, extension resource policy, actual installation, or Edge installation. The manifest declares Manifest V3, the MFL content-script target, and the packaged stylesheet as a web-accessible resource; these still require a user-browser load check.

Ricky's supplied video was inspected as the visual reference; desktop and mobile fixture renders were compared against its stadium style. No authenticated MFL Pro match was available. Real live player motion, actual ball markup, score/clock extraction and frame rate remain unverified. The implementation uses the supplied version's source conventions and preserves its rendered-position synchronization strategy.

## Repeat the browser fixture

From `tests/`, run:

```sh
npm ci
npx playwright install chromium
node test.cjs
```

If a system Chromium exists at `/usr/bin/chromium`, the runner uses it; otherwise it uses the Playwright browser. To choose another Chromium binary, set `CHROMIUM_PATH` to that binary's full path. The runner creates `ironwood-lane-desktop.png` and `ironwood-lane-mobile.png`. Test dependencies are not required to load or use the extension.

## Live acceptance check

Load unpacked as described in README. In an actual MFL Pro match:

1. Confirm the toggle appears, opens, closes and responds to Alt+Shift+M / Escape.
2. Watch players and the ball through passing, possession, restarts and a goal. Compare directly with the original pitch; neither should trail it.
3. Confirm team names, score and clock agree with MFL and all stadium displays update.
4. Resize the window; pitch lines, player positions and goals must stay aligned.
5. Navigate to another match without refreshing, then away from matches and back. No old players or old scores should remain.
6. If a live entity is missing, use Diagnostics and capture the source match SVG / header markup for an adapter correction. Do not substitute guessed motion or fabricate a match clock.
