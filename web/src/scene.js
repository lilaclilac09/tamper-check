// Scene-first interactive lab: step 1 (one mg scale + paper note), step 2 (two scales + ruler + 3D Ledger).
// Everything is computed locally with the same engine as the dashboard. Numbers you type are the only input.
import * as THREE from "three";
import { REFERENCE } from "./reference.js";
import { score, comFromTwoScales } from "./engine.js";

const $ = (id) => document.getElementById(id);
const model = () => $("model").value || "ledger-flex";
const NS = "http://www.w3.org/2000/svg";
const ease = (u) => 0.5 - 0.5 * Math.cos(Math.PI * Math.max(0, Math.min(1, u)));
function tween(ms, f) { return new Promise((res) => { const t0 = performance.now(); (function k(t) { const u = Math.min(1, (t - t0) / ms); f(ease(u)); u < 1 ? requestAnimationFrame(k) : res(); })(t0); }); }
const verdictClass = (r) => (r.risk >= 60 ? "critical" : r.risk >= 25 ? "medium" : "ok");

/* ---------------- step 1: weigh 3 times ---------------- */
const S1 = { readings: [], tared: false };
function lcd1(text) { $("lcd1").textContent = text; }
async function placeWallet(on) {
  const w = $("w1wallet"), from = on ? -140 : 0, to = on ? 0 : -140;
  if (on) w.style.display = "";
  await tween(450, (k) => w.setAttribute("transform", `translate(0,${from + (to - from) * k})`));
  if (!on) w.style.display = "none";
}
function noteLine(i, text, cls = "") {
  const t = document.createElementNS(NS, "text"); t.setAttribute("x", 650); t.setAttribute("y", 112 + i * 36); t.setAttribute("class", "hand " + cls); t.textContent = ""; $("note").appendChild(t);
  return new Promise((res) => { let n = 0; const iv = setInterval(() => { t.textContent = text.slice(0, ++n); if (n >= text.length) { clearInterval(iv); res(); } }, 45); });
}
async function tare1() { lcd1("0.000"); S1.tared = true; $("s1msg").textContent = "Tared: display reads 0.000 g. Now place the wallet and type the reading."; }
async function read1() {
  const v = parseFloat($("s1in").value); if (!(v > 0)) { $("s1msg").textContent = "Type the reading shown on your scale, e.g. 57.007"; return; }
  if (!S1.tared) { $("s1msg").textContent = "Tare first (display must read 0.000)."; return; }
  if (S1.readings.length >= 3) reset1(true);
  await placeWallet(true);
  await tween(700, (k) => lcd1((v * k).toFixed(3)));
  S1.readings.push(v); await noteLine(S1.readings.length - 1, `#${S1.readings.length}   ${v.toFixed(3)} g`);
  $("s1in").value = ""; await new Promise((r) => setTimeout(r, 350)); await placeWallet(false); S1.tared = false; lcd1("- - -");
  if (S1.readings.length < 3) { $("s1msg").textContent = `Reading ${S1.readings.length} of 3 noted. Tare again, then weigh again.`; return; }
  const avg = S1.readings.reduce((a, b) => a + b, 0) / 3, ref = REFERENCE[model()].weight_g, d = avg - ref;
  await noteLine(3, `avg ${avg.toFixed(3)} g`, "avg");
  await noteLine(4, `ref ${ref.toFixed(3)} g  Δ ${d >= 0 ? "+" : ""}${d.toFixed(3)}`, "ref");
  const r = score({ model: model(), scale_readings_g: S1.readings, scale_resolution_g: 0.001 });
  const c = verdictClass(r); $("s1v").innerHTML = `<span class="v ${c}">${r.verdict}</span> <span class=muted>risk ${r.risk}/100 · tolerance ±${REFERENCE[model()].weight_tol_g.toFixed(3)} g (example reference)</span>`;
  $("s1msg").textContent = Math.abs(d) <= REFERENCE[model()].weight_tol_g ? "Within tolerance of the reference weight." : "Heavier than the reference: something was added.";
}
function reset1(keepTare) { S1.readings = []; $("note").querySelectorAll("text.hand").forEach((t) => t.remove()); $("s1v").innerHTML = ""; if (!keepTare) { S1.tared = false; lcd1("- - -"); $("s1msg").textContent = "Step 1: press TARE (empty scale reads 0.000)."; } }

