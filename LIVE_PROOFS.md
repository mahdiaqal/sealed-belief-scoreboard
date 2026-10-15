# StudioNet proof matrix

## Deployment and matching source

- Network: gasless GenLayer StudioNet, chain ID 61999.
- Contract: [0xdD085aa0d0074D4f2c4cf0b8071A9D0860be8a79](https://explorer-studio.genlayer.com/address/0xdD085aa0d0074D4f2c4cf0b8071A9D0860be8a79).
- Dedicated test signer: `0x7a413BB4AB62E31d62d4cD9efC8C8a8Dae37FB42`; zero GEN required. No existing wallet key was exported.
- Contract and fixture commit: [`097dde704ca5d2b9e9596da61238936469c82306`](https://github.com/mahdiaqal/sealed-belief-scoreboard/commit/097dde704ca5d2b9e9596da61238936469c82306).
- Deployed source SHA-256, after CRLF normalization and a single trailing newline: `e6e7b68ac5c8b0fb6288266ee3be96d7380354dfc22f681f94eaebb7cd13ee1c`.
- `gen_getContractCode` source matched the local contract. Later commits change only tests, scripts and documentation, not deployed contract source or pinned fixture bytes.
- [PROOFS.json](PROOFS.json) contains sanitized transaction metadata only, not raw validator configurations, credentials or receipts.

## Real transaction matrix

All 14 below are FINALIZED with MAJORITY_AGREE. Twelve executed SUCCESS; two deliberately executed ERROR and changed no state. An execution ERROR is never represented as a successful business transition.

| Step | Execution | Verified purpose | Transaction |
| --- | --- | --- | --- |
| Deploy | SUCCESS | Contract created | [406d93c8](https://explorer-studio.genlayer.com/tx/0x406d93c8b4f7920027b10fdb7aadeb972388f460fd3aa3bdb051771368065f35) |
| Open deadline round | SUCCESS | Fixed 60s commit + 60s reveal windows | [bdb5ab75](https://explorer-studio.genlayer.com/tx/0xbdb5ab758a17feb3e2a75073ac95c2e61161b053ce6c39f41387524ab8c0670b) |
| Commit deadline round | SUCCESS | Authenticated commitment; reveal deliberately omitted | [bb58f685](https://explorer-studio.genlayer.com/tx/0xbb58f685528ac3ba2e267467794e073e98e5daac4e8a853f1dd5c12145b2c545) |
| Open scoring round | SUCCESS | Immutable question, roster and two source commitments | [1dd2a600](https://explorer-studio.genlayer.com/tx/0x1dd2a600dff6ccdb3b69cc3172a1263dbaeb3ce10fcf59a90f3c98f2207a9f97) |
| Commit scoring round | SUCCESS | Sealed 20% YES probability | [3add9be4](https://explorer-studio.genlayer.com/tx/0x3add9be490302aaa6c33cefc9ba32932c18078787488a8df37a7c45e05a46538) |
| Wrong reveal | **ERROR, expected** | Revealing 80% against the 20% commitment rejected: `Reveal commitment mismatch` | [3e906c7d](https://explorer-studio.genlayer.com/tx/0x3e906c7d2288e12d3539704e80d7056c9b11e8c4c5fb33db4a73e1939522a298) |
| Correct reveal | SUCCESS | Sender-bound 20% probability matches commitment | [cb06a47a](https://explorer-studio.genlayer.com/tx/0xcb06a47a8f7582862c9dfc41f94d65aa80b6c3e858dd16646563768daf8d1e6e) |
| Evidence-resolved scoring | SUCCESS | Full documents fetched; REFUTE/REFUTE → NO; score 96,000,000 | [ab362c2a](https://explorer-studio.genlayer.com/tx/0xab362c2afb9253840e34be5a2710ca1d015f115b003ee39fc8b5b8fd7c5b138b) |
| Duplicate resolution | **ERROR, expected** | `Round terminal`; no duplicate score | [486149f4](https://explorer-studio.genlayer.com/tx/0x486149f47076f4a8c88e2a1f9e3deee23b26aa5c55330ded48b88d9a5053295d) |
| Open bad-hash round | SUCCESS | First source deliberately bound to incorrect all-`f` hash | [9526e881](https://explorer-studio.genlayer.com/tx/0x9526e8819437b7282ace7146ce15913d8de781d72bec09510d1dffcbcb3895d1) |
| Commit bad-hash round | SUCCESS | Commitment does not itself authorize scoring | [0341d201](https://explorer-studio.genlayer.com/tx/0x0341d201c42cd322cf24ba68efabe239a29a0b62642319c8ac473d630e318a3a) |
| Reveal bad-hash round | SUCCESS | Valid reveal still does not bypass evidence checks | [e604dd9d](https://explorer-studio.genlayer.com/tx/0xe604dd9de8b5a2682d0063c2c38d4de8bbc5a932e81a7a3b2ce200f4c36edfeb) |
| Resolve bad-hash round | SUCCESS | Fetched byte hash differs from commitment; UNKNOWN/UNKNOWN → VOID, no score | [22547eb8](https://explorer-studio.genlayer.com/tx/0x22547eb8686256b2696f17e5d5e5f3bea708b0527a7fc20fedba1356a77f6b0c) |
| Resolve withheld reveal after deadline | SUCCESS | Independently established NO; MISSED_REVEAL → score 0, loss 100,000,000 | [e6993281](https://explorer-studio.genlayer.com/tx/0xe69932813134179a2f11ea143a754bf84fbccb98111c54632f0da681aba5b98b) |

## Independently checked final records

| Round | ID | Final state | Evidence labels | Score / loss | Final root |
| --- | --- | --- | --- | --- | --- |
| `demo-good` | `8d3fdee84f247fadd68532637302e270c5754fc110d8fe4de8a640f9d8b98d77` | SCORED | REFUTE / REFUTE | 96,000,000 / 4,000,000 | `624a766c296fd1dad04bee40549820b876870f7a4bdc2b2b8384a028f6c24689` |
| `demo-void` | `a04a3795c59d6ec412475cdc110c03782ae2d2790bff34c5d93d6ef385caac0d` | VOID | UNKNOWN / UNKNOWN | No score; void count +1 | `0a127189e78032731badf83d542ea8c9cc79eeb8c923772cd60723d1d3bfda86` |
| `demo-missing` | `b6fbd0b7f61c339d6de14a02d40b43c1b2f3c6a839dd385a11c29338d6db3e7f` | SCORED | REFUTE / REFUTE | 0 / 100,000,000 | `2a2bcff7a7c4b51d77fd110088e55dd87a40a6c91062acd8550d684d52c1776e` |

The missing-reveal deadline was `1792044511`; its evidence resolution timestamp was `1792045563`, strictly after expiry. Final aggregate for creator/participant test signer:

```json
{"committed":3,"scored":2,"score_sum":96000000,"loss_sum":104000000,"missed_reveal":1,"voided":1,"pending":0}
```

Conservation: `score_sum + loss_sum = scored * 100000000`. The checker recomputed configuration roots, final roots, full body hashes, source commitments, answer/vector consistency and exact scoring from state reads. The rejected replay did not change the scoring round root.

### Evidence byte commitments

- [Archive policy at the pinned commit](https://raw.githubusercontent.com/mahdiaqal/sealed-belief-scoreboard/097dde704ca5d2b9e9596da61238936469c82306/examples/archive-policy.txt): `5603163bb6ba64a684582eae106a00a562bcd2c116d5967fcb8be25abcf89b06`.
- [Archive FAQ at the pinned commit](https://raw.githubusercontent.com/mahdiaqal/sealed-belief-scoreboard/097dde704ca5d2b9e9596da61238936469c82306/examples/archive-faq.txt): `900262743aafee3f3b6ef5d183cb77bf3f496305e197cf9a60a319e49ea7e8a3`.

Both are authored, controlled demonstration fixtures at the same publisher. They were publicly available before commitments. They prove independently executed acquisition and semantic interpretation, **not independent source authority, actual predictive skill, future-event publication timing or real-world service delivery**. Only one test signer was used live; authenticated two-participant separation was tested locally.

## Local coverage versus live coverage

| Property | Local test | Live proof |
| --- | --- | --- |
| Two independently authenticated participants, 20% vs 80% scores | Passed | Not claimed; live rounds have one signer |
| All nine semantic vectors, including contradictory pairs | Passed | REFUTE/REFUTE and failed-evidence UNKNOWN/UNKNOWN observed |
| Independent validator comparison rejects altered label/answer/body/binding | Actual callback tested | Successful network MAJORITY_AGREE; deliberate validator disagreement not claimed |
| Post-consensus forged answer/vector/body cannot score | Passed | Not injected into live network |
| Wrong reveal and terminal replay | Passed | Expected ERROR receipts above |
| Missing commit cannot block deadline resolution or penalize nonconsenter | Passed | Not claimed live |
| Committed non-revealer receives maximum loss after deadline | Passed | SUCCESS receipt above |
| 24-hour permissionless no-outcome expiry fallback | Passed at exact boundary | Not claimed live; no artificial chain-clock jump |
| Bad HTTP, encoding, oversized body and wrong source hash | Passed | Wrong hash exercised live |
| Malformed model response never finalizes | Passed | Not forced live |
| All 10001 integer probabilities, symmetry/range and properness identities | Exhaustive checks passed | Concrete 20% / NO accounting verified |
| SDK calldata and pinned runtime validation | 7 roundtrips + lint/SDK validation passed | Successful real GenVM execution |

## Excluded failure and transport recovery

An initial creation [015c70f2](https://explorer-studio.genlayer.com/tx/0x015c70f22f3cd9e7a7776c2e138ca4ab84f8148e378a53ce719e87d1490fefff) finalized ERROR because CLI 0.39.2 automatically encoded the single hexadecimal roster as typed Address, not the contract's string roster API. It created no round and is **excluded** from the 14-proof matrix. The helper now supplies the public address in base64, which the same deployed Address parser normalizes correctly. No contract source change or authorization bypass was needed.

Receipt lookups intermittently failed. Known hashes were retained and rechecked, never blindly rebroadcast. Before the final deadline write was sent, a state read showed OPEN and sender latest/pending nonce `221`, exactly one past the last known transaction nonce `220`, confirming no additional broadcast had occurred. The final write was then submitted once under its recorded hash.

## Reproduce read-only checks

```powershell
node --dns-result-order=ipv4first scripts/check.mjs source 0xdD085aa0d0074D4f2c4cf0b8071A9D0860be8a79
node --dns-result-order=ipv4first scripts/check.mjs round 0xdD085aa0d0074D4f2c4cf0b8071A9D0860be8a79 8d3fdee84f247fadd68532637302e270c5754fc110d8fe4de8a640f9d8b98d77
node --dns-result-order=ipv4first scripts/check.mjs round 0xdD085aa0d0074D4f2c4cf0b8071A9D0860be8a79 a04a3795c59d6ec412475cdc110c03782ae2d2790bff34c5d93d6ef385caac0d
node --dns-result-order=ipv4first scripts/check.mjs round 0xdD085aa0d0074D4f2c4cf0b8071A9D0860be8a79 b6fbd0b7f61c339d6de14a02d40b43c1b2f3c6a839dd385a11c29338d6db3e7f
node --dns-result-order=ipv4first scripts/check.mjs stats 0xdD085aa0d0074D4f2c4cf0b8071A9D0860be8a79 0x7a413BB4AB62E31d62d4cD9efC8C8a8Dae37FB42 0x7a413BB4AB62E31d62d4cD9efC8C8a8Dae37FB42
```

For each ledger hash, `check.mjs success HASH` verifies FINALIZED/SUCCESS/MAJORITY_AGREE; use `error HASH "EXPECTED_MESSAGE"` for the two labeled negative proofs. `complete-proofs.mjs` resumes known hashes only and stops on uncertain execution. Run only one proof runner at a time. There is no claim of an independent security audit or guaranteed steward acceptance.
