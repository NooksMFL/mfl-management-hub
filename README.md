# MFL Management Hub

A Streamlit app with four sections:

- **Transfer Bargains** — search current player listings and compare asking prices.
- **Agency progression** — track current players against their recorded purchase or earliest available history.
- **Club progression** — track player and club gains from the selected season's starting stats.
- **Squad analyser** — review FCN squads using already checked profiles, including an unfinished sync. See missing starters, thin cover and players below your target rating.

The interface uses a charcoal and violet theme with bundled Open Sans fonts, simple navigation and player photos. Missing stats display as a dash rather than a zero.

## Using the Hub

Save your public MFL wallet address in the sidebar, then choose **Sync entire agency**. This loads current profiles, attributes, clubs and agency membership. Use **Update progression** to read player histories. Each section offers a CSV download.

If MFL limits requests, the app saves its place and shows **Continue sync** or **Continue update**. Wait for the displayed cooldown before continuing. Previously completed data stays available throughout an interrupted sync. Pages do not request MFL data automatically when opened.

## Run

```sh
python -m pip install -r requirements.txt
streamlit run app.py
```

For Streamlit Community Cloud, use this repository's `main` branch and `app.py`. Store `MFL_REFRESH_TOKEN` in Streamlit Secrets or an environment variable; never commit it. The API client refreshes authentication when required and shares its rate-limit cooldown between all sections.

## Data and recovery

Full agency sync follows every roster page, including short pages. It checkpoints each profile and verifies membership again before publishing. A changed or sold player is reconciled on continuation. Current-club fields override historic parent-club data. Unavailable details are marked in exports.

A full sync publishes its roster, owned clubs and current agency stats together, preserving existing acquisition baselines and progression history. Incomplete runs leave the last completed roster untouched. The full-agency CSV is frozen to the completed run, with individual check times.

Progression updates also checkpoint completed players. Club progression uses a recorded state at or before the season boundary; a missing starting state is never replaced by a later state. Agency results label the baseline source as purchase, first record or unverified.

SQLite stores data on the server. Wallet-specific browser backups help restore saved data after a Streamlit restart. Keep CSV exports for a separate copy. Historical helper modules remain in the repository for data compatibility; only the four sections above are exposed in the app.

## Validate

```sh
python -m unittest discover -s tests
```

The suite covers full-sync completeness, checkpoint recovery, membership changes, HTTP 429 cooldowns, authentication, progression baselines, browser backups and the simplified interface. Tests use simulated API responses; they do not prove that a live MFL sync has completed.

Theme: `hub.css` and `.streamlit/config.toml`. Font licences: `assets/hub-fonts/`.

## Squad analysis and saved syncs

The analyser makes no API requests and never starts, resets or modifies a sync. A paused run with 452 of 460 checked profiles can be analysed immediately; the eight unverified players are labelled as pending. Retired/no-club players are hidden from active views and excluded from analysis, while their stored records remain untouched. Agency progression has a **Show retired / no club** toggle.

Choose FCN clubs, a formation and a target starting rating (initially the club's median OVR). Analysis assigns each player once across the XI and one cover player per starting place. Listed secondary positions without a supplied rating are flagged for checking rather than assigned an invented OVR. Cover is compared with a target five points below the starting target. Recommendations depend on these settings and do not claim to know a club's league standard.

Opening the analyser does not discard or re-fetch checked profiles. **Continue sync** resumes the existing run; **Start again** is hidden once profiles have been checked. **Download saved sync** in Sync help saves the wallet's data and partial checkpoint. Browser restoration waits for storage to reply before writing a backup, and an older browser checkpoint cannot replace an existing server run.
