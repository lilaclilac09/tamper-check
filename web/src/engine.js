// Pure-browser port of tamper_check/engine.py. No network, no storage: everything is computed locally.
import { REFERENCE, CELL_BANDS_MHZ } from "./reference.js";

const r3 = (v) => Math.round(v * 1000) / 1000;
const r4 = (v) => Math.round(v * 10000) / 10000;
const sgn = (v, d) => (v >= 0 ? "+" : "-") + Math.abs(v).toFixed(d);

/** IMU pivot fit: samples {x:[[support_mm, tilt_deg],...], y:[...]}; tilt = slope*s + icpt, com = -icpt/slope. */
export function estimateCom(samples) {
  return ["x", "y"].map((ax) => {
    const pts = (samples && samples[ax]) || [];
    if (pts.length < 2) return 0;
    const n = pts.length;
    let sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (const [s, t] of pts) { sx += s; sy += t; sxx += s * s; sxy += s * t; }
    const den = n * sxx - sx * sx;
    if (den === 0) return 0;
    const slope = (n * sxy - sx * sy) / den, icpt = (sy - slope * sx) / n;
    return slope === 0 ? 0 : r3(-icpt / slope);
  });
}

/** Two-scale balance: x = (R-L)/(R+L) * span/2; rotating 180° gives x2 = -d + p, so d = (x1-x2)/2. */
export function comFromTwoScales(left_g, right_g, span_mm = 100, left2_g = null, right2_g = null) {
  const x = (L, R) => {
    if (L == null || R == null || !(L + R > 0)) throw new Error("left/right readings must be positive");
    return ((R - L) / (R + L)) * span_mm / 2;
  };
  const x1 = x(left_g, right_g);
  const out = { method: "two_scale", span_mm, left_g, right_g, left2_g, right2_g, x1_mm: r3(x1), total_g: r4(left_g + right_g) };
  if (left2_g != null && right2_g != null) {
    const x2 = x(left2_g, right2_g);
    Object.assign(out, { x2_mm: r3(x2), offset_mm: r3((x1 - x2) / 2), placement_mm: r3((x1 + x2) / 2), flipped: true });
  } else Object.assign(out, { offset_mm: r3(x1), flipped: false });
  return out;
}

/** CSV columns: timestamp_s,freq_mhz,rssi_dbm */
export function parseRfCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const hdr = lines.shift().split(",").map((h) => h.trim());
  const i = ["timestamp_s", "freq_mhz", "rssi_dbm"].map((k) => hdr.indexOf(k));
  if (i.some((v) => v < 0)) throw new Error("CSV needs timestamp_s,freq_mhz,rssi_dbm");
  return lines.filter((l) => l.trim()).map((l) => { const c = l.split(","); return i.map((j) => parseFloat(c[j])); });
}
export const inCell = (f) => CELL_BANDS_MHZ.some(([a, b]) => a <= f && f <= b);

export const REMEDIATION = [
  "STOP: do NOT enter or import any seed phrase on this device; do not set it up.",
  "Run Ledger Genuine Check in Ledger Live (note: passes even with an added implant).",
  "Verify firmware version in Ledger Live matches the latest official release.",
  "If funds are already on a seed generated/entered on this device: move them to a fresh device bought DIRECT from ledger.com, with a NEW seed.",
  "Report to Ledger Support with purchase source; if funds were stolen, contact police before opening the device.",
  "Optional: photograph, then open up / visually inspect for extra PCB, eSIM, antenna or glue (voids evidence chain - only after reporting).",
];

