#!/usr/bin/env node
/*
 * Builds Kiki's guide artwork (assets/Kiki/*.svg) from one set of shapes, so every scene
 * shares the same pointer, trail, halo, step badges and path grammar.
 *
 * Kiki is a companion cursor (in the spirit of Clicky): it lives beside the student's own
 * cursor or finger, flies to the thing that matters, and shows the route: the current step
 * gets a halo and a filled number, the next steps appear ahead as ghost numbers on a dashed
 * path, finished steps are ticked. The four dots trail behind it along the path it flew.
 *
 * Usage: node design-system/tools/build-kiki.js
 */
const fs = require('fs');
const path = require('path');
const OUT = path.join(__dirname, '..', 'project', 'assets', 'Kiki');

const C = {
  paper: '#fbfaf7', raised: '#ffffff', ink: '#1f1f1f', pencil: '#5f6368', line: '#d9d6cf', grid: '#e3e1dc', wire: '#3c4043',
  blue: '#4285f4', blueInk: '#1967d2', blueTint: '#e8f0fe',
  red: '#ea4335', redInk: '#c5221f', redTint: '#fce8e6',
  yellow: '#fbbc05', yellowInk: '#9a5500',
  green: '#34a853', greenInk: '#137333', greenTint: '#e6f4ea'
};
const DOTS = [C.blue, C.red, C.yellow, C.green];
const FONT = "Noto Sans, Roboto, Arial, sans-serif";
/* Concept is green, Lab (practical) is blue. Kiki's own dots keep Google's order (DOTS). */
const SKILL = { concept: [C.green, C.greenInk, C.greenTint], words: [C.red, C.redInk, C.redTint], lab: [C.blue, C.blueInk, C.blueTint] };
const f = (n) => Math.round(n * 100) / 100;

/* ---------------- the pointer ---------------- */
const BODY = 'M12 8 L12 46 L21.5 37.5 L28.5 53 L35 50 L28 35 L40 35 Z';
const EYES = [[16.8, 25], [23.4, 25]];
/** Kiki's pointer with its tip at (x, y). gaze: a screen point the eyes look at. mood: 'happy' squints. */
function pointer(x, y, { s = 0.62, rot = 0, gaze = null, mood = null } = {}) {
  const r = (rot * Math.PI) / 180;
  const toScreen = (lx, ly) => { const dx = (lx - 12) * s, dy = (ly - 8) * s; return [x + dx * Math.cos(r) - dy * Math.sin(r), y + dx * Math.sin(r) + dy * Math.cos(r)]; };
  const eyes = EYES.map(([ex, ey]) => {
    let px = ex, py = ey;
    if (gaze && mood !== 'happy') {
      const [sx, sy] = toScreen(ex, ey);
      let vx = gaze[0] - sx, vy = gaze[1] - sy; // screen vector -> local
      const lx = vx * Math.cos(-r) - vy * Math.sin(-r), ly = vx * Math.sin(-r) + vy * Math.cos(-r);
      const len = Math.hypot(lx, ly) || 1; px = ex + (lx / len) * 1.15; py = ey + (ly / len) * 1.15;
    }
    if (mood === 'happy') return `<path d="M${ex - 2.6} ${ey + 0.8} Q${ex} ${ey - 2.6} ${ex + 2.6} ${ey + 0.8}" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>`;
    return `<circle cx="${ex}" cy="${ey}" r="2.9" fill="#ffffff"/><circle cx="${f(px)}" cy="${f(py)}" r="1.35" fill="${C.ink}"/>`;
  }).join('');
  const svg = `<g transform="translate(${f(x)} ${f(y)}) rotate(${rot}) scale(${s}) translate(-12 -8)"><path d="${BODY}" fill="${C.ink}" stroke="#ffffff" stroke-width="3.2" stroke-linejoin="round"/>${eyes}</g>`;
  return { svg, tail: toScreen(31, 52), toScreen };
}

