# FC Nooks 2.5D match extension

[Download the ready-to-load v1.13 ZIP](./FC-Nooks-2.5D-Extension-v1.13.zip?raw=true)

1. Download and extract the ZIP on Windows.
2. Disable the older FC Nooks extension.
3. Open `chrome://extensions` or `edge://extensions` and enable **Developer mode**.
4. Click **Load unpacked** and select the extracted `fc-nooks-25d` folder containing `manifest.json`.
5. Reload MFL, open a Pro match and click **FC Nooks · 2.5D**.

**New in v1.13:** more natural player figures with shaped bodies, shaded kits, boots and movement-driven arm/leg poses. A single surname badge appears above the player in possession, using MFL's native name beneath that player where available. Name extraction is separate from motion and cannot stop player/ball rendering. The goal-line calibration, ball flight, close camera and scoreboard fixes are retained. Use **Camera** for Full stadium, Close · 1.75× or Very close · 2.5×.

Seven real-ground-inspired themes—Wembley, San Siro, Camp Nou, Craven Cottage, The Dripping Pan, Bracken Moor and Sandygate—plus Minty Stadium join Selhurst Park, Ironwood Lane and Harbour Park. All eleven backdrops are packaged locally; named stadiums are approximate artistic interpretations.

Score extraction now handles compact/split playback-row markup, refreshes independently every 100 ms and offers **Select scoreboard**. Ball flight follows rendered ball/shadow separation, with **Set ball shadow** for unlabelled shadows. The rendered player movement foundation and single motion loop are preserved.

In **Minty Stadium**, use **Choose Minty face** once to select his original photo locally. It populates player heads, repeated crowd faces and the stand banner and is remembered on this browser. The chat avatar was unavailable as a downloadable source file, so no substitute portrait is bundled.

[Source and full instructions](./fc-nooks-25d/README.md) · [Original code audit](./fc-nooks-25d/AUDIT.md) · [Validation](./fc-nooks-25d/VALIDATION.md)

Chromium fixture checks pass for motion, synchronized flight, score/clock updates, eleven stadiums, face storage, 22 players, resizing, navigation and recovery. Authenticated MFL and actual unpacked Chrome/Edge installation remain unverified: the development browser blocks installation through administrator policy.

The ZIP includes runtime source, local images, documentation and tests. Test dependencies are needed only for development. Older ZIPs remain for rollback. This extension does not modify the Streamlit management hub.
