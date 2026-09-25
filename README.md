# MFL Management Hub — Public Fix v17.1

Fixes:
- Club Development KeyError in Top developing clubs (`ATTR ↑` column mismatch).
- Public Agency first load is reduced to 4 players per batch.
- Public Agency now shows per-player API errors instead of looking like a hard failure.
- Agency HTTP calls retry timeouts / connection errors / transient 5xx responses.
- Agency current refresh reduced to 8 players per batch.
- Grower fresh-deployment empty state now clearly tells users to run Refresh Competition.

Privacy protections from v17 remain unchanged.