/** Flight trail: a faint dotted line from `from` along a curve to the pointer's tail, with the four dots closest to Kiki. */
function trail(from, to, { bend = 0.25, dotR = 2.6, gap = 7.5, line = true } = {}) {
  const mx = (from[0] + to[0]) / 2, my = (from[1] + to[1]) / 2;
  const nx = -(to[1] - from[1]), ny = to[0] - from[0];
  const c = [mx + nx * bend, my + ny * bend];
  const pts = []; for (let i = 0; i <= 200; i++) { const t = i / 200, u = 1 - t; pts.push([u * u * from[0] + 2 * u * t * c[0] + t * t * to[0], u * u * from[1] + 2 * u * t * c[1] + t * t * to[1]]); }
  const cum = [0]; for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const total = cum.at(-1);
  const at = (d) => { const target = total - d; let i = cum.findIndex((v) => v >= target); if (i < 0) i = pts.length - 1; return pts[i]; };
  const dots = DOTS.map((col, k) => { const [px, py] = at(6 + k * gap); return `<circle cx="${f(px)}" cy="${f(py)}" r="${dotR}" fill="${col}"/>`; }).join('');
  const lastD = 6 + 3 * gap + gap; const endIdx = cum.findIndex((v) => v >= total - lastD);
  const ln = line && endIdx > 2 ? `<path d="M${f(from[0])} ${f(from[1])} Q${f(c[0])} ${f(c[1])} ${f(pts[endIdx][0])} ${f(pts[endIdx][1])}" fill="none" stroke="${C.pencil}" stroke-width="1.4" stroke-linecap="round" stroke-dasharray="0.1 5" opacity="0.55"/>` : '';
  return ln + dots;
}

/* ---------------- guidance marks ---------------- */
function halo(x, y, r, skill = 'concept', { pulse = true } = {}) {
  const [col, , tint] = SKILL[skill];
  const anim = pulse ? `<animate attributeName="r" values="${r + 3};${r + 9};${r + 3}" dur="1.8s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.5;0;0.5" dur="1.8s" repeatCount="indefinite"/>` : '';
  return `<circle cx="${x}" cy="${y}" r="${r}" fill="${tint}" fill-opacity="0.75" stroke="${col}" stroke-width="2.2"/><circle cx="${x}" cy="${y}" r="${r + 3}" fill="none" stroke="${col}" stroke-width="1.6" opacity="0.5">${anim}</circle>`;
}
function haloRect(x, y, w, h, skill = 'concept', dashed = false) {
  const [col, , tint] = SKILL[skill];
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="10" fill="${tint}" fill-opacity="${dashed ? 0.35 : 0.75}" stroke="${col}" stroke-width="2" ${dashed ? 'stroke-dasharray="5 4"' : ''}/>`;
}
/** Step badge. state: 'now' (filled number), 'next' (ghost number), 'done' (tick). */
function badge(n, x, y, state = 'now', skill = 'concept') {
  const [col, ink] = SKILL[skill];
  if (state === 'now') return `<circle cx="${x}" cy="${y}" r="9.5" fill="${ink}" stroke="#ffffff" stroke-width="2"/><text x="${x}" y="${y + 4}" text-anchor="middle" font-family="${FONT}" font-size="11.5" font-weight="700" fill="#ffffff">${n}</text>`;
  if (state === 'done') return `<circle cx="${x}" cy="${y}" r="9.5" fill="${col}" stroke="#ffffff" stroke-width="2"/><path d="M${x - 4.2} ${y + 0.2} L${x - 1.2} ${y + 3.2} L${x + 4.4} ${y - 3}" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>`;
  return `<circle cx="${x}" cy="${y}" r="9" fill="#ffffff" stroke="${col}" stroke-width="1.8" stroke-dasharray="3 2.5"/><text x="${x}" y="${y + 4}" text-anchor="middle" font-family="${FONT}" font-size="11" font-weight="700" fill="${ink}">${n}</text>`;
}
/** The route still ahead: dashed, flowing gently towards the next step. */
function ahead(d, skill = 'concept') {
  const [col] = SKILL[skill];
  return `<path d="${d}" fill="none" stroke="${col}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1 6"><animate attributeName="stroke-dashoffset" values="14;0" dur="1.2s" repeatCount="indefinite"/></path>`;
}
/** The route already walked: solid and bold. */
function walked(d, skill = 'concept') {
  const [col] = SKILL[skill];
  return `<path d="${d}" fill="none" stroke="${col}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>`;
}
function arrow(d, skill = 'concept', id = 'a') {
  const [, ink] = SKILL[skill];
  return `<defs><marker id="kk-${id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="${ink}"/></marker></defs><path d="${d}" fill="none" stroke="${ink}" stroke-width="2" stroke-linecap="round" marker-end="url(#kk-${id})"/>`;
}
function chip(x, y, text, { w = null, skill = null, anchor = 'start', icon = null } = {}) {
  const width = w || Math.round(text.length * 6.3 + (icon ? 34 : 22));
  const x0 = anchor === 'middle' ? x - width / 2 : x;
  const stroke = skill ? SKILL[skill][0] : C.line, fill = skill ? SKILL[skill][2] : C.raised, ink = skill ? SKILL[skill][1] : C.ink;
  const ic = icon === 'kiki' ? DOTS.map((col, i) => `<circle cx="${x0 + 10 + (i % 2) * 5}" cy="${y + 9 + Math.floor(i / 2) * 5}" r="2" fill="${col}"/>`).join('') : '';
  return `<rect x="${f(x0)}" y="${y}" width="${width}" height="24" rx="12" fill="${fill}" stroke="${stroke}" stroke-width="1.2"/>${ic}<text x="${f(x0 + (icon ? 24 : 11))}" y="${y + 16}" font-family="${FONT}" font-size="11.5" font-weight="600" fill="${ink}">${text}</text>`;
}
function studentCursor(x, y) {
  return `<g transform="translate(${x} ${y}) scale(0.5) translate(-12 -8)"><path d="${BODY}" fill="#ffffff" stroke="${C.pencil}" stroke-width="2.4" stroke-linejoin="round"/></g>`;
}
function tapMark(x, y, label) {
  return `<circle cx="${x}" cy="${y}" r="11" fill="none" stroke="${C.pencil}" stroke-width="1.6"/><circle cx="${x}" cy="${y}" r="3" fill="${C.pencil}"/>` + (label ? `<text x="${x + 15}" y="${y + 4}" font-family="${FONT}" font-size="10.5" fill="${C.pencil}">${label}</text>` : '');
}

