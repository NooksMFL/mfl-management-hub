# MFL Management Hub — Clean Dark v2

Fresh native Streamlit app. No old app UIs are embedded.

Key fixes:
- clean dark layout matching the selected minimal dark mockup direction
- sidebar navigation without radio-button dots
- Club Development no longer uses the rejected `withLeague` parameter
- verified MFL_OWNER filtering
- known 12-club fallback for the primary wallet if MFL club discovery is temporarily unavailable
- Club Development syncs in saved batches instead of attempting hundreds of player histories in one run

Deploy all files to a brand-new repository root.
Main file: app.py

Streamlit secret:
MFL_REFRESH_TOKEN = "your current refresh token"
