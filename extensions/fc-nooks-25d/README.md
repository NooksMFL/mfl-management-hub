# FC Nooks Match View 2.5D — v1.7.0

Harbour Park is an original, floodlit broadcast stadium overlay for MFL Pro. The stadium architecture, crowd, floodlights and dugouts use an original photographic backdrop packaged in `assets/harbour-park.jpg`. Live pitch markings, players, goals, nets and score displays are SVG constructed by packaged code. There are no remote image/CDN URLs, fonts, analytics, API requests or build steps in the extension. Keep the complete folder, including `assets`, when loading the extension.

## Install in Chrome or Edge

1. Unzip the release. Keep the resulting `fc-nooks-25d` folder in a permanent location.
2. Disable/remove the previous FC Nooks extension to avoid two versions drawing overlays.
3. Open `chrome://extensions` or `edge://extensions` and enable **Developer mode**.
4. Choose **Load unpacked** and select the folder containing `manifest.json`.
5. Reload the MFL tab, open a Pro match at `https://app.playmfl.com/`, and click **FC Nooks · 2.5D**.

Close with the Close button, the floating toggle, Escape, or Alt+Shift+M. The overlay is view-only: close it to use the original match controls. The underlying match stays mounted and continues animating; it is never hidden with `display:none` or moved out of its DOM.

When updating files, click **Reload** on the extension card and reload the MFL tab. Only one version should be enabled.

## Structure

- `tracking.js`: discovers MFL pitch/player/ball nodes, reads rendered screen CTMs, normalizes both entities against the same source bounds and recovers from replaced SVG nodes.
- `scoreboard.js`: reads original MFL score/clock text, excludes extension content and reports unavailable values instead of inventing or retaining a previous match score.
- `scene.js`: photographic backdrop calibration, live pitch markings, goals, displays, shared perspective projection, and inline image-failure fallback.
- `assets/harbour-park.jpg`: original local stadium art. Roof, crowds, dugouts and pitch texture are retained image pixels, not thousands of per-frame DOM elements.
- `renderer.js`: directly places player/ball sprites from one source snapshot. No extra smoothing, transitions, extrapolation or motion clock.
- `viewer.js`: shadow DOM interface, toggle, one requestAnimationFrame loop, ball selection, diagnostics and SPA lifecycle.
- `viewer.css`: isolated extension UI styling; listed as a packaged accessible resource so the shadow stylesheet can load.

Swap a stadium theme by replacing `buildScene()` while preserving its return contract (`svg`, `actors`, `ball`, `scale`, `updateScore`) and the shared `project(u,v)` function used for every pitch feature and moving entity. Do not add CSS transitions to actors or read raw inline translation targets.

## Ball selection and diagnostics

Automatic ball discovery retains support for MFL's `puck`, `football` and `ball` names. If no ball is detected, choose **Select ball** and click the actual ball graphic on the original SVG pitch. Selection expires after 15 seconds; Escape cancels it. Selection is cleared when the source SVG or match changes. A missing ball is hidden, never guessed from a player or the centre spot.

**Diagnostics** displays the source viewBox, player count, ball candidates, coordinate bounds and extracted scoreboard. It contains no token or authenticated network data. The diagnostics are inside the extension; there is no page-global debugging API.

## Validation and limits

See `AUDIT.md` for the original-code audit and `VALIDATION.md` for checks performed. Chromium fixture validation checks extension injection and real browser SVG/CSS animation, not an authenticated live MFL match. Chrome and Edge live-match verification remains necessary.

MFL DOM selectors are inferred from the supplied version, not a supported public MFL integration contract. Player IDs must still follow `match-v2-p<number>` and contain a circle. Coordinates use an explicit pitch marker when present, otherwise the original SVG viewBox / 105 × 68 fallback. If MFL introduces padded viewBoxes or changes its markup, update the adapter using an actual match DOM capture; do not tune stadium-specific CSS offsets.

Scoreboard extraction supports the supplied abbreviated header format and a full-name fallback, plus separate clock/timer elements. Unrecognised markup displays an em dash / unavailable clock. Match times are always extracted; no synthetic local match clock is run. Multiple simultaneous rendered match pitches select the first visible matching SVG; the standard workflow assumes one match pitch.

This is a lightweight fake 2.5D stadium, not a 3D engine. The supplied Ricky video (`screen-capture (6).mp4`) guided the v1.7 redesign: layered stands, hospitality ribbon, detailed roof, dense crowds, compact broadcast framing and slender player silhouettes. Harbour Park uses different coastal architecture and colours. This matches the visual approach, not the exact stadium or its source assets. Fine player depth occlusion and ball height are not available from the supplied source; the ball draws above player sprites for readability.
