# MFL Management Hub — Product UI v9

Frontend rebuild on the working v6.1 backend:
- custom HTML/CSS dashboard
- bespoke vector MFL shield/crown lockup
- compact navigation and page hierarchy
- dashboard hero + performance snapshot
- proper KPI/workspace/top-club components
- existing Grower, Agency and Club logic retained
- one-click slow Club sync retained

Note: Streamlit Community Cloud runtime SQLite is ephemeral across redeploys. This build
does not deliberately clear club cache, but permanent cross-deployment cache persistence
requires a persistent data store.