/* ---------------- the worked diagram: R3 in series, then R1 and R2 in parallel ---------------- */
const zz = (x, y1, y2, amp = 7, n = 6) => { let d = `M${x} ${y1}`; const h = (y2 - y1) / n; for (let i = 0; i < n; i++) d += ` L${x + (i % 2 ? -amp : amp)} ${y1 + h * (i + 0.5)}`; return d + ` L${x} ${y2}`; };
const zzH = (x1, x2, y, amp = 7, n = 6) => { let d = `M${x1} ${y}`; const w = (x2 - x1) / n; for (let i = 0; i < n; i++) d += ` L${x1 + w * (i + 0.5)} ${y + (i % 2 ? amp : -amp)}`; return d + ` L${x2} ${y}`; };
const P = { top: 48, bot: 172, bat: 44, r3a: 84, r3b: 132, r1: 184, r2: 264, r1a: 88, r1b: 132 };
function circuit({ fade = 1, slot = false } = {}) {
  const w = `stroke="${C.wire}" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"`;
  const lbl = (x, y, t) => `<text x="${x}" y="${y}" font-family="${FONT}" font-size="11" font-weight="600" fill="${C.pencil}">${t}</text>`;
  const r3 = slot ? `<rect x="${P.r3a}" y="${P.top - 10}" width="${P.r3b - P.r3a}" height="20" rx="4" fill="none" stroke="${C.pencil}" stroke-width="1.4" stroke-dasharray="4 3"/>` : `<path d="${zzH(P.r3a, P.r3b, P.top)}" ${w}/>`;
  return `<g opacity="${fade}">
<path d="M${P.bat} 104 V${P.top} H${P.r3a} M${P.r3b} ${P.top} H${P.r2} V${P.r1a} M${P.r2} ${P.r1b} V${P.bot} H${P.bat} V114" ${w}/>
<path d="M${P.r1} ${P.top} V${P.r1a} M${P.r1} ${P.r1b} V${P.bot}" ${w}/>
${r3}<path d="${zz(P.r1, P.r1a, P.r1b)}" ${w}/><path d="${zz(P.r2, P.r1a, P.r1b)}" ${w}/>
<path d="M32 104 H56" stroke="${C.wire}" stroke-width="1.8"/><path d="M38 114 H50" stroke="${C.wire}" stroke-width="3.4"/>
<circle cx="${P.r1}" cy="${P.top}" r="3" fill="${C.wire}"/><circle cx="${P.r1}" cy="${P.bot}" r="3" fill="${C.wire}"/>
${lbl(60, 102, '+')}${slot ? lbl(98, 74, 'R3') : lbl(102, 34, 'R3')}${lbl(199, 114, 'R1')}${lbl(279, 114, 'R2')}
</g>`;
}

