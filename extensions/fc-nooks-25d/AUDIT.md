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


## v1.9: Selhurst Park and persistent stadium selector

Added a generated Selhurst Park-inspired red-and-blue scene and restored the packaged Harbour Park image alongside Ironwood Lane. A `stadiums.js` registry supplies names, asset paths and screen calibration. Selhurst Park's geometry is an artistic interpretation with approximate architectural detail. All three plates retain the calibrated camera and field opening.

The toolbar Stadium menu switches locally packaged backdrops and labels without recreating player/ball nodes, clearing tracker caches or changing the animation clock. New art decodes behind the existing scene; stale image events are ignored by a request revision. Missing art retains an inline pitch and supports selecting another stadium. Preference storage uses `chrome.storage.local`, with the Manifest V3 `storage` permission. A delayed read cannot overwrite a later user choice, and invalid saved values fall back to Selhurst Park.

`tracking.js`, `scoreboard.js` and `renderer.js` are byte-for-byte unchanged from v1.8. Shared field projection is unchanged. Browser fixture coverage now includes switching during motion, all three local images, storage persistence, invalid preferences, delayed reads, storage unavailability and failed-image recovery.


## v1.10: scoreboard binding, native ball flight and eleven stadiums

The user reports that MFL's original score bar works while the overlay scoreboard stalls. The old reader relied on named header/score wrappers and whitespace-separated team/score strings. Compact playback rows with glued React text, separately rendered digits or unnamed wrappers could fail extraction. Browser fixtures reproduce those format failures; exact authenticated MFL markup remains unavailable.

The new reader binds a native source, preserves text-node boundaries, discovers compact unnamed rows, ignores hidden copies and independently polls every 100 ms. Native top score content stays exposed and manual selection supplies a fallback. Parsing errors cannot reset tracks or stop motion. Navigation and responsive source replacement reconnect the reader; unknown scores remain unknown.

The ball previously had one bounding-box centre and was always drawn on the ground. The user confirms MFL shows flight through separation from a shadow. Tracking now reads shadow and sphere using the unchanged `svgPosition()` matrix function. Shadow centre anchors ground position; separation supplies visual lift. A combined ball/shadow group isolates its sphere. Manual shadow selection supports unlabelled markup. A rendered-size cue is a fallback, not a flight simulation. Player sampling and one requestAnimationFrame are retained without interpolation.

Seven new real-ground-inspired local images cover large and tiny grounds. Minty Stadium is an eighth addition, making eleven themes. Per-theme registry calibration changes one scene camera shared by markings, goals and actors. Switches rebuild static geometry while retaining actor nodes and tracker state. Tiny grounds show one physical display only.

Minty decoration uses a locally selected original photo for crowd faces, banner and player heads, persisted in extension storage. The inline chat avatar lacked a downloadable file; an inaccurate generated portrait was rejected and never packaged. The release requires selecting the original photo once. Face effects remain separate from source extraction and appear only in Minty Stadium.


## v1.11: closer action camera

The v1.10 view framed the complete 1672 × 941 stadium plate, so players occupied a small fraction of the screen. This release adds a separate `camera.js` viewport controller and defaults to 1.75× magnification. Full stadium and 2.5× presets remain available and preferences persist locally.

The controller changes only the root overlay SVG viewBox. Backdrop, markings, goals, actors, sphere and shadow therefore share exactly the same pan and zoom. A central region holds the shot steady until the rendered ball moves out of it; camera bounds stay inside the packaged image. Sphere/ground separation participates in framing. There is no interpolation of source positions, added actor lag, separate motion clock or guessed ball position.

`tracking.js`, `renderer.js`, `scoreboard.js`, `scene.js` and all eleven images are byte-for-byte unchanged from v1.10. Camera updates consume the existing snapshot after rendering in the same requestAnimationFrame. Browser checks verify actual on-screen 1.75×/2.5× magnification, unchanged actor coordinates/node identity, screen-space player/ball alignment through camera changes, ball-following at all four pitch corners, airborne/ground visibility, persisted preferences and delayed-read protection.


## v1.12: goal-line alignment and padded native SVGs

The user supplied an overlay screenshot with the ball in front of the goal and confirmed that the original MFL view shows it inside the goal at that moment. This establishes a visual mismatch, but the screenshot does not reveal the underlying SVG coordinates or prove its exact cause.

A reproducible defect exists in bounds selection: when the native viewBox includes a two-unit margin around an unmarked 105 × 68 playing field, the old adapter normalizes that margin as part of the pitch. A native ball at x=0 maps to u=2/109, nearly two metres inside the overlay. A ball just behind the goal can also map inside the field. The new goals fixture fails on v1.11 with this exact condition and passes after the correction.

Bounds now prefer explicit markers, then an identifiable rendered pitch surface/outline, and only then the viewBox fallback. Canonical 105 × 68 shapes or semantically named pitch geometry are candidates; player/ball shapes, definitions and hidden copies are excluded. Discovery is cached in the existing source scan and reconnects after boundary replacement. Field geometry is transformed through the same rendered root coordinate space as actors. Both ball and players normalize against the corrected bounds.

The original `svgPosition()` function, player-circle anchors, ball/flight arithmetic and one-frame sampling remain intact. `renderer.js`, `scene.js`, `camera.js`, `scoreboard.js` and all stadium images are unchanged. The scoreboard never fabricates a ball position to make a score look correct. Diagnostics now includes the chosen boundary and raw ball/shadow anchors to distinguish remaining markup/anchor problems from a source animation reset.

Tests cover both goal lines, positions behind and in front of both goals, nested translation, rendered native transitions, all eleven themes and three camera presets, airborne goal balls, hidden/defs copies and disconnected boundaries. Exact authenticated MFL geometry and the user's specific screenshot remain to be confirmed by replaying that goal with this release.
