# FC Nooks 2.5D match extension

Chrome / Edge Manifest V3 extension for `https://app.playmfl.com/*`.

[Download the ready-to-load v1.7 ZIP](./FC-Nooks-2.5D-Extension-v1.7.zip?raw=true)

1. Download and unzip the archive on your PC.
2. Disable the previous FC Nooks extension, if installed.
3. Open `chrome://extensions` or `edge://extensions` and enable **Developer mode**.
4. Click **Load unpacked** and select the unzipped `fc-nooks-25d` folder containing `manifest.json`.
5. Reload MFL, open a Pro match, and click **FC Nooks · 2.5D**.

Keep the complete extension folder, including `assets/harbour-park.jpg`. The photographic Harbour Park stadium, crowd, roof, floodlights and dugouts are packaged locally; the extension does not fetch remote stadium images. Rendered SVG tracking synchronizes players and the ball without added smoothing. Close with the toggle, Close button, Escape or Alt+Shift+M.

[Editable source and full instructions](./fc-nooks-25d/README.md) · [Original code audit](./fc-nooks-25d/AUDIT.md) · [Validation and live-test checklist](./fc-nooks-25d/VALIDATION.md)

Chromium fixture checks pass for animated movement, ball alignment, scoreboard/clock extraction, 22 players, resizing, SPA navigation and missing-image fallback. Real authenticated MFL matches and unpacked extension installation remain unverified because the development browser blocks unpacked installation through administrator policy.

The standalone ZIP contains the same runtime source, local image, documentation and tests as the source folder. Test dependencies are needed only to run the fixture, not to install the extension. This extension does not modify the Streamlit management hub.
