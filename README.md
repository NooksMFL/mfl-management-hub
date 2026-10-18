# MFL Management Hub

![MFL Management Hub Manager Workspace logo](assets/mfl-management-hub.svg)

The MFL Management Hub, with a Football Manager–inspired dark workspace: navy panels, violet accents, crisp typography, a manager sidebar and a green tactics pitch.

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
| 306 | Agency / Player Valuation |
| 400 | Compare |
| 500 | Insights |
| 888 | Sync Centre |
| 999 | Design Studio |

Choose an application in the sidebar, use the workspace shortcuts, or enter a page number and press Enter. The header reports the current page and UK date. Connect a public wallet to load personal agency and club data; Home uses saved data and labels missing values explicitly.

Squads retain the positional minimums, flexible goalkeeper ratings, retired-player exclusions, portraits, ages and CSV exports. The 4-1-3-2 and 4-3-3 formation planners retain drag-and-drop and browser-saved lineups, with matching Manager Workspace styling.

## Run locally

```sh
python -m pip install -r requirements.txt
streamlit run app.py
```

The shared theme is configured in `.streamlit/config.toml`; `mfl_text.py` and `win95.css` apply the visual identity. Fonts are bundled locally with its licence, so no external font service is required. Keep refresh tokens in environment settings or Streamlit Secrets, never in the repository.

## Validate

```sh
python -m unittest discover -s tests -v
```

The suite checks squad allocation, retirement and goalkeeper rules, player-card escaping, preview rendering, numbered pages and navigation. [The original six design studies](design-concepts/README.md) remain available for reference.

## Agency valuations

Page 306 estimates each player from at least five independent active asking-price comparables, using age, OVR and position. It shows price ranges, evidence and priced-player coverage; these are not completed-sale valuations. Market snapshots are saved locally in `valuation_market_cache.db` and reused on later visits. Scan failures preserve the previous snapshot. Currency groups are kept separate; listings without currency metadata are labelled market units.

## Dapper and remembered wallets

Public wallet addresses are remembered on this browser and restored on the next visit. Use **Forget saved wallet** to remove the saved selection. Manual entry remains available. The Dapper connection component is prepared but sign-in stays disabled until the app owner completes Dapper developer registration. See [Dapper setup](dapper_component/README.md) for the activation setting and pinned SDK build instructions.

## Ten new visual concepts

Page 999 Design Studio now includes a **Ten new · Wild collection** selector, alongside the original six designs. [Browse the ten-theme gallery and PDF](design-concepts/WILD_COLLECTION.md). These are independent interactive previews; the live branding now uses Manager Workspace.

### Season progression cards

Open **Insights → Progression cards** to select a player and download a blue shield-style 720 × 1080 PNG showing their portrait, age, position, season OVR gain and PAC / SHO / PAS / DRI / DEF / PHY gains. Cards use Club Development season records, not agency ownership gains. Sync Club Development first; unavailable fields display an em dash and unavailable portraits use a silhouette. The displayed baseline and latest progression dates identify the saved measurement window.