export function score(m) {
  const model = m.model, ref = REFERENCE[model];
  if (!ref) throw new Error("unknown model");
  const warnings = []; let risk = 0;
  const add = (check, severity, points, message) => { risk += points; warnings.push({ check, severity, points, message }); };
  const readings = m.scale_readings_g?.length ? m.scale_readings_g : m.weight_g != null ? [m.weight_g] : [];
  const res = m.scale_resolution_g || 0.001;
  let weight = null;
  if (readings.length) {
    weight = readings.reduce((a, b) => a + b, 0) / readings.length;
    const spread = Math.max(...readings) - Math.min(...readings);
    const tol = Math.max(ref.weight_tol_g, 2 * res, 2 * spread);
    const d = weight - ref.weight_g;
    const info = `avg of ${readings.length} reading(s) ${weight.toFixed(3)} g, ${sgn(d, 3)} g vs reference (tol ±${tol.toFixed(3)} g @ ${res} g resolution)`;
    if (Math.abs(d) > 2 * tol) add("scale_weight", "high", 50, "PRIMARY: " + info);
    else if (Math.abs(d) > tol) add("scale_weight", "medium", 25, "PRIMARY: " + info);
    else add("scale_weight", "ok", 0, "PRIMARY: " + info);
    if (res >= 0.1) add("scale_resolution", "medium", 0, `${res} g scale is DEMO-ONLY: cannot catch mg-level implants. Use a ~0.001 g diamond scale (2 mg repeatability).`);
    if (readings.length < 3) add("scale_repeat", "low", 0, "Take >=3 readings (re-zero between) for a reliable average");
    if (spread > 5 * res && spread > 0.005) add("scale_repeat", "low", 0, `Readings spread ${spread.toFixed(3)} g: check draft/level/zero`);
  } else add("scale_weight", "medium", 10, "No scale reading: precision weight is the primary check");

  let com = m.com_mm ?? null, tsc = null;
  const t2 = m.two_scale;
  if (com == null && t2 && t2.left_g != null && t2.right_g != null) {
    tsc = comFromTwoScales(t2.left_g, t2.right_g, t2.span_mm || 100, t2.left2_g ?? null, t2.right2_g ?? null);
    com = [tsc.offset_mm, 0];
  }
  if (com == null && m.imu_samples) com = estimateCom(m.imu_samples);
  if (com != null) {
    const sh = Math.hypot(com[0] - ref.com_mm[0], com[1] - ref.com_mm[1]);
    const how = tsc ? ` [two scales: x=${sgn(tsc.offset_mm, 2)} mm` + (tsc.flipped ? `, flip-corrected, placement ${sgn(tsc.placement_mm, 2)} mm cancelled` : ", single placement: rotate 180 deg and re-weigh to cancel placement error") + "]" : "";
    if (sh > 2 * ref.com_tol_mm) add("center_of_mass", "high", 30, `Center of mass shifted ${sh.toFixed(2)} mm toward (${sgn(com[0], 1)},${sgn(com[1], 1)})` + how);
    else if (sh > ref.com_tol_mm) add("center_of_mass", "medium", 12, `CoM shift ${sh.toFixed(2)} mm (tol ${ref.com_tol_mm})` + how);
    else add("center_of_mass", "ok", 0, `CoM shift ${sh.toFixed(2)} mm, normal` + how);
  }

  let rf = m.rf_rows ?? null;
  if (rf == null && m.rf_csv) rf = parseRfCsv(m.rf_csv);
  if (rf != null) {
    const floor = m.rf_noise_floor_dbm ?? -95;
    const hits = rf.filter((r) => r[2] > floor + 15), cell = hits.filter((r) => inCell(r[1]));
    if (cell.length) {
      const ts = cell.map((r) => r[0]).sort((a, b) => a - b); let per = null;
      if (ts.length > 2) {
        const gaps = ts.slice(1).map((b, i) => b - ts[i]).filter((g) => g > 1);
        per = gaps.length ? Math.round((gaps.reduce((a, b) => a + b, 0) / gaps.length) * 10) / 10 : null;
      }
      add("rf_emission", "critical", 45, `${cell.length} cellular-band bursts while device OFF in Faraday bag` + (per ? `, periodic ~${per}s` : "") + " — consistent with LTE/eSIM implant");
    } else if (hits.length) add("rf_emission", "medium", 10, `${hits.length} non-cellular emissions above floor`);
    else add("rf_emission", "ok", 0, "RF silent while powered off (expected)");
  }

  const att = m.attestation;
  if (att != null) {
    if (att === "pass") add("attestation", "ok", 0, "Ledger Genuine Check passed (note: does NOT detect added implants)");
    else if (att === "fail") add("attestation", "critical", 50, "Genuine Check / attestation FAILED");
    else add("attestation", "medium", 10, "Attestation not performed");
  }
  if (m.seal_broken) add("packaging", "medium", 10, "Packaging/seal anomaly reported");
  if (m.source && m.source !== "direct") add("provenance", "low", 5, `Bought via ${m.source} (not ledger.com direct)`);
  risk = Math.min(risk, 100);
  const verdict = risk >= 60 ? "TAMPERED - DO NOT USE" : risk >= 25 ? "SUSPICIOUS" : "LIKELY GENUINE";
  return { model, model_name: ref.name, risk, verdict, warnings, com_mm: com, weight_g: weight, remediation: risk >= 25 ? REMEDIATION : [], two_scale: tsc };
}
