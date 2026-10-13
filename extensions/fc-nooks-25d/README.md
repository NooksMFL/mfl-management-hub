# FC Nooks Match View 2.5D — v1.12.0

Chrome / Edge Manifest V3 extension for MFL Pro matches. Eleven photographic stadium backdrops are packaged locally, with live SVG pitch markings, players, ball, netted goals and scoreboards. The original rendered-CTM player movement foundation is preserved: one frame samples native players and ball, with no extra motion smoothing.

## Install or update on Windows

1. Extract `FC-Nooks-2.5D-Extension-v1.12.zip`; keep the extracted `fc-nooks-25d` folder in a permanent location.
2. Disable/remove older FC Nooks extensions so only one version draws the overlay.
3. Open `chrome://extensions` or `edge://extensions` and enable **Developer mode**.
4. Choose **Load unpacked** and select the extracted folder containing `manifest.json`. Keep the entire `assets` folder.
5. Reload your MFL tab, open a Pro match and click **FC Nooks · 2.5D**.

For an existing unpacked installation, replace its complete folder, click **Reload** on the extension card and reload MFL. Close with the Close button, floating toggle, Escape or Alt+Shift+M. Close the overlay to use original match controls. The underlying match remains mounted and its SVG is never hidden with `display:none`.

## Stadiums

Use **Stadium** in the toolbar. Your choice is saved locally and restored on reload.

| Theme | Visual character |
| --- | --- |
| Selhurst Park | Red-and-blue stands and a compact floodlit bowl; default |
| Ironwood Lane | Original brick-and-claret ground and industrial evening skyline |
| Harbour Park | Original coastal arena with teal seating |
| Wembley | Huge bowl and illuminated arch |
| San Siro | Three tiers, spiral towers and red roof trusses |
| Camp Nou | Sweeping open bowl and Barcelona skyline at dusk |
| Craven Cottage | Compact riverside setting and brick pavilion |
| The Dripping Pan | Small low stand, grassy banks and Lewes backdrop |
| Bracken Moor | Small blue-and-yellow terraces in a hillside setting |
| Sandygate | Tiny low stand, open boundaries and stone walls |
| Minty Stadium | Mint-and-white ground, custom face crowd, banner and player heads |

Named real grounds are generated artistic interpretations with approximate architecture, not surveyed replicas or official assets. Small grounds have one small display. Each theme provides pitch/screen calibration shared by all static geometry and moving entities.

Switches retain player/ball nodes, the source tracker and animation loop. Art loads locally; stale image callbacks are ignored. Missing art reports an error, retains the inline live pitch and permits switching to another theme.

## Closer camera

The default **Close · 1.75×** shot makes players 75% larger than Full stadium. Use the **Camera** menu for **Full stadium**, **Close · 1.75×** or **Very close · 2.5×**. Your choice is saved locally and restored on reload; invalid saved choices return to Close.

Close shots follow the ball when play leaves the central region of the picture. The complete SVG viewport pans/zooms together, including the backdrop, field markings, goals, players, ball and shadow. Actor coordinates and the original rendered-motion tracker are unchanged; no extra actor smoothing or animation clock is added. When a pass lifts off the ground, framing accounts for sphere and shadow. If the ball is unavailable, the shot holds its position. Match navigation resets its focus.

The broadcast score/clock stays above the cropped scene. Close shots show a portion of the pitch; goals, roof and stadium screens come into view as the camera follows play. Select Full stadium to see the entire ground at once.

## Minty's face

Select **Minty Stadium**, then **Choose Minty face**, and choose his original PNG/JPG/WebP photo under 1 MB. It appears on player heads, repeated across the crowd and on the large stand banner. Team-colour shirts and players' foot positions remain intact. Face effects appear only in Minty Stadium.

The exact avatar pasted into chat was not available as a downloadable source file. No reconstructed substitute face is bundled. Minty Stadium works immediately; face effects require choosing the original photo once. The photo is read and stored locally in this browser profile, with no upload or remote request. It persists across tab reloads; if storage is unavailable, it remains usable for the current tab.

## Scoreboard and clock

The reader supports compact playback rows, separate React text nodes, split score/clock digits, abbreviated or full team names, stoppage time, HT and FT. It reads the bound source every 100 ms independently of player/ball rendering. It never generates a local match clock. Hidden stale rows are ignored; replaced or hidden selected rows reconnect automatically.

