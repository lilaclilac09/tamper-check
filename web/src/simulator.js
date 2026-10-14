// Port of tamper_check/simulator.py. Seeded PRNG (mulberry32 + Box-Muller) instead of Python's Mersenne Twister,
// so exact numbers differ from Python but the distributions and scenarios are the same. EXAMPLE data only.
import { REFERENCE } from "./reference.js";

export function rng(seed = 0) {
  let a = (seed + 0x9e3779b9) >>> 0;
  const random = () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const gauss = (mu, sd) => mu + sd * Math.sqrt(-2 * Math.log(1 - random())) * Math.cos(2 * Math.PI * random());
  const choice = (arr) => arr[Math.floor(random() * arr.length)];
  return { random, gauss, choice };
}

export function imuSamples(com, R, k = 0.8, noise = 0.05) {
  const pts = {};
  ["x", "y"].forEach((ax, i) => { pts[ax] = [-6, -3, 0, 3, 6].map((s) => [s, k * (com[i] - s) + R.gauss(0, noise)]); });
  return pts;
}

export function rfLog(R, implant = false, dur = 120, period = 30) {
  const lines = ["timestamp_s,freq_mhz,rssi_dbm"];
  for (let t = 0; t < dur; t += 2) lines.push(`${t},${R.choice([433.9, 868.3, 915.0, 1800.0, 2140.0])},${(-96 + R.gauss(0, 1.5)).toFixed(1)}`);
  if (implant) for (let t = 5; t < dur; t += period) for (let j = 0; j < 3; j++)
    lines.push(`${(t + j * 0.2).toFixed(1)},${R.choice([850.0, 1842.5, 2655.0])},${(-52 + R.gauss(0, 3)).toFixed(1)}`);
  return lines.join("\n");
}

export function twoScaleReadings(w, comX, R, span = 100, res = 0.001, placementSd = 0.8) {
  const p = R.gauss(0, placementSd), rd = (v) => Math.round(Math.round(v / res) * res * 10000) / 10000, out = { span_mm: span };
  for (const [sfx, x] of [["", comX + p], ["2", -comX + p + R.gauss(0, 0.03)]]) {
    const Rv = w * (0.5 + x / span);
    out[`left${sfx}_g`] = rd(w - Rv + R.gauss(0, 0.0007)); out[`right${sfx}_g`] = rd(Rv + R.gauss(0, 0.0007));
  }
  return out;
}

/** kind: genuine | glue | implant | counterfeit; method: imu | two_scale */
export function scenario(model = "ledger-flex", kind = "genuine", seed = 0, res = 0.001, method = "imu") {
  const R = rng(seed), ref = REFERENCE[model];
  let w = ref.weight_g + R.gauss(0, 0.008); const com = [R.gauss(0, 0.2), R.gauss(0, 0.2)];
  let rf = false, att = "pass", src = "direct";
  if (kind === "glue" || kind === "implant") {
    const added = kind === "glue" ? 0.35 : 1.2, off = ref.dims_mm[0] * 0.35;
    com[0] = (com[0] * w + off * added) / (w + added); w += added; src = "reseller"; rf = kind === "implant";
  }
  if (kind === "counterfeit") { att = "fail"; src = "marketplace"; }
  const reads = Array.from({ length: 5 }, () => Math.round(Math.round((w + R.gauss(0, 0.001)) / res) * res * 10000) / 10000);
  const d = { model, scale_readings_g: reads, scale_resolution_g: res };
  if (method === "two_scale") { d.two_scale = twoScaleReadings(w, com[0], R, 100, res); d.label = kind + " (two-scale)"; }
  else d.imu_samples = imuSamples(com, R);
  return { ...d, rf_csv: rfLog(R, rf), attestation: att, source: src, label: d.label ?? kind };
}