/* ---------------- step 2: two scales + ruler + 3D Ledger ---------------- */
let R2, scene, cam, wallet, comBall, lcdL, lcdR, rot = 0;
function lcdTexture() { const c = document.createElement("canvas"); c.width = 256; c.height = 96; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return { c, t }; }
function drawLcd(l, text) { const x = l.c.getContext("2d"); x.fillStyle = "#08140c"; x.fillRect(0, 0, 256, 96); x.fillStyle = "#78ff8c"; x.font = "bold 62px monospace"; x.textAlign = "center"; x.textBaseline = "middle"; x.fillText(text, 128, 52); l.t.needsUpdate = true; }
function buildScale(xpos) {
  const g = new THREE.Group(); const body = new THREE.Mesh(new THREE.BoxGeometry(70, 22, 70), new THREE.MeshStandardMaterial({ color: 0x9aa4b2, roughness: 0.5 })); body.position.y = 11; g.add(body);
  const pan = new THREE.Mesh(new THREE.CylinderGeometry(22, 22, 3, 40), new THREE.MeshStandardMaterial({ color: 0xd8dde3, metalness: 0.5, roughness: 0.3 })); pan.position.y = 24; g.add(pan);
  const l = lcdTexture(); const scr = new THREE.Mesh(new THREE.PlaneGeometry(52, 19.5), new THREE.MeshBasicMaterial({ map: l.t })); scr.position.set(0, 11, 35.2); g.add(scr);
  g.position.x = xpos; scene.add(g); return l;
}
function buildLedger() {
  const ref = REFERENCE[model()], [x, y, z] = ref.dims_mm, g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.BoxGeometry(x, z, y), new THREE.MeshStandardMaterial({ color: 0x3a3f47, metalness: 0.4, roughness: 0.4 })));
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(x * 0.6, y * 0.72), new THREE.MeshStandardMaterial({ color: 0x0b0f14, emissive: 0x1d3a55 })); scr.rotation.x = -Math.PI / 2; scr.position.set(-x * 0.12, z / 2 + 0.05, 0); g.add(scr);
  const btn = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 3.2, 1, 24), new THREE.MeshStandardMaterial({ color: 0xc9ced6 })); btn.position.set(x * 0.36, z / 2 + 0.4, 0); g.add(btn);
  const tag = new THREE.Mesh(new THREE.BoxGeometry(4, 0.6, y * 0.9), new THREE.MeshBasicMaterial({ color: 0x3fb950 })); tag.position.set(x / 2 - 2, z / 2 + 0.3, 0); g.add(tag); // green edge = "this end"
  g.position.y = 24 + 1.5 + 4 + z / 2; return g;
}
function init3d() {
  const el = $("s2v"); R2 = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); R2.setSize(el.clientWidth, 380); R2.setClearColor(0x0d1117); el.appendChild(R2.domElement);
  scene = new THREE.Scene(); cam = new THREE.PerspectiveCamera(32, el.clientWidth / 380, 1, 3000); cam.position.set(0, 150, 330); cam.lookAt(0, 25, 0);
  scene.add(new THREE.AmbientLight(0xffffff, 0.75)); const L = new THREE.DirectionalLight(0xffffff, 1.3); L.position.set(80, 200, 160); scene.add(L);
  const table = new THREE.Mesh(new THREE.BoxGeometry(520, 4, 160), new THREE.MeshStandardMaterial({ color: 0x2a2219 })); table.position.y = -2; scene.add(table);
  lcdL = buildScale(-100); lcdR = buildScale(100); drawLcd(lcdL, "- - -"); drawLcd(lcdR, "- - -");
  const ruler = new THREE.Mesh(new THREE.BoxGeometry(260, 4, 26), new THREE.MeshStandardMaterial({ color: 0xc4a064 })); ruler.position.y = 24 + 1.5 + 2; scene.add(ruler);
  const mid = new THREE.Mesh(new THREE.BoxGeometry(1, 0.5, 26), new THREE.MeshBasicMaterial({ color: 0x3fb950 })); mid.position.y = 30; scene.add(mid);
  wallet = buildLedger(); wallet.visible = false; scene.add(wallet);
  comBall = new THREE.Mesh(new THREE.SphereGeometry(4), new THREE.MeshStandardMaterial({ color: 0xffd33d, emissive: 0x664400 })); comBall.visible = false; scene.add(comBall);
  (function loop() { requestAnimationFrame(loop); R2.render(scene, cam); })();
}
const n = (id) => parseFloat($(id).value);
function syncLcd() {
  const a = rot ? n("s2l2") : n("s2l"), b = rot ? n("s2r2") : n("s2r");
  if ($("s2tared").dataset.on) { drawLcd(lcdL, a > 0 ? a.toFixed(3) : wallet.visible ? "…" : "0.000"); drawLcd(lcdR, b > 0 ? b.toFixed(3) : wallet.visible ? "…" : "0.000"); }
}
function tare2() { $("s2tared").dataset.on = "1"; drawLcd(lcdL, "0.000"); drawLcd(lcdR, "0.000"); $("s2msg").textContent = "Ruler on, both tared to 0.000. Place the wallet in the middle."; }
async function place2() {
  if (!$("s2tared").dataset.on) { $("s2msg").textContent = "Tare both scales first."; return; }
  wallet.visible = true; const y = wallet.position.y; await tween(500, (k) => (wallet.position.y = y + 80 * (1 - k)));
  syncLcd(); $("s2msg").textContent = "Type the Left and Right readings.";
}
async function rotate2() {
  if (!wallet.visible) return; rot = 1; const a = wallet.rotation.y; await tween(1100, (k) => (wallet.rotation.y = a + Math.PI * k));
  syncLcd(); $("s2msg").textContent = "Rotated 180° in place. Type the new Left and Right readings.";
}
function compute2() {
  const L = n("s2l"), R = n("s2r"), L2 = n("s2l2"), Rb = n("s2r2"), S = n("s2span") || 100;
  if (!(L + R > 0)) { $("s2msg").textContent = "Type L and R first."; return; }
  const t = comFromTwoScales(L, R, S, L2 + Rb > 0 ? L2 : null, L2 + Rb > 0 ? Rb : null);
  const m = { model: model(), two_scale: { left_g: L, right_g: R, span_mm: S, ...(t.flipped ? { left2_g: L2, right2_g: Rb } : {}) } };
  if (S1.readings.length) { m.scale_readings_g = S1.readings; m.scale_resolution_g = 0.001; }
  const r = score(m), c = verdictClass(r), tol = REFERENCE[model()].com_tol_mm;
  comBall.visible = true; comBall.position.set(t.offset_mm * 20, wallet.position.y + 12, 0); // ×20 exaggerated
  const heavyFollows = t.flipped && Math.sign(R - L) !== Math.sign(Rb - L2) && Math.abs(t.offset_mm) > tol;
  $("s2out").innerHTML = `x1 = ${t.x1_mm.toFixed(2)} mm` + (t.flipped ? ` · x2 = ${t.x2_mm.toFixed(2)} mm · <b>offset = (x1−x2)/2 = ${t.offset_mm >= 0 ? "+" : ""}${t.offset_mm.toFixed(2)} mm</b> · placement ${t.placement_mm.toFixed(2)} mm cancelled` : ` · rotate 180° and re-read to cancel placement error`);
  $("s2v2").innerHTML = `<span class="v ${c}">${r.verdict}</span> <span class=muted>risk ${r.risk}/100 · CoM tolerance ${tol} mm (example)</span>`;
  $("s2msg").textContent = Math.abs(t.offset_mm) <= tol ? "Balanced: the center of mass is where a genuine unit's is." : heavyFollows ? "The heavy side followed the wallet when rotated: extra mass inside that end." : "Center of mass is off-centre beyond tolerance.";
}
function reset2() { for (const i of ["s2l", "s2r", "s2l2", "s2r2"]) $(i).value = ""; rot = 0; wallet.rotation.y = 0; wallet.visible = false; comBall.visible = false; delete $("s2tared").dataset.on; drawLcd(lcdL, "- - -"); drawLcd(lcdR, "- - -"); $("s2out").textContent = ""; $("s2v2").innerHTML = ""; $("s2msg").textContent = "Step 2: lay the ruler across both scales and press TARE BOTH."; }

export function initScene() {
  $("s1tare").onclick = tare1; $("s1read").onclick = read1; $("s1reset").onclick = () => reset1(false);
  $("s1in").addEventListener("keydown", (e) => e.key === "Enter" && read1());
  init3d(); $("s2tare").onclick = tare2; $("s2place").onclick = place2; $("s2rot").onclick = rotate2; $("s2calc").onclick = compute2; $("s2reset").onclick = reset2;
  for (const i of ["s2l", "s2r", "s2l2", "s2r2"]) $(i).addEventListener("input", syncLcd);
  $("model").addEventListener("change", () => { scene.remove(wallet); wallet = buildLedger(); wallet.visible = false; scene.add(wallet); reset2(); reset1(false); });
  reset1(false); reset2();
}
