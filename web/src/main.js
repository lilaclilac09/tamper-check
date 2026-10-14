import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { REFERENCE } from "./reference.js";
import { score } from "./engine.js";
import { scenario } from "./simulator.js";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const HISTORY = []; let seed = 0;
for (const k in REFERENCE) $("model").innerHTML += `<option value=${k}>${REFERENCE[k].name}</option>`;
$("model").value = "ledger-flex";

function twoCalc() {
  const n = (id) => parseFloat($(id).value), L = n("ls"), R = n("rs"), L2 = n("ls2"), R2 = n("rs2"), S = n("span") || 100;
  if (!(L + R > 0)) { $("twox").textContent = ""; return null; }
  const x1 = ((R - L) / (R + L)) * S / 2; let t = `x1 = ${x1 >= 0 ? "+" : ""}${x1.toFixed(2)} mm`; const o = { left_g: L, right_g: R, span_mm: S };
  if (L2 + R2 > 0) { const x2 = ((R2 - L2) / (R2 + L2)) * S / 2, d = (x1 - x2) / 2; t += ` · x2 = ${x2 >= 0 ? "+" : ""}${x2.toFixed(2)} mm · CoM offset (x1−x2)/2 = ${d >= 0 ? "+" : ""}${d.toFixed(2)} mm · placement ${((x1 + x2) / 2).toFixed(2)} mm cancelled`; o.left2_g = L2; o.right2_g = R2; }
  $("twox").textContent = t; return o;
}
document.addEventListener("input", (e) => { if (["ls", "rs", "ls2", "rs2", "span"].includes(e.target.id)) twoCalc(); });

function run(m) {
  let r; try { r = score(m); } catch (e) { $("res").innerHTML = `<b class=high>${esc(e.message)}</b>`; return; }
  r.label = m.label || "manual"; r.id = HISTORY.length + 1; HISTORY.push(r); show(r);
}
function show(r) {
  if (r.two_scale) { const t = r.two_scale; $("ls").value = t.left_g; $("rs").value = t.right_g; $("ls2").value = t.left2_g ?? ""; $("rs2").value = t.right2_g ?? ""; $("span").value = t.span_mm; twoCalc(); }
  draw3d(r); const c = r.risk >= 60 ? "critical" : r.risk >= 25 ? "medium" : "ok";
  $("res").innerHTML = `<div>${esc(r.model_name)} — <i>${esc(r.label)}</i></div><div class="v ${c}">${r.verdict}</div><div>Risk ${r.risk}/100</div><div class=bar><div class="fill" style="width:${r.risk}%;background:${c == "ok" ? "#3fb950" : c == "medium" ? "#d29922" : "#f85149"}"></div></div>
<table>${r.warnings.map((w) => `<tr><td>${w.check}</td><td class=${w.severity}>${w.severity.toUpperCase()}</td><td>${esc(w.message)}</td></tr>`).join("")}</table>${r.remediation.length ? `<div style="margin-top:12px;padding:10px;border:1px solid #f85149;border-radius:8px"><b>Remediation checklist</b><ol>${r.remediation.map((x) => `<li><label><input type=checkbox> ${esc(x)}</label></li>`).join("")}</ol></div>` : ""}`;
  $("hist").innerHTML = "<tr><th>#</th><th>model</th><th>scenario</th><th>risk</th><th>verdict</th></tr>" + HISTORY.slice().reverse().map((h) => `<tr><td>${h.id}</td><td>${h.model}</td><td>${esc(h.label)}</td><td>${h.risk}</td><td class=${h.risk >= 60 ? "critical" : h.risk >= 25 ? "medium" : "ok"}>${h.verdict}</td></tr>`).join("");
}
window.sim = (k, m = "imu") => {
  if (m == "imu") { for (const i of ["ls", "rs", "ls2", "rs2"]) $(i).value = ""; twoCalc(); }
  run(scenario($("model").value, k, seed++, 0.001, m));
};
window.manual = async () => {
  const b = { model: $("model").value, attestation: $("att").value, scale_resolution_g: +$("resol").value };
  if ($("w").value) b.scale_readings_g = $("w").value.split(",").map(Number).filter((x) => !isNaN(x));
  if ($("cx").value || $("cy").value) b.com_mm = [+$("cx").value || 0, +$("cy").value || 0]; else { const t = twoCalc(); if (t) b.two_scale = t; }
  if ($("rf").files[0]) b.rf_csv = await $("rf").files[0].text(); // read locally via File API, never uploaded
  run(b);
};

