# MFL Management Hub — One-Click Slow Sync v6

Club Development now has one button: Sync all remaining.

Behaviour:
- continues from the existing cache
- processes every remaining owned-club player in one run
- one progression-history request at a time
- 3-second spacing between players
- 20-second request timeout
- up to 3 automatic retries for transient timeout/connection failures
- a persistently slow player is skipped for that run rather than killing the full sync
- every completed player is saved immediately
- HTTP 429 is respected; completed work remains saved and the next click resumes
- once all players are covered, the same button refreshes the full owned-club roster oldest-first

Because Streamlit executes the sync in the active app session, keep the Club Development
page open while the long sync is running.