/* ---------------- frames ---------------- */
const W = 320, H = 220;
function frame(inner, { title = '', label = '' } = {}) {
  let grid = ''; for (let gx = 8; gx < W; gx += 16) for (let gy = 8; gy < H; gy += 16) grid += `<circle cx="${gx}" cy="${gy}" r="0.8" fill="${C.grid}"/>`;
  return { inner: `<rect width="${W}" height="${H}" rx="16" fill="${C.paper}"/>${grid}${inner}`, title, label };
}
const svgDoc = (w, h, body, title) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${title}">\n<title>${title}</title>\n${body}\n</svg>\n`;

const scenes = {};
const S = 0.76; // pointer scale inside scenes
// Kiki's marks run beside a wire (a rail 8px off it), never on top of the student's diagram.
const RT = P.top - 8, RB = P.bot + 8, RX2 = P.r2 + 30;

// 1. Look here: Kiki flies from beside the student's cursor to R1 and haloes it.
{
  const k = pointer(205, 131, { s: S, gaze: [P.r1, 110] });
  scenes.look = frame(
    circuit() + halo(P.r1, 110, 30) + badge(1, 159, 84, 'now') + studentCursor(286, 178) + trail([292, 192], k.tail, { bend: -0.3 }) + k.svg + chip(16, 186, 'Look here first: R1', { icon: 'kiki' }),
    { title: 'Kiki guide: look here', label: 'Look here' });
}
// 2. Path ahead: step 1 now, steps 2 and 3 waiting on a dashed route; Kiki already looks at step 2.
{
  const k = pointer(194, 58, { s: S, gaze: [P.r2, RT] });
  scenes.pathAhead = frame(
    circuit() + ahead(`M${P.r1 + 14} ${RT} H${RX2} V${P.bot}`) + halo(P.r1, P.top, 11) + badge(1, P.r1 - 19, P.top - 16, 'now') + badge(2, RX2, RT - 14, 'next') + badge(3, RX2, P.bot + 14, 'next')
    + trail([300, 204], k.tail, { bend: 0.22, line: false }) + k.svg + chip(16, 186, 'Step 1 now. 2 and 3 are next', { icon: 'kiki' }),
    { title: 'Kiki guide: path ahead', label: 'Path ahead' });
}
// 3. Trace: Kiki rides beside the wire from the battery; behind it the rail is solid, ahead it is dashed.
{
  const RL = P.bat - 9;
  const up = (x, y) => `<path d="M${x - 4} ${y + 3} L${x} ${y - 2} L${x + 4} ${y + 3}" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>`;
  const right = (x, y) => `<path d="M${x - 3} ${y - 4} L${x + 2} ${y} L${x - 3} ${y + 4}" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>`;
  const k = pointer(152, RT + 1, { s: S, rot: -8, gaze: [P.r1, P.top] });
  scenes.trace = frame(
    circuit() + walked(`M${RL} 100 V${RT} H148`) + up(RL, 74) + right(70, RT) + right(112, RT) + ahead(`M158 ${RT} H${P.r1}`) + badge(1, RL - 10, 112, 'done') + badge(2, P.r1 + 2, RT - 14, 'next')
    + trail([60, 210], k.tail, { bend: 0.2, line: false }) + k.svg + chip(16, 186, 'Follow the current with me', { icon: 'kiki' }),
    { title: 'Kiki guide: trace', label: 'Trace' });
}
// 4. Connect: Kiki links two parts and shows what they share.
{
  const k = pointer(228, 148, { s: S, gaze: [224, 108] });
  scenes.connect = frame(
    circuit() + walked(`M${P.r1} ${RT} H${P.r2}`) + walked(`M${P.r1} ${RB} H${P.r2}`) + haloRect(P.r1 - 14, P.r1a - 8, 28, 60) + haloRect(P.r2 - 14, P.r1a - 8, 28, 60)
    + `<text x="224" y="30" text-anchor="middle" font-family="${FONT}" font-size="12" font-weight="700" fill="${C.greenInk}">A</text><text x="290" y="${RB + 4}" font-family="${FONT}" font-size="12" font-weight="700" fill="${C.greenInk}">B</text>`
    + arrow(`M${P.r1 + 18} 96 Q224 80 ${P.r2 - 20} 96`, 'concept', 'c1') + arrow(`M${P.r2 - 18} 124 Q224 140 ${P.r1 + 20} 124`, 'concept', 'c2')
    + trail([306, 206], k.tail, { bend: -0.2 }) + k.svg + chip(16, 196, 'Both join A and B: parallel', { icon: 'kiki' }),
    { title: 'Kiki guide: connect', label: 'Connect' });
}
// 5. Your turn: Kiki parks beside the target and waits; it never covers the thing to tap.
{
  const k = pointer(130, 74, { s: S, gaze: [108, P.top] });
  const ring = `<circle cx="108" cy="${P.top}" r="24" fill="${C.greenTint}" fill-opacity="0.6" stroke="${C.green}" stroke-width="2.2" stroke-dasharray="6 5"><animateTransform attributeName="transform" type="rotate" from="0 108 ${P.top}" to="360 108 ${P.top}" dur="6s" repeatCount="indefinite"/></circle>`;
  scenes.yourTurn = frame(
    circuit() + ring + badge(3, 80, 22, 'now') + trail([150, 160], k.tail, { bend: 0.1, line: false }) + k.svg + chip(16, 186, 'Your turn: tap the part in series', { icon: 'kiki' }),
    { title: 'Kiki guide: your turn', label: 'Your turn' });
}
// 6. Redirect: the student tapped somewhere else; Kiki draws the way from their tap to the target. No "wrong".
{
  const k = pointer(112, 72, { s: S, gaze: [108, P.top] });
  scenes.redirect = frame(
    circuit() + tapMark(P.r2, 110, '') + `<text x="${P.r2}" y="150" text-anchor="middle" font-family="${FONT}" font-size="10.5" fill="${C.pencil}">your tap</text>` + halo(108, P.top, 20)
    + arrow(`M${P.r2 - 12} 102 C232 66 180 30 ${133} ${P.top}`, 'concept', 'r1') + k.svg + DOTS.map((col, i) => `<circle cx="${140 + i * 7}" cy="${112 + i * 5}" r="2.6" fill="${col}"/>`).join('') + chip(16, 186, 'Close. Look here instead', { icon: 'kiki' }),
    { title: 'Kiki guide: redirect', label: 'Redirect' });
}
// 7. Show me: Kiki demonstrates a drag in the lab, from the parts tray to the empty slot.
{
  const tray = `<rect x="214" y="8" width="94" height="26" rx="8" fill="${C.raised}" stroke="${C.line}"/><text x="222" y="25" font-family="${FONT}" font-size="10.5" fill="${C.pencil}">Parts</text><path d="${zzH(256, 298, 21, 4, 6)}" fill="none" stroke="${C.pencil}" stroke-width="1.4" opacity="0.4"/>`;
  const ghost = `<rect x="150" y="12" width="44" height="18" rx="5" fill="${C.blueTint}" stroke="${C.blue}" stroke-width="1.8"/><path d="${zzH(154, 190, 21, 4, 6)}" fill="none" stroke="${C.blueInk}" stroke-width="1.6"/>`;
  const k = pointer(170, 26, { s: S, rot: -6, gaze: [108, P.top] });
  scenes.showMe = frame(
    circuit({ slot: true }) + walked(`M246 30 Q222 40 198 24`, 'lab') + ahead(`M146 24 Q118 22 110 34`, 'lab') + badge(1, 300, 44, 'done', 'lab') + badge(2, 74, 30, 'next', 'lab') + tray + ghost
    + trail([240, 110], k.tail, { bend: 0.1, line: false }) + k.svg + chip(16, 186, 'Watch: pick it up, drop it here', { icon: 'kiki', w: 182 }),
    { title: 'Kiki guide: show me', label: 'Show me' });
}
// 8. Ask: Kiki points between the two answers; the parts in question are lightly marked.
{
  const k = pointer(158, 168, { s: S, gaze: [158, 120] });
  scenes.ask = frame(
    circuit() + haloRect(P.r1 - 14, P.r1a - 8, 28, 60, 'concept', true) + haloRect(P.r2 - 14, P.r1a - 8, 28, 60, 'concept', true)
    + `<text x="16" y="17" font-family="${FONT}" font-size="12.5" font-weight="700" fill="${C.ink}">R1 and R2: series or parallel?</text>`
    + chip(64, 188, 'Series', { w: 72, anchor: 'middle' }) + chip(256, 188, 'Parallel', { w: 84, anchor: 'middle' })
    + k.svg + DOTS.map((col, i) => `<circle cx="${f(160 + 13 * Math.cos(Math.PI * (1.1 + i * 0.27)))}" cy="${f(150 + 13 * Math.sin(Math.PI * (1.1 + i * 0.27)))}" r="2.6" fill="${col}"/>`).join(''),
    { title: 'Kiki guide: ask', label: 'Ask' });
}
// 9. Done: the whole route turns solid and every step is ticked; Kiki hops.
{
  const k = pointer(222, 62, { s: S, gaze: [222, 40], mood: 'happy', rot: -8 });
  const burst = DOTS.map((col, i) => { const a = -0.95 + i * 0.6; return `<circle cx="${f(244 + 18 * Math.cos(a))}" cy="${f(74 + 18 * Math.sin(a))}" r="2.8" fill="${col}"/>`; }).join('');
  const hop = `<path d="M218 106 q12 -8 24 0" fill="none" stroke="${C.pencil}" stroke-width="1.4" stroke-linecap="round" opacity="0.6"/>`;
  scenes.done = frame(
    circuit() + walked(`M${P.r1 + 14} ${RT} H${RX2} V${P.bot}`) + badge(1, P.r1 - 19, P.top - 16, 'done') + badge(2, RX2, RT - 14, 'done') + badge(3, RX2, P.bot + 14, 'done')
    + hop + k.svg + burst + chip(16, 186, 'Parallel. You found it', { skill: 'concept' }),
    { title: 'Kiki guide: done', label: 'Done' });
}
// 10. Words: the same grammar on text. Kiki sweeps the term (red) and shows the next phrase ahead.
{
  const card = `<rect x="16" y="40" width="288" height="128" rx="12" fill="${C.raised}" stroke="${C.line}"/>`;
  const t = (x, y, s, len, w = 400, col = C.ink) => `<text x="${x}" y="${y}" font-family="${FONT}" font-size="14" font-weight="${w}" fill="${col}" textLength="${len}" lengthAdjust="spacingAndGlyphs">${s}</text>`;
  const sweep = `<rect x="153" y="68" width="70" height="22" rx="5" fill="${C.redTint}"/><path d="M153 92 H223" stroke="${C.red}" stroke-width="3" stroke-linecap="round"/>`;
  const k = pointer(224, 96, { s: S, gaze: [80, 150] });
  scenes.words = frame(
    card + sweep + t(32, 84, 'R1 and R2 are in', 116) + t(157, 84, 'parallel', 62, 700, C.redInk) + t(32, 116, 'because they share', 124) + t(32, 148, 'both nodes.', 78)
    + ahead('M32 156 H112') + badge(1, 146, 62, 'now', 'words') + badge(2, 126, 150, 'next') + trail([300, 204], k.tail, { bend: -0.2 }) + k.svg + chip(16, 186, 'This word first, then why', { icon: 'kiki' }),
    { title: 'Kiki guide: words', label: 'Words' });
}
// 11. Think: Kiki reads the screen; a scan line passes over the diagram while the dots orbit.
{
  const k = pointer(232, 128, { s: S, gaze: [150, 100] });
  const orbit = DOTS.map((col, i) => `<circle r="2.6" fill="${col}" cx="${f(250 + 17 * Math.cos(i * Math.PI / 2))}" cy="${f(150 + 17 * Math.sin(i * Math.PI / 2))}"><animateTransform attributeName="transform" type="rotate" from="0 250 150" to="360 250 150" dur="2.4s" repeatCount="indefinite"/></circle>`).join('');
  const scan = `<rect x="24" y="60" width="272" height="16" fill="${C.green}" opacity="0.12"><animate attributeName="y" values="40;160;40" dur="3s" repeatCount="indefinite"/></rect>`;
  scenes.think = frame(circuit() + scan + k.svg + orbit + chip(16, 186, 'Reading your diagram', { icon: 'kiki' }), { title: 'Kiki guide: thinking', label: 'Thinking' });
}
// 12. Listen: Kiki listens to the student; the dots become a level meter.
{
  const k = pointer(136, 82, { s: S, gaze: [140, 200] });
  const bars = DOTS.map((col, i) => { const hgt = [12, 22, 16, 9].at(i); return `<rect x="${166 + i * 9}" y="${132 - hgt / 2}" width="6" height="${hgt}" rx="3" fill="${col}"><animate attributeName="height" values="${hgt};${hgt / 2};${hgt}" dur="${0.6 + i * 0.15}s" repeatCount="indefinite"/></rect>`; }).join('');
  scenes.listen = frame(circuit({ fade: 0.35 }) + k.svg + bars + chip(16, 186, 'Listening: say it in your words', { icon: 'kiki' }), { title: 'Kiki guide: listening', label: 'Listening' });
}
// 13. Unsure: Kiki is not sure what the student means, so it offers the two candidates instead of guessing.
{
  const k = pointer(222, 146, { s: S, rot: 12, gaze: [224, 110] });
  scenes.unsure = frame(
    circuit() + haloRect(P.r1 - 16, P.r1a - 10, 32, 64, 'concept', true) + haloRect(P.r2 - 16, P.r1a - 10, 32, 64, 'concept', true) + badge('a', P.r1 - 16, P.r1a - 12, 'next') + badge('b', P.r2 - 16, P.r1a - 12, 'next')
    + k.svg + DOTS.map((col, i) => `<circle cx="${[252, 266, 246, 274].at(i)}" cy="${[150, 162, 174, 180].at(i)}" r="2.6" fill="${col}"/>`).join('') + chip(16, 186, 'Which one do you mean: a or b?', { icon: 'kiki' }),
    { title: 'Kiki guide: unsure', label: 'Unsure' });
}