// 3D view
const el = $("v3d"), Rn = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
Rn.setSize(el.clientWidth, 300); Rn.setClearColor(0x0d1117); el.appendChild(Rn.domElement);
const S = new THREE.Scene(), C = new THREE.PerspectiveCamera(40, el.clientWidth / 300, 1, 2000); C.position.set(0, 90, 120);
const O = new OrbitControls(C, Rn.domElement);
S.add(new THREE.AmbientLight(0xffffff, 0.6)); const Lt = new THREE.DirectionalLight(0xffffff, 1.2); Lt.position.set(50, 100, 80); S.add(Lt);
S.add(new THREE.GridHelper(200, 20, 0x30363d, 0x21262d));
let G = new THREE.Group(); S.add(G);
function draw3d(r) {
  S.remove(G); G = new THREE.Group(); S.add(G); const ref = REFERENCE[r.model]; if (!ref) return; const [x, y, z] = ref.dims_mm;
  const body = new THREE.Mesh(new THREE.BoxGeometry(x, z, y), new THREE.MeshStandardMaterial({ color: 0x2b2f36, metalness: 0.6, roughness: 0.4 })); body.position.y = z / 2; G.add(body);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(x * 0.6, y * 0.7), new THREE.MeshStandardMaterial({ color: 0x111111, emissive: 0x223344 })); scr.rotation.x = -Math.PI / 2; scr.position.set(-x * 0.1, z + 0.05, 0); G.add(scr);
  const com = r.com_mm || [0, 0], flag = r.warnings.some((w) => (w.check == "scale_weight" || w.check == "center_of_mass") && w.severity != "ok");
  const m = new THREE.Mesh(new THREE.SphereGeometry(2.2), new THREE.MeshStandardMaterial({ color: 0xffd33d, emissive: 0x664400 })); m.position.set(com[0] * 5, z + 3, com[1] * 5); G.add(m);
  const c0 = new THREE.Mesh(new THREE.SphereGeometry(1.2), new THREE.MeshBasicMaterial({ color: 0x3fb950 })); c0.position.set(0, z + 3, 0); G.add(c0);
  if (flag) { const side = com[0] >= 0 ? 1 : -1, hot = new THREE.Mesh(new THREE.BoxGeometry(x * 0.25, z * 1.05, y * 0.9), new THREE.MeshStandardMaterial({ color: 0xf85149, transparent: true, opacity: 0.55, emissive: 0x550000 })); hot.position.set(side * x * 0.36, z / 2, 0); G.add(hot); }
  if (r.warnings.find((w) => w.check == "rf_emission" && w.severity == "critical")) for (let i = 1; i < 4; i++) { const t = new THREE.Mesh(new THREE.TorusGeometry(x * 0.3 * i, 0.4, 8, 64), new THREE.MeshBasicMaterial({ color: 0xf85149, transparent: true, opacity: 0.6 / i })); t.rotation.x = Math.PI / 2; t.position.set(x * 0.36, z, 0); G.add(t); }
}
draw3d({ model: "ledger-flex", warnings: [], com_mm: [0, 0] });
(function loop() { requestAnimationFrame(loop); G.rotation.y += 0.004; O.update(); Rn.render(S, C); })();
document.querySelectorAll("[data-sim]").forEach((b) => b.addEventListener("click", () => window.sim(b.dataset.sim, b.dataset.m || "imu")));
$("check").addEventListener("click", () => window.manual());
