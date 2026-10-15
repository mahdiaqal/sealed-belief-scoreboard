# Builder → Intelligent Contracts

## Title

SealedBeliefScoreboard — Evidence-Resolved Brier Accounting

## Notes / Description

A sealed-probability accounting primitive, not a graph or consumable certificate. Participants commit identity-bound hashes, then reveal authenticated forecasts after the commit barrier.

Leader and validators independently fetch two full commit-pinned documents, verify HTTP status and SHA-256, and semantically judge each against the exact question. Exact report equality is required. Only matching SUPPORT or REFUTE vectors determine YES or NO; mixed, uncertain or failed evidence voids the round. A deterministic answer/vector check prevents contradictory outcomes.

The outcome drives integer Brier accounting. Committed non-revealers receive the worst score on scoreable rounds. Resolution is permissionless; a delayed no-outcome fallback closes unresolved rounds. Final score sheets are immutable.

StudioNet proofs cover scoring, wrong-reveal rejection, bad-hash voiding, deadline handling and replay rejection. Public fixtures demonstrate mechanics, not predictive skill. 43 tests pass.

## Evidence

- Repository: https://github.com/mahdiaqal/sealed-belief-scoreboard
- Contract: https://github.com/mahdiaqal/sealed-belief-scoreboard/blob/main/contracts/SealedBeliefScoreboard.py
- README: https://github.com/mahdiaqal/sealed-belief-scoreboard/blob/main/README.md
- Proof matrix: https://github.com/mahdiaqal/sealed-belief-scoreboard/blob/main/LIVE_PROOFS.md
- Sanitized transaction ledger: https://github.com/mahdiaqal/sealed-belief-scoreboard/blob/main/PROOFS.json
- Deployment: https://explorer-studio.genlayer.com/address/0xdD085aa0d0074D4f2c4cf0b8071A9D0860be8a79
- Scoring: https://explorer-studio.genlayer.com/tx/0xab362c2afb9253840e34be5a2710ca1d015f115b003ee39fc8b5b8fd7c5b138b
- Bad-hash VOID: https://explorer-studio.genlayer.com/tx/0x22547eb8686256b2696f17e5d5e5f3bea708b0527a7fc20fedba1356a77f6b0c
- Withheld-reveal deadline accounting: https://explorer-studio.genlayer.com/tx/0xe69932813134179a2f11ea143a754bf84fbccb98111c54632f0da681aba5b98b
- Wrong reveal (expected execution ERROR): https://explorer-studio.genlayer.com/tx/0x3e906c7d2288e12d3539704e80d7056c9b11e8c4c5fb33db4a73e1939522a298
- Replay (expected execution ERROR): https://explorer-studio.genlayer.com/tx/0x486149f47076f4a8c88e2a1f9e3deee23b26aa5c55330ded48b88d9a5053295d

Preserve expected-error labels when adding negative transaction evidence to the portal. No award or acceptance guarantee is made. Use the actual contribution date.
