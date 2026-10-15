# Security scope

Experimental, unaudited, test-network-only. Do not connect real funds or use these scores as security-critical permission gates. No fund movement exists.

## Controls

- Authenticated commits and reveals; fixed roster, per-contract/round/participant domain separation.
- Immutable question/source/deadline configuration; immutable final score sheets; no reset, admin override or consumption mechanism.
- Commit barrier prevents observing revealed beliefs before choosing a commitment. A high-entropy salt remains essential.
- Full source bodies fetched inside each validator's nondeterministic flow. Hash length/text existence cannot determine an outcome.
- Exact source/label/config/book comparison, deterministic answer consistency, bounded integer score computation.
- Worst-score accounting for committed non-revealers on scoreable rounds; nonconsenting invitees not penalized.
- Permissionless deadline resolution; separate no-outcome expiry fallback after 24 hours.
- Bounded inputs/roster/body bytes/creator rounds; no arbitrary URLs, file paths, code evaluation or cross-contract calls.

## Residual trust and limits

Content addressing is integrity, not source authority or event freshness. Documents can be false; two files can have one author. Consensus can share model errors or prompt-injection susceptibility. Creator-selected rounds and pseudonymous accounts cannot establish general predictive skill. This is not a future-event market: pinned fixture contents are known before commitments. A transaction datetime is the network's time reference, not a high-precision wall-clock oracle. Shared StudioNet may fail or rate-limit; no liveness guarantee can override network failure.

Creator-scoped statistics prevent strangers from poisoning another creator's comparison set, but do not prevent cherry-picked questions by that creator. Consumers must include pending, missed and void counts and must not silently divide by revealed successes only. Unrevealed commitments are deliberately worst-scored, not treated as skipped observations.

No private key/token/password should appear in this repository. Native CLI signing is used without exporting wallet keys; demo salts are stored in the OS vault. Report issues privately to the repository maintainer before posting exploitable details. No claim of an independent professional audit is made.