const FILES = [
  ['look', 'kiki-guide-look.svg'], ['pathAhead', 'kiki-guide-path-ahead.svg'], ['trace', 'kiki-guide-trace.svg'], ['connect', 'kiki-guide-connect.svg'],
  ['yourTurn', 'kiki-guide-your-turn.svg'], ['redirect', 'kiki-guide-redirect.svg'], ['showMe', 'kiki-guide-show-me.svg'], ['ask', 'kiki-guide-ask.svg'],
  ['done', 'kiki-guide-done.svg'], ['words', 'kiki-guide-words.svg'], ['think', 'kiki-guide-thinking.svg'], ['listen', 'kiki-guide-listening.svg'], ['unsure', 'kiki-guide-unsure.svg']
];

/* ---------------- write ---------------- */
fs.mkdirSync(OUT, { recursive: true });
const written = [];
const write = (name, body) => { fs.writeFileSync(path.join(OUT, name), body); written.push(name); };

// The bare pointer: for avatars, slides and anywhere a scene is too much.
{
  const k = pointer(44, 36, { s: 1.05, gaze: [120, 20] });
  write('kiki-pointer.svg', svgDoc(160, 160, trail([150, 150], k.tail, { bend: -0.15, dotR: 4.2, gap: 11, line: false }) + k.svg, 'Kiki pointer'));
}
write('kiki-dots.svg', svgDoc(128, 128, `<circle cx="48" cy="48" r="14" fill="${C.blue}"/><circle cx="80" cy="48" r="14" fill="${C.red}"/><circle cx="48" cy="80" r="14" fill="${C.yellow}"/><circle cx="80" cy="80" r="14" fill="${C.green}"/>`, 'Kiki, four dots'));
FILES.forEach(([key, name]) => write(name, svgDoc(W, H, scenes[key].inner, scenes[key].title)));

