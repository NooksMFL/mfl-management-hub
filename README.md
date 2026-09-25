# MFL Management Hub — True All-Remaining v6.1

Fixes a leftover UI variable in v6 which was still passing the selected value
10 into club_backend.sync_batch(), despite the button saying Sync all remaining.

v6.1:
- removes the 5/10/15 selector entirely
- calls sync_batch(..., None, ...) explicitly
- processes the complete unsynced player list in one slow run
- preserves the conservative 3-second spacing, retries, timeout handling,
  rate-limit cooldown and immediate per-player saves from v6
