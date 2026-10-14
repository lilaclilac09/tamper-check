# tamper-check

Software-first triage for **tampered Ledger hardware wallets** (Nano S Plus, Nano X, Stax, Flex). Built at Paradigm Frontiers 2026 hackathon (Aileen Choo + Aaron Li).

Checks: **weight** vs reference · **center-of-mass shift** (phone IMU tilt over a pivot) · **RF/cellular emission** while OFF inside a Faraday bag (Flipper/SDR CSV) · **Ledger Genuine Check** result · provenance. Explainable rule-based risk score 0–100 → LIKELY GENUINE / SUSPICIOUS / TAMPERED.

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

## Live pitch demo (≈2 min)
1. "Ledger confirmed implants in devices sold via CryptoBilis; that implant reads the seed off the screen and exfiltrates over LTE — Genuine Check still passes." (screenshot attestation row: OK but warns)
2. Weigh a real, untouched Ledger on a 0.01 g kitchen scale → enter weight → LIKELY GENUINE.
3. Put a blob of glue/blu-tack on one side → reweigh, redo phone tilt → SUSPICIOUS (weight + CoM).
4. Click **LTE implant** simulation (or upload `samples/rf_implant.csv`, as if from Flipper/SDR with device in a Faraday bag) → TAMPERED, periodic cellular bursts.
5. Show history table: genuine → glue → implant.

## Screenshots
`screenshots/genuine.png`, `screenshots/glue.png`, `screenshots/implant.png`

## Limitations
- Example reference values; real tolerances need many genuine units per model/batch.
- Phone-IMU CoM is crude (mm-level, needs a stable pivot); a well-designed implant that replaces mass can evade weight checks.
- Flipper Zero's CC1101 covers sub-GHz only (≈300–928 MHz), NOT LTE bands >1 GHz; use an RTL-SDR/HackRF or cheap RF detector. Implants may transmit only after setup/seed entry, so a powered-off scan can miss them.
- Genuine Check verifies the secure element, not added PCBs — it cannot detect this attack class.
- NFC check (Stax/Flex) is a stub: only the attestation result is ingested.

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