The native top score bar stays exposed when detected near the top. If scores are missing or the wrong scoreboard is selected, choose **Select scoreboard** and click the actual score/clock row in the original MFL view. Escape or Cancel abandons selection. Unknown values show `—` / unavailable time and never retain another match's score. All visible stadium displays receive the same values.

## Pitch and goal-line alignment

Source SVG borders and advertising margins are outside the playing field. The tracker now prefers explicit pitch bounds, otherwise an identifiable rendered field rectangle/outline, before falling back to the full viewBox. Discovery excludes player/ball shapes, hidden copies and definitions. Both players and ball normalize against the same detected field; a native ball on either goal line therefore lands on the overlay's corresponding goal mouth. Balls just behind a goal retain their actual position.

**Diagnostics** shows `bounds.source` and the detected geometry element, plus the ball/shadow element names and their native `visualPosition` / `groundPosition`. If a goal remains misaligned, pause the same moment in MFL and provide these diagnostics. Unrecognised geometry still uses the viewBox fallback; actual MFL markup has not been inspected in this environment. A scoreboard change never moves the ball artificially.

## Ball flight

The native shadow's rendered centre supplies the ground coordinate. The ball's rendered separation above it supplies visual elevation. Both are read through the same SVG matrices as players, in one animation frame. Landing removes lift immediately; there is no inferred flight duration or extra smoothing.

For an unlabelled shadow, use **Set ball shadow**, then click its ground shadow in the original view. If the ball itself is missing, use **Select ball**. Selections clear when the source SVG or match changes. A missing ball is hidden, never guessed. Selection expires after 15 seconds; Escape cancels it.

Without a usable shadow, native rendered ball growth/scaling can provide an approximate visual cue. Without either cue, the ball remains grounded. Height maps the source animation visually; it is not a physical measurement in metres. **Diagnostics** reports flight cue, normalized ground coordinates, height, ball/shadow candidates, score source, bounds, image state and preference errors.

## Architecture

- `tracking.js`: native SVG discovery, rendered screen CTMs, shared bounds, shadow/flight extraction and replaced-node recovery.
- `scoreboard.js`: score/clock parsing and source binding, independent of actor rendering.
- `stadiums.js`: theme names, local assets, per-theme pitch/screen calibration and default choice.
- `scene.js`: camera, live markings/goals/displays, Minty decoration and image-failure fallback.
- `camera.js`: shared SVG viewport, closer framing, bounded ball-following and camera presets; source extraction remains separate.
- `renderer.js`: direct placement from one snapshot, with separate ground shadow and airborne sphere.
- `viewer.js`: shadow DOM UI, stadium/photo preferences, camera preferences, one motion requestAnimationFrame, independent score polling and SPA lifecycle.
- `viewer.css`: isolated UI styling.
- `assets/*.jpg`: all eleven local backdrops; no remote image/CDN or font dependency.

To add a theme, register it in `stadiums.js`, package its image and declare it in manifest resources. Optional `pitch` calibration defines `farLeft`, `farRight`, `farY`, `nearLeft`, `nearRight`, `nearY`; `screens` lists physical displays. Scene `project(u,v)`, `scale(v)` and `flightScale(v)` serve every pitch feature and actor. Never add independent CSS offsets, actor transitions, raw inline animation target reads or a second motion clock.

No API credentials, runtime dependencies or build step are needed to load the extension. It does not modify the management hub app or send authenticated requests.

## Validation and limitations

See `AUDIT.md` and `VALIDATION.md`. Real Chromium fixture suites exercise rendered motion, score updates, eleven local images, flight, photo storage, navigation and failure recovery. Actual authenticated MFL Pro matches and installed Chrome/Edge operation remain unverified: the development browser blocks unpacked extensions through administrator policy.

MFL selectors come from the supplied extension, not a supported integration contract. Players still need `match-v2-p<number>` IDs and a circle. Source bounds prefer an explicit pitch marker or identifiable field geometry, otherwise the viewBox / 105 × 68 fallback. Automatic unmarked geometry detection recognises a 105 × 68 local surface/outline or a semantically named pitch shape; unknown markup requires an adapter update using Diagnostics. The first visible matching SVG is used when multiple pitches exist. Actual MFL ball/shadow markup has not been inspected; manual selection supplies a fallback. A source DOM capture may be needed if MFL changes these conventions.

This is a fake 2.5D overlay. Fine depth occlusion is approximate; the ball draws above player sprites for readability. Live user-browser checks remain necessary before calling it fully stable on MFL.
