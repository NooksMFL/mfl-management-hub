# MFL Text

The MFL Management Hub, rebranded as a UK television teletext football service: black screens, pixel display headings, crisp monospace body text, primary colours, numbered pages and four-colour shortcuts.

## Football page index

| Page | Section |
|---|---|
| 100 | Home / live cached network overview |
| 200 | Grower or Shower |
| 201 | Agency Development |
| 202 | Club Development |
| 302 | Squad Builder and formation planner |
| 303 | Transfer Window |
| 304 | Transfer Bargains |
| 305 | Watchlist |
| 400 | Compare |
| 500 | Insights |
| 888 | Sync Centre |
| 999 | Design Studio |

Choose a page in the sidebar, use a coloured shortcut, or enter its three-digit number and press Enter. The header reports the current page and UK date. Connect a public wallet to load personal agency and club data; Home uses saved data and labels missing values explicitly.

Squads retain the positional minimums, flexible goalkeeper ratings, retired-player exclusions, portraits, ages and CSV exports. The 4-1-3-2 and 4-3-3 formation planners retain drag-and-drop and browser-saved lineups, with matching MFL Text styling.

## Run locally

```sh
python -m pip install -r requirements.txt
streamlit run app.py
```

The shared theme is configured in `.streamlit/config.toml`; `mfl_text.py` and `mfl_text.css` apply the visual identity. The pixel font is bundled locally with its licence, so no external font service is required. Keep refresh tokens in environment settings or Streamlit Secrets, never in the repository.

## Validate

```sh
python -m unittest discover -s tests -v
```

The suite checks squad allocation, retirement and goalkeeper rules, player-card escaping, preview rendering, numbered pages and navigation. [The original six design studies](design-concepts/README.md) remain available for reference.
