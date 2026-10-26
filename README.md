# MFL Management Hub

![MFL Management Hub Signal logo](assets/mfl-management-hub.svg)

The MFL Management Hub, in the Signal theme: warm ivory, yellow wayfinding, charcoal controls and compact sans-serif typography. Body text is 14px, headings and controls are smaller, and the Load → Track → Select route links the main tasks.

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

Page 999 Design Studio now includes a **Ten new · Wild collection** selector, alongside the original six designs. [Browse the ten-theme gallery and PDF](design-concepts/WILD_COLLECTION.md). These are independent interactive previews; the live branding now uses Signal.

### Season progression cards

Open **Insights → Progression cards** to select a player and download a blue shield-style 720 × 1080 PNG showing their portrait, age, position, season OVR gain and PAC / SHO / PAS / DRI / DEF / PHY gains. Cards use Club Development season records, not agency ownership gains. Sync Club Development first; unavailable fields display an em dash and unavailable portraits use a silhouette. The displayed baseline and latest progression dates identify the saved measurement window.

### Club tactics and navigation update

**Squad Builder → Club tactics** is the default workspace. Select a current club, compare eight formations, apply a suggested XI, and drag players between the pitch and reserves. The compact desktop pitch has an optional Large pitch toggle. Download a self-contained 1800 × 1500 tactics PNG or a lineup CSV including position OVR and rating source. **League squads** retains the 25-player quotas, two goalkeepers and retired-player exclusions; league bands use base OVR while role assignments use known position ratings.

Explicit position-rating maps returned in player metadata are retained in the shared roster cache. Enter missing values under **Review / enter position ratings**. Ratings are stored per wallet and player; e.g. CM 69 / CDM 62 stays 62 at CDM. Unknown secondary ratings are not invented or selected automatically. A labelled base-OVR fallback is available only for the first listed position. Complete-XI averages are unavailable when any slot is empty or unverified. Live MFL data access was blocked in the development environment; automatic position-data ingestion supports explicit maps and has controlled-payload tests, but has not been verified against a live response.

**Load / refresh team players** is available on Home and Squad Builder. Community & design hides Grower or Shower and Design Studio by default; existing page links still work. Section accents differentiate the main workspaces. Home distinguishes incomplete planning groups from complete 25-player squads and reconciles the agency roster with assigned and omitted records.

**Club progression** keeps the whole-season club/player overview as its default. Numeric leaderboard headings sort highest first on their first click. **Since joining my club** is a separate option: enter actual joining dates, then refresh player histories in batches of eight. Dates are entered explicitly because a verified club-joining date is not present in the saved roster. The baseline is the latest known attribute snapshot at or before the entered date (date-only entries use midnight UTC). Unknown baselines and missing attributes remain unavailable; totals show coverage. Changing a joining date resets its cached baseline. Whole-season, club-tenure and agency-acquisition totals are separate measurement periods.

**Transfer Window** now uses public, season-tagged competition appearance records instead of requiring a refresh-token login or treating every MATCH history event as an official appearance. Select the season explicitly (default 18); friendlies/preseason are excluded, and unrecognised responses are errors rather than false zeros. Scan state is scoped to wallet and season. A failed or partial scan does not claim all players are clear. Live API verification remains subject to MFL access from the deployed app.

### Retired-player visibility

Retired / no-current-club players are hidden by default from agency and club development displays, comparisons, watchlists, insights and the Home player count. The latest shared roster takes priority over stale analysis metadata, including an explicit null club; refreshing the roster can no longer retain an old club during agency hydration. Use **Show retired players** in the sidebar to review saved history. Squads and tactics always exclude retired players. Valuation tables default to active players and export the selected filter. No player history is deleted.

### Fifteen fresh website directions

[Browse the new 15-design gallery](design-concepts/FRESH_FIFTEEN.md) · [PDF lookbook](design-concepts/MFL_Fresh_15_Lookbook.pdf). In **Design Studio**, the default **Fifteen new · Fresh directions** collection includes 15 distinct layout studies, locally bundled fonts, desktop/mobile screenshots and working demo interactions. Previews use illustrative data; choosing a preview does not rebrand the live app.

### Signal theme

The live Hub uses **12 · Signal** from the fresh-design collection. `signal.css` supplies the shared theme, with matching styles for the formation planner, sortable progression tables, wallet panel, icons and exported tactics boards. Default body text is 14px, controls 13px and the main page heading 26px (23px on phones). The compact pitch and optional expanded view remain available. Design Studio keeps the original concept previews for comparison.
