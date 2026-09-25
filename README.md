# MFL Management Hub — Clean Start

This is a fresh single-app build. It does NOT execute or embed any of the old Streamlit app UIs.

Pages:
- Home
- Grower or Shower
- Agency Development
- Club Development

Club Development now uses small saved batches instead of attempting hundreds of MFL progression-history calls in one page load.

## Streamlit secret
MFL_REFRESH_TOKEN = "your current refresh token"

Optional:
DISCORD_WEBHOOK_URL = "your webhook"

## Deploy
Create a brand-new GitHub repository and upload every file from this folder to the repository root.
Main Streamlit file: app.py

Grower or Shower reconstructs its baseline from MFL progression history using the configurable Season 17/competition start shown in the app.
