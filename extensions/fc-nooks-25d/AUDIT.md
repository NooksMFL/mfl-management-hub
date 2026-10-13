# Audit of supplied FC-Nooks-2.5D-Extension-v1.5.zip

## Base selection

Only one archive was supplied. Its filename says v1.5; `manifest.json` declares 1.2.0 and `README.txt` says “v1.2 experimental movement alignment” and explicitly states that live-match verification has not been performed. There is no Git history or alternative release to compare. Consequently, no historical “last proven stable version” can be identified from this evidence.

The strongest available base is the uploaded `viewer.js` rendered-CTM foundation, retained in this refactor. The original uploaded archive is preserved unchanged alongside the working files; rebuilding did not modify it.

## Motion and ball synchronization worth preserving

Original `viewer.js`, lines 5745–5762: `svgPosition()` applies an element's `getScreenCTM()` and the root SVG's inverse screen matrix to a local point. This samples the actual CSS/SVG animation after nested transforms and screen scaling, rather than the next inline CSS transition target. Player positions use the circle centre. Ball positions use the graphic bounding-box centre, in the same root space.

Lines 5836–5845 and 5857–5886: `moveNode()` writes the sampled position directly; a single requestAnimationFrame samples players and ball together. `animateTracks()` deliberately does nothing. This is the correct foundation to retain: a second interpolation loop would trail an already animated source. The refactor keeps `svgPosition()`'s matrix calculation and direct placement; it replaces the old percentage-to-rectangle mapping with one deterministic stadium projection used by both entities and the field itself.

## Defects and regression risks visible in this source

- The 414,885-byte `viewer.js` combines lifecycle, extraction, renderers, styles/hooks and thousands of individual crowd primitives. The geometry is difficult to maintain and tune independently.
- `viewer.css` aligns a rectangular pitch using fixed percentages; mobile overrides change those percentages without changing the backdrop. The large backdrop seating/crowd shapes and the field have no shared geometric contract. This explains visual alignment risk, not a verified historical report.
- The two stadium screens contain literal `0 – 0` and `45:00`; only the floating board is live.
- `selectedBall` can reference a disconnected element indefinitely. `readSelectedBall()` returns null while automatic detection is bypassed, so the ball stays missing.
- Player caches are global rather than scoped to the chosen pitch. Bounds and ball candidates can persist while a SPA changes matches or replaces the source SVG. The refactor scopes and resets these references.
- UI observer watches only direct document-element child changes, missing normal body-child removal. The toggle gate only recognises `/matches/<id>`; an actual pitch in another route receives no toggle. Recovery now also detects the source pitch and observes host removal.
- Score extraction is restricted to compact uppercase abbreviations and runs every ~1.8 seconds. It can retain a prior score/clock when no current match header is recognised. The refactor refreshes every 250 ms and displays unknown values when extraction fails.
- The original entire backdrop is inline SVG. It contains no external stadium-image request. Failed external stadium image loading in another release cannot be diagnosed from this upload.
- Raw inline CSS-target reads or added interpolation would cause jumps/lag, but those regressions are not present in this archive's active movement code. Unused parsing/interpolation variables suggest earlier experiments; they do not establish historical behavior.

## Kept and replaced

Kept: rendered matrix sampling, player-circle and ball-bounds anchors, root viewBox fallback, MFL player ID convention, ball naming heuristics, manual ball selection, original-header score extraction, direct one-frame placement, toggle shortcut and view-only match behavior.

Replaced: giant monolithic scene, independent CSS pitch offsets, static side scoreboards, stale caches, nonrecovering lifecycle and page-style-dependent UI. New scene is original Harbour Park, with locally constructed SVG seating patterns, roof/truss geometry, floodlights, ad boards, dugouts, tunnel and netted goals. The source match engine and repository dashboard applications are untouched.


## v1.7: redesign after the Ricky video was supplied

The 16.5-second 1920 × 910 reference confirms a photographic stadium background rather than the vector aesthetic of v1.6. The earlier crowd patterns and simple roof did not match that visual quality. v1.7 replaces those visuals with an original generated photographic plate: coastal skyline, teal seating, dense spectators, two tiers, hospitality boxes, steel roof/floodlights, dugouts and tunnel. The image is packaged locally, with no external CDN dependency.

Live pitch lines, actors, ball, goal nets and the three score displays remain separate SVG layers, calibrated to the plate. One projective mapping covers the field rectangle; it is applied immediately to both moving entities and all static markings. Human figures are reduced to broadcast scale. Top controls and scoreboard occupy a compact bar so the stadium fills the viewer.

`tracking.js` and `scoreboard.js` are byte-for-byte unchanged from the tested v1.6 files. The rendered-CTM extraction foundation, one-frame sampling and no-added-smoothing policy are retained. Missing art reports a clear error and retains a local inline pitch, players, ball and scores. A photo of Ricky's stadium is not copied into the extension.


## v1.8: Ironwood Lane stadium replacement

Replaced the coastal Harbour Park plate with a genuinely different architectural theme: a traditional red-brick ground with claret seating, a gabled press box, brick corner towers, dark cantilever canopies, tall floodlight gantries and an industrial-town evening skyline. A photographic image edit preserved the exact 1672 × 941 camera framing, grass opening and blank-screen locations. The shared pitch projection and screen calibration remain unchanged.

`tracking.js`, `scoreboard.js` and `renderer.js` are byte-for-byte unchanged from v1.7. Changes are the locally packaged stadium image, asset references, stadium branding and the UI colour palette. No motion smoothing or animation clocks were added. The previous v1.7 ZIP remains in the repository for rollback.