// Storyboard: the series-or-parallel question, guided in four moves.
{
  const order = [['look', '1 · Kiki flies to the first thing to look at'], ['pathAhead', '2 · It shows the steps still ahead'], ['connect', '3 · It connects what they share'], ['yourTurn', '4 · Then it hands the next step to you']];
  const gap = 28, top = 64, sw = order.length * W + (order.length - 1) * gap + 48;
  let body = `<rect width="${sw}" height="${top + H + 56}" fill="${C.paper}"/><text x="24" y="38" font-family="${FONT}" font-size="20" font-weight="700" fill="${C.ink}">Series or parallel? Kiki guides one step at a time</text>`;
  order.forEach(([key, cap], i) => {
    const x = 24 + i * (W + gap);
    body += `<svg x="${x}" y="${top}" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${scenes[key].inner}</svg><text x="${x + 4}" y="${top + H + 28}" font-family="${FONT}" font-size="13" font-weight="600" fill="${C.ink}">${cap}</text>`;
    if (i < order.length - 1) body += `<path d="M${x + W + 6} ${top + H / 2} h${gap - 12}" stroke="${C.pencil}" stroke-width="1.6" marker-end="url(#sb-arrow)"/>`;
  });
  body = `<defs><marker id="sb-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="${C.pencil}"/></marker></defs>` + body;
  write('kiki-guide-storyboard.svg', svgDoc(sw, top + H + 56, body, 'Kiki storyboard: series or parallel'));
}

