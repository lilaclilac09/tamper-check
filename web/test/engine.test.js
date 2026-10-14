import { describe, it, expect } from "vitest";
import fixtures from "./fixtures.json";
import { score, estimateCom, comFromTwoScales, parseRfCsv } from "../src/engine.js";
import { scenario, imuSamples, rfLog, twoScaleReadings, rng } from "../src/simulator.js";
import { REFERENCE } from "../src/reference.js";
const W = (r, c) => r.warnings.find((w) => w.check === c);
const M = Object.keys(REFERENCE);

describe("parity with Python engine (fixtures from web/test/gen_fixtures.py)", () => {
  it.each(fixtures.map((f, i) => [i, f.input.label ?? f.input.model, f]))("case %i %s", (_i, _l, { input, expected }) => {
    const r = score(input);
    expect(r.verdict).toBe(expected.verdict);
    expect(r.risk).toBe(expected.risk);
    expect(r.remediation.length).toBe(expected.remediation.length);
    expect(r.warnings.map((w) => [w.check, w.severity, w.points])).toEqual(expected.warnings.map((w) => [w.check, w.severity, w.points]));
    expect(r.warnings.map((w) => w.message)).toEqual(expected.warnings.map((w) => w.message));
    if (expected.weight_g != null) expect(r.weight_g).toBeCloseTo(expected.weight_g, 9);
    if (expected.com_mm) { expect(r.com_mm[0]).toBeCloseTo(expected.com_mm[0], 6); expect(r.com_mm[1]).toBeCloseTo(expected.com_mm[1], 6); }
    if (expected.two_scale) expect(r.two_scale.offset_mm).toBeCloseTo(expected.two_scale.offset_mm, 9);
  });
});

describe("engine (mirrors tests/test_all.py)", () => {
  it("IMU fit recovers CoM", () => {
    const [cx, cy] = estimateCom(imuSamples([5, -2], rng(1), 0.8, 0)); expect(cx).toBeCloseTo(5, 6); expect(cy).toBeCloseTo(-2, 6);
    expect(Math.abs(estimateCom(imuSamples([3, 0], rng(2)))[0] - 3)).toBeLessThan(0.3);
  });
  it("RF bursts detected / silent", () => {
    const w = W(score({ model: "ledger-flex", rf_rows: parseRfCsv(rfLog(rng(0), true)) }), "rf_emission");
    expect(w.severity).toBe("critical"); expect(w.message).toContain("periodic");
    expect(W(score({ model: "ledger-flex", rf_csv: rfLog(rng(0)) }), "rf_emission").severity).toBe("ok");
  });
  it("two-scale math and flip cancels placement", () => {
    expect(comFromTwoScales(24, 26, 100).x1_mm).toBeCloseTo(2, 9);
    expect(comFromTwoScales(26, 24, 200).offset_mm).toBe(-4);
    const w = 57, d = 1.5, p = 3, S = 100, R1 = w * (0.5 + (d + p) / S), R2 = w * (0.5 + (-d + p) / S);
    const t = comFromTwoScales(w - R1, R1, S, w - R2, R2);
    expect(t.offset_mm).toBeCloseTo(d, 9); expect(t.placement_mm).toBeCloseTo(p, 9); expect(t.flipped).toBe(true);
    expect(() => comFromTwoScales(0, 0)).toThrow();
    for (let s = 0; s < 20; s++) { const r = twoScaleReadings(57, 1, rng(s)); expect(Math.abs(comFromTwoScales(r.left_g, r.right_g, r.span_mm, r.left2_g, r.right2_g).offset_mm - 1)).toBeLessThan(0.15); }
  });
  it("JS simulator scenarios give expected verdicts on all models", () => {
    for (const m of M) for (let s = 0; s < 25; s++) for (const method of ["imu", "two_scale"]) {
      expect(score(scenario(m, "genuine", s, 0.001, method)).verdict).toBe("LIKELY GENUINE");
      expect(score(scenario(m, "glue", s, 0.001, method)).verdict).not.toBe("LIKELY GENUINE");
      expect(score(scenario(m, "implant", s, 0.001, method)).verdict).toBe("TAMPERED - DO NOT USE");
      expect(score(scenario(m, "counterfeit", s, 0.001, method)).verdict).not.toBe("LIKELY GENUINE");
    }
  });
  it("unknown model throws", () => expect(() => score({ model: "nope" })).toThrow());
});
