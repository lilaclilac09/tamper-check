# tamper-check

Software-first triage for **tampered Ledger hardware wallets** (Nano S Plus, Nano X, Stax, Flex). Built at Paradigm Frontiers 2026 hackathon (Aileen Choo + Aaron Li).

**Primary check: precision-scale weight.** Following Ryan Lackey (@octal)'s suggestion: a ~$100 diamond scale with ~2 mg repeatability (e.g. US Solid DBS46-1, 0.001 g) can catch added implants/glue. Enter ≥3 readings (re-zero between); they are averaged, and tolerance = max(model tol, 2×resolution, 2×spread). A 1 g kitchen scale is flagged **DEMO-ONLY** — it cannot catch mg-level implants. When flagged, the dashboard shows an **agent remediation checklist** (don't enter seed → Genuine Check → verify firmware → move funds to a fresh device bought direct from Ledger with a new seed → report → optional open-up inspection).

Optional advanced checks: **center-of-mass shift** (phone IMU tilt over a pivot) · **RF/cellular emission** while OFF inside a Faraday bag (Flipper/SDR CSV) · **Ledger Genuine Check** result · provenance. Explainable rule-based risk score 0–100 → LIKELY GENUINE / SUSPICIOUS / TAMPERED.

> ⚠️ Reference weights/dims in `tamper_check/reference.py` are **EXAMPLE placeholders, not official Ledger specs**. Calibrate by measuring a unit bought directly from ledger.com.

