# Acceptance audit — 2026-11-22

Scope: `origin/main` `71f6c0967229dbd0495fdf3e8934cd313bd9ae63`, every merged PR from the paginated GitHub API, tracked docs/instructions, existing media and both application variants. Only [ACCEPTANCE.md](../ACCEPTANCE.md) and its incorporated repository instructions apply. Historical work is assessed against today's standard, not assumed to have been governed by it at the time.

| # | Item | Fails rule | Source rule | Fix or not fixable |
|---|------|------------|-------------|--------------------|
| 1 | README lacked a product-status/next-action line and asserted "Live at" a URL that could not be verified | "Demo ≠ product"; "LIVE / BLOCKED / LOCAL ONLY + next human action in one line"; "if you cannot prove it on production, do not claim it is fixed" | `ACCEPTANCE.md` §5, quoting `ship-visible-mvp.mdc` / `AGENTS.md` | Added BLOCKED plus a human TLS/domain verification action and qualified the public-URL claim. Curl returned HTTP 000, exit 35, `SSL routines::unexpected eof while reading`; Chromium independently returned `net::ERR_CONNECTION_CLOSED`. This does not establish a universal outage or its root cause. Deployment/domain remediation is **not fixable here** without deployment configuration/access; no bypass or production success claim. |
| 2 | README described the checked-in final demo as 94 seconds | "Do not claim verified if you did not observe it"; "Point to artifacts: screenshots, `verify-report.json`, CI output, command output" | `ACCEPTANCE.md` §2, quoting `verification.mdc` / `AGENTS.md` | Corrected to 58 seconds: `ffprobe demo/demo_final.mp4` reports 57.960000 s; the final SRT cue ends at 57.880 s. Previous narrated cut is 83.687 s, consistent with its rounded 84-second description. No media was regenerated. |

## Checks and evidence

- Exactly one merged PR: [#1](https://github.com/lilaclilac09/tamper-check/pull/1), process files only. Current body checker exit 0; merge SHA is an ancestor of `origin/main`. No merged UI PR exists; original application changes were direct commits.
- Read root `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/acceptance.mdc` and README. No additional English-only or job-ID rule exists. README's browser-only privacy statement is scoped to `web/`: it reads RF CSV with the File API and scores locally, unlike the explicitly documented Python API. No scan or secret was uploaded in this audit.
- Existing UI evidence is present: `screenshots/lab/live_bottom_390.png` is 390×844, and checked-in demonstration videos exist. The other two filenames ending in `_390.png` are cropped images (300×392 and 350×935), not full viewport stills. Fresh local browser-only genuine → implant → remediation evidence at 390×844 is linked below; simulated inputs are labelled as such, not real-device validation.
- `python -m pytest -q` using the requirements-installed isolated environment: **19 passed**, including the existing Chromium/API end-to-end test. One upstream Starlette deprecation warning.
- In `web/`, `npm test`: **104 passed**; `npm run build`: passed. No separate lint script exists. `npm ci` reported six dependency advisories (3 moderate, 1 high, 2 critical); dependency upgrades were not part of this rule-backed documentation fix.
- Local browser capture: genuine gives LIKELY GENUINE; simulated implant gives TAMPERED - DO NOT USE and six remediation items; no page errors. This is local simulation, not public-deployment or hardware-detection evidence.
- Repository homepage is null; Pages API HTTP 404 and deployments API empty. These do not disprove hosting outside GitHub. Forbidden-claim search found no unqualified completion phrases outside the mandated acceptance-rule quotations. Example reference values and real-world detection limitations remain clearly disclosed.
- Prepared PR body passes `python3 scripts/check_acceptance.py`; `git diff --check` passes. No product code, dependency or layout changed.

## Fresh local UI evidence

[Mobile input surface](https://app.devin.ai/attachments/026c1f81-78a3-46b6-8d61-25e0c9c18dba/01-mobile-390.png) → [genuine](https://app.devin.ai/attachments/e1217143-9238-4d54-8f14-45d3d837a2bc/02-genuine-390.png) → [implant](https://app.devin.ai/attachments/c843908f-76ba-48ec-9976-6e3f3e02bc9a/03-implant-390.png) → [remediation](https://app.devin.ai/attachments/7c2f58dd-256d-4662-a337-6b37fe4212b3/04-remediation-390.png), all 390×844. [Interaction recording](https://app.devin.ai/attachments/d7b10a09-1e96-4551-b3c5-eef90e624777/mobile-genuine-implant.webm).

| blocked_on | evidence | impact | human_action | not_doing |
|------------|----------|--------|--------------|-----------|
| Public deployment verification | Curl TLS EOF and Chromium ERR_CONNECTION_CLOSED at check.aileena.xyz | degraded: local simulation verified; production unverified | Inspect public TLS/domain configuration and verify the deployed app | No TLS bypass, new deployment or localhost-as-production claim |

Passed: merged PR #1 closer and ancestry; existing mobile/media artifacts; Python and web tests/build; browser-only local-file handling in source; explicit example-only reference data and hardware limitations.

Observed, no rule covers it: mobile warning tables extend beyond the viewport; package-manager dependency advisories require separate dependency work, not an invented acceptance gate. No aesthetic redesign or claim that simulated scoring proves real implant detection was added.
