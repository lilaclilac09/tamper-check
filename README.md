# tamper-check

Software-first tamper triage for Ledger hardware wallets (Nano S Plus, Nano X, Stax, Flex).

## Problem

In October 2026, Ledger confirmed that devices sold through the Southeast Asian reseller CryptoBilis contained an unauthorized hardware implant. According to press reports, the implant reads the 24-word recovery phrase during setup and sends it out over a cellular (eSIM) link. On-chain researchers estimate $86–93M was stolen from 300+ wallets (CoinDesk). On Oct 13 Ledger asked resellers in Indonesia, Singapore, Thailand, the Philippines, Vietnam, Malaysia and Hong Kong to pull devices from shelves while it investigates. The secure element is not broken, so **Ledger Genuine Check still passes** on a tampered unit.

- CoinDesk, Oct 12 2026: https://www.coindesk.com/tech/2026/10/12/ledger-says-unauthorized-implant-found-in-at-least-one-device-sold-by-cryptobilis
- Cointelegraph, Oct 13 2026: https://cointelegraph.com/news/ledger-asks-resellers-to-halt-sales-in-southeast-asia-and-hong-kong
- Ledger Genuine Check: https://www.ledger.com/blog/genuine-check

## Solution

tamper-check catches what attestation misses: **physical changes to the device**. Checks are scored with transparent rules into a 0–100 risk score and a verdict of **LIKELY GENUINE**, **SUSPICIOUS** or **TAMPERED – DO NOT USE**.

1. **Precision scale weight (primary).** Enter ≥3 readings from a 0.001 g scale (re-zero between readings). Readings are averaged, and the tolerance is the largest of the model tolerance, 2× scale resolution and 2× reading spread. A 1 g kitchen scale is flagged as demo-only because it cannot detect implants weighing a few hundred mg.
2. **Center-of-mass shift (optional).** Rest the device across a pivot at several offsets and record the tilt with a phone IMU. A least-squares fit estimates the CoM shift caused by mass added on one side. Or use the simpler **two-scale balance** (below).
3. **RF emission (optional).** Put the device, powered off, in a Faraday bag with an SDR or RF detector and upload the scan as CSV (`timestamp_s,freq_mhz,rssi_dbm`). Bursts in cellular bands are critical, because a Ledger has no cellular radio. Periodic bursts are reported.
4. **Genuine Check result and provenance.** Both are recorded. A failed Genuine Check is critical, and a non-direct purchase is low risk.
5. **Remediation checklist.** Shown when a device is flagged: do not enter a seed → run Genuine Check → verify firmware → move funds to a new device bought from ledger.com with a new seed → report to Ledger → optionally open the device and inspect it.
6. **3D view (three.js).** A model of the device that shows the expected and estimated center of mass, the region with suspected added mass, and RF activity.

A simulator generates genuine, glue-on-one-side, LTE-implant and counterfeit scenarios for every model.

> Reference weights and dimensions in `tamper_check/reference.py` are **example values, not official Ledger specs**. Calibrate them with a known-good unit bought directly from Ledger.

## How to measure at home: two-scale method

1. Lay a rigid ruler across two 0.001 g scales, supports `span` mm apart (default 100 mm). Tare both with the ruler on.
2. Lay the wallet centred on the ruler. Read left `L` and right `R`.
3. Rotate the wallet 180° in place and read again (`L2`, `R2`).
4. Enter them in the dashboard's **Two scales** section (or `two_scale` in `/api/check`).

The tool computes `x = (R−L)/(R+L) × span/2` for each placement. The first reading is the true offset plus your placement error, the flipped one is minus the true offset plus the same error, so `offset = (x1−x2)/2` cancels placement error. The offset goes into the normal CoM check (example tolerance 0.7 mm; >1.4 mm = high) and the 3D view. `L+R` should also match your single-scale weight. Simulated example: `/api/simulate/{model}/{kind}?method=two_scale`.

## Setup & run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium            # for e2e test, screenshots, video
.venv/bin/uvicorn tamper_check.app:app --port 8765   # http://127.0.0.1:8765
```

## Test

```bash
.venv/bin/pytest -v
```
Unit and API tests cover the scoring rules, scale resolution, averaging, remediation, CoM, RF, the simulator and the endpoints. A Playwright end-to-end test loads the dashboard, runs each scenario, checks verdicts and the checklist, confirms the 3D canvas renders, and requires zero console errors. CI runs on every push (`.github/workflows/ci.yml`). The dashboard loads three.js from a CDN.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/models` | Reference models |
| POST | `/api/check` | JSON: `model`, `scale_readings_g`, `scale_resolution_g`, optional `com_mm`, `two_scale` (`left_g`, `right_g`, optional `left2_g`, `right2_g`, `span_mm`) or `imu_samples`, `rf_csv`, `attestation` (`pass`/`fail`/`not_run`), `source` |
| POST | `/api/simulate/{model}/{genuine\|glue\|implant\|counterfeit}` | Run a simulated scenario |
| GET | `/api/history` | Past checks |

Sample RF logs: `samples/rf_genuine.csv`, `samples/rf_implant.csv`.

## Demo

- **Final video: `demo/demo_final.mp4`** (~3 min 15 s: stat-card hook, narrated walkthrough, step-by-step two-scale CoM segment with zoom-ins, Faraday-bag tip, end card; burned-in + soft English subtitles, SRT `demo/demo_final.srt`). Previous 84 s cut: `demo/demo_final_v1.mp4`. All numbers are simulated examples.
- Two-scale screenshots: `screenshots/two_scale/` (recorded with `scripts_two_scale.py`)
- Earlier cuts: `demo/demo.mp4` (silent), `demo/demo_voiceover.mp4` (narrated, script `demo/voiceover_script.md`), `demo/demo_subtitled.mp4` (+ subtitles, SRT `demo/demo_voiceover.srt`)
- Screenshots: `screenshots/genuine.png`, `glue.png`, `implant.png`, `kitchen_scale_demo_only.png`, `manual_diamond_scale_flagged.png`
- Regenerate with the server running: `python scripts_screenshot.py`, `python scripts_video.py`

## Limitations

- Example reference values. Real tolerances need measurements of many genuine units per model and batch.
- An implant that removes as much mass as it adds can pass the weight check.
- An implant may transmit only after setup, so a powered-off RF scan can miss it.
- Flipper Zero's sub-GHz radio does not cover LTE bands above 1 GHz. Use an SDR such as HackRF or RTL-SDR.

## License

MIT

## Web version (browser-only)

`web/` is a static build of the same checks: weight, center of mass (IMU fit or two scales), RF CSV, attestation, provenance and remediation. All of it runs in the browser. There's no server and no uploads, and RF CSV files are read locally. Live at https://check.aileena.xyz.

```bash
cd web && npm ci && npm run dev    # local
npm test                           # vitest: parity with the Python engine
```

`web/test/fixtures.json` holds inputs and the Python `score()` outputs. The JS engine must reproduce the verdict, risk, warnings and messages exactly. To regenerate after changing the Python engine, run `python web/test/gen_fixtures.py` from the repo root.