// Contact sheet of every move, for reviews.
{
  const cols = 4, tw = 240, th = 165, gx = 20, gy = 44, x0 = 24, y0 = 96;
  const items = [['pointer', 'Pointer'], ...FILES.map(([k]) => [k, scenes[k].label])];
  const rows = Math.ceil(items.length / cols), sw = x0 * 2 + cols * tw + (cols - 1) * gx, sh = y0 + rows * (th + gy) + 8;
  let body = `<rect width="${sw}" height="${sh}" fill="${C.paper}"/><text x="${x0}" y="42" font-family="${FONT}" font-size="22" font-weight="700" fill="${C.ink}">Kiki · guide moves</text><text x="${x0}" y="68" font-family="${FONT}" font-size="13" fill="${C.pencil}">Halo and filled number = step now · ghost number on a dashed path = steps ahead · tick = done · dots = where Kiki flew from</text>`;
  items.forEach(([key, label], i) => {
    const x = x0 + (i % cols) * (tw + gx), y = y0 + Math.floor(i / cols) * (th + gy);
    const inner = key === 'pointer' ? `<rect width="${W}" height="${H}" rx="16" fill="${C.raised}"/><svg x="80" y="30" width="160" height="160" viewBox="0 0 160 160">${fs.readFileSync(path.join(OUT, 'kiki-pointer.svg'), 'utf8').replace(/^[\s\S]*?<\/title>\n/, '').replace(/<\/svg>\s*$/, '')}</svg>` : scenes[key].inner;
    body += `<rect x="${x - 1}" y="${y - 1}" width="${tw + 2}" height="${th + 2}" rx="13" fill="none" stroke="${C.line}"/><svg x="${x}" y="${y}" width="${tw}" height="${th}" viewBox="0 0 ${W} ${H}">${inner}</svg><text x="${x + 4}" y="${y + th + 22}" font-family="${FONT}" font-size="13" font-weight="600" fill="${C.ink}">${label}</text>`;
  });
  write('kiki-sheet.svg', svgDoc(sw, sh, body, 'Kiki guide moves contact sheet'));
}

console.log(`Wrote ${written.length} files to ${path.relative(process.cwd(), OUT)}:\n  ${written.join('\n  ')}`);