## Run
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest -q                                   # 8 tests
.venv/bin/uvicorn tamper_check.app:app --port 8765    # open http://127.0.0.1:8765
.venv/bin/python scripts_screenshot.py                # regenerate screenshots (server running)
```
API: `GET /api/models`, `POST /api/check` (JSON: model, weight_g, com_mm | imu_samples, rf_csv, attestation, source), `POST /api/simulate/{model}/{genuine|glue|implant|counterfeit}`, `GET /api/history`. Sample RF logs in `samples/`.

RF CSV format: `timestamp_s,freq_mhz,rssi_dbm`. Bursts >15 dB above floor in 700–960 / 1710–2200 / 2300–2700 MHz → critical (a Ledger has no cellular modem); periodicity is reported.

CoM method: lay device across a pivot at offsets s; tilt ≈ k·(com − s); least-squares fit gives com = −intercept/slope per axis.

## Live pitch demo (≈2 min) — video: `demo/demo.mp4` (81 s)
1. "Ledger confirmed implants in devices sold via CryptoBilis; the implant reads the seed off the screen and exfiltrates over LTE — and Genuine Check still passes."
2. Put an untouched Ledger on the diamond scale, 3 readings → enter → LIKELY GENUINE.
3. Add a blob of glue on one side → reweigh → SUSPICIOUS, red region on the 3D view, remediation checklist appears; tick through it.
4. Show the same readings with "1 g kitchen" resolution → DEMO-ONLY warning: why the $100 scale matters.
5. Click **LTE implant** (or upload `samples/rf_implant.csv`) → TAMPERED: weight + periodic cellular bursts, RF rings in 3D.
6. History table: genuine → glue → implant.

## Tests
`pytest -v` — 15 unit/API tests (incl. community dataset & API) + 1 Playwright end-to-end test (loads dashboard, runs each scenario, checks verdicts & checklist, kitchen-scale warning, 3D canvas actually renders, zero console errors). CI: `.github/workflows/ci.yml`. Needs internet for three.js CDN.

## Screenshots
`screenshots/genuine.png`, `glue.png`, `implant.png`, `kitchen_scale_demo_only.png`, `manual_diamond_scale_flagged.png`, `community_reports.png`

## Limitations
- Example reference values; real tolerances need many genuine units per model/batch.
- Phone-IMU CoM is crude (mm-level, needs a stable pivot); a well-designed implant that replaces mass can evade weight checks.
- Flipper Zero's CC1101 covers sub-GHz only (≈300–928 MHz), NOT LTE bands >1 GHz; use an RTL-SDR/HackRF or cheap RF detector. Implants may transmit only after setup/seed entry, so a powered-off scan can miss them.
- Genuine Check verifies the secure element, not added PCBs — it cannot detect this attack class.
- NFC check (Stax/Flex) is a stub: only the attestation result is ingested.

## Community reports (X: @ohyishi) — UNVERIFIED
[@ohyishi](https://x.com/ohyishi) is Yishi, founder of OneKey (bio: "janitor @OneKeyHQ"). After the CryptoBilis incident he invited people to post teardown photos ([post](https://x.com/ohyishi/status/2110209576276828517)) and replied to each one with a verdict ("clean" or suspicious).
- Raw public data: `data/x_ohyishi/posts.json` (his posts), `replies.json` (others' replies), `media/` (device photos from key cases). Handles only, UTC timestamps, collected 2026-10-14.
- Curated: `data/x_ohyishi/cases.jsonl` (10 cases, all `verified:false`), served at `GET /api/community?model=&category=` and in the dashboard **Community reports** panel.
- Per-model **community notes** are shown next to results but **never change reference specs or scores**. Examples: genuine Nano S Plus chips are ST (STM32F042 + ST33K1M5), so ground-off markings are a red flag; official weight specs drift by batch (OneKey 1S Pure measured 19.9 g vs 18.3 g spec, per the vendor because of a housing material change), so calibrate against a same-batch unit; RF timing is unpredictable, so use a Faraday cage.

## Tampering cases & would tamper-check catch it?
| Case | Source | Caught? |
|---|---|---|
| **CryptoBilis implant, Oct 2026**: extra module with eSIM inside genuine Ledgers sold by a SEA reseller; reads seed from screen, sends over LTE | [CoinDesk](https://www.coindesk.com/tech/2026/10/12/ledger-says-unauthorized-implant-found-in-at-least-one-device-sold-by-cryptobilis), [Cointelegraph](https://cointelegraph.com/news/ledger-asks-resellers-to-halt-sales-in-southeast-asia-and-hong-kong) | **Yes, likely**: module+eSIM+antenna adds mass → diamond-scale weight; LTE bursts if it transmits during an RF scan. Genuine Check alone: **no**. |
| **Fake Ledgers mailed to 2020-leak victims, 2021**: repackaged Nano X with a USB flash drive soldered on, plus a letter asking for the seed | widely reported (BleepingComputer, Jun 2021; page blocks our fetch, link not verified) | **Yes**: added PCB changes weight; the "enter your seed" letter triggers checklist step 1. |
| **Saleem Rashid, 2018**: MCU firmware attack on Nano S, could be done in the supply chain with no hardware change | [saleemrashid.com](https://saleemrashid.com/2018/03/20/breaking-ledger-security-model/) | **No** by weight/RF (software-only); Genuine Check + firmware update (since patched) is the defense, which our checklist includes. |
| **Ledger Connect Kit, Dec 2023**: malicious npm library release drained dApp users | [Ledger](https://www.ledger.com/blog/a-letter-from-ledger-chairman-ceo-pascal-gauthier-regarding-ledger-connect-kit-exploit) | **No**: not a device attack; out of scope. |
| **2020 customer data leak → phishing**: emails/SMS/fake Ledger Live, "replace your device" | [Ledger](https://www.ledger.com/blog/security-incident-report) | **Partly**: device checks don't apply, but the checklist rule "never enter your seed anywhere" covers the attack. |

## Briefing: the scene (sources fetched 2026-10-14)
- **Oct 9 2026**: drained funds traced to Ledgers bought from SEA reseller **CryptoBilis** (MY/ID/PH). Oct 10 Ledger: "one of the impacted users' devices contained an unauthorized hardware implant"; Oct 11: all confirmed cases via CryptoBilis; direct channel not compromised. Est. $86–93M from 300+ wallets (on-chain researchers). — https://www.coindesk.com/tech/2026/10/12/ledger-says-unauthorized-implant-found-in-at-least-one-device-sold-by-cryptobilis
- **Oct 13 2026**: Ledger asks resellers in Indonesia, Singapore, Thailand, Philippines, Vietnam, Malaysia, **Hong Kong** to pull stock; "only confirmed incidents remain contained to Southeast Asia". Users in **Europe** report *suspected* tampering (unconfirmed). — https://cointelegraph.com/news/ledger-asks-resellers-to-halt-sales-in-southeast-asia-and-hong-kong ; Donjon analyzing recalled units — https://www.tokenpost.com/news/technology/31561
- Implant reportedly has its own eSIM, reads the 24-word phrase off the screen during setup, sends over cellular; Bitquery estimate up to $102M / 324 wallets (secondary source, **unconfirmed** figure) — https://coinlab.info/en/articles/ledger-cryptobilis-implant-explained/
- Teardowns of Ledger Flex from Challenger (VivoCity) and Changi airport retailer by Mark Karpelès / Ben Yorke (secondary report, **unverified**) — https://blocktimes.co.uk/ledger-extends-regional-retail-freeze-across-sea-and-hong-kong-as-teardowns-find-spy-implants-beyond-cryptobilis/
- **Genuine Check / attestation**: secure element proves authenticity cryptographically to Ledger's HSM — https://www.ledger.com/blog/genuine-check , https://support.ledger.com/article/360002204997-zd
- **2020 customer data leak** (Shopify/marketing DB; later phishing and "replacement device" scams incl. fake Ledgers mailed with implanted USB hardware — widely reported 2021, page link not verified here) — https://www.ledger.com/blog/security-incident-report
- **Connect Kit supply-chain attack, Dec 2023** (malicious npm release drained dApp users) — https://www.ledger.com/blog/a-letter-from-ledger-chairman-ceo-pascal-gauthier-regarding-ledger-connect-kit-exploit
- **Prior hardware research**: Saleem Rashid, 2018, supply-chain/MCU attack on Nano S — https://saleemrashid.com/2018/03/20/breaking-ledger-security-model/

## Useful repos (all verified HTTP 200)
- https://github.com/LedgerHQ/ledgerctl — talk to a Ledger over USB/APDU; base for scripting attestation checks.
- https://github.com/LedgerHQ/ledger-live — official app implementing Genuine Check / manager flow.
- https://github.com/trezor/trezor-firmware — open firmware; compare vendor anti-tamper/attestation design.
- https://github.com/flipperdevices/flipperzero-firmware — sub-GHz scanning & NFC reading for field checks.
- https://github.com/DarkFlippers/unleashed-firmware — Flipper firmware with extended sub-GHz tools/frequency analyzer.
- https://github.com/EFForg/rayhunter — EFF cellular anomaly (IMSI-catcher) detector; model for an LTE-activity dashboard.
- https://github.com/CellularPrivacy/Android-IMSI-Catcher-Detector — Android cellular anomaly detection ideas.
- https://github.com/greatscottgadgets/hackrf — SDR covering 1 MHz–6 GHz for real LTE-band emission scans.
- https://github.com/phyphox/phyphox-android — export phone accelerometer/gyro data for the tilt/CoM measurement.
- https://github.com/paradigmxyz/iron-proxy — Paradigm's secret-isolating proxy; related "agent never sees keys" angle.
