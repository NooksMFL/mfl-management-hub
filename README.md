# MFL Management Hub — Resilient Sync v5

Club Development sync changes:
- keeps the existing local club cache; no cache reset in this build
- defaults to 10-player batches (5/10/15 selectable)
- one request at a time with 2 seconds between players
- 20-second read timeout instead of 6 seconds
- automatically retries network/read timeouts up to 3 times
- if one player still times out, the batch stops safely rather than failing the whole page
- completed players are saved immediately
- next sync resumes from the first unsynced player
- HTTP 429 activates a cooldown and disables the sync button temporarily

Upload over the current repository and reboot Streamlit.
