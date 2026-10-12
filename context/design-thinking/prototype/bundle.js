/* @ds-bundle: {"format":4,"namespace":"Breadboard","components":[{"name":"Button"},{"name":"Kiki"},{"name":"MasteryRing"},{"name":"LanguageDial"},{"name":"TermChip"},{"name":"MorphText"},{"name":"WordSticker"},{"name":"LessonProgress"},{"name":"DiodeExplorable"},{"name":"DiagnosisCard"},{"name":"VoiceScope"},{"name":"ReceiptCompare"},{"name":"MapNode"},{"name":"Snackbar"},{"name":"SourceTag"},{"name":"PredictionCanvas"},{"name":"LabStepper"},{"name":"Spotlight"},{"name":"FaultCard"},{"name":"AnswerOverlay"},{"name":"ClassPulseBar"},{"name":"KikiPointer"},{"name":"KikiWalkthrough"},{"name":"LabGuide"},{"name":"PracticeReport"}]} */
(function () {
  "use strict";
  var React = window.React;
  var h = React.createElement;
  var useState = React.useState, useEffect = React.useEffect, useRef = React.useRef, useCallback = React.useCallback;

  function cx() { return Array.prototype.filter.call(arguments, Boolean).join(" "); }
  function buzz(ms) { try { if (navigator.vibrate) navigator.vibrate(ms); } catch (e) {} }
  function prefersReduced() { try { return window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { return false; } }
  function icon(name, filled) { return h("span", { className: cx("bb-icon", filled && "bb-filled"), "aria-hidden": "true" }, name); }
  function omit(obj, keys) { var o = {}; Object.keys(obj).forEach(function (k) { if (keys.indexOf(k) < 0) o[k] = obj[k]; }); return o; }
  function useOutsideClose(open, setOpen) {
    var ref = useRef(null);
    useEffect(function () {
      if (!open) return undefined;
      function onDown(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false); }
      function onKey(e) { if (e.key === "Escape") setOpen(false); }
      document.addEventListener("pointerdown", onDown);
      document.addEventListener("keydown", onKey);
      return function () { document.removeEventListener("pointerdown", onDown); document.removeEventListener("keydown", onKey); };
    }, [open]);
    return ref;
  }
  function speak(text, lang) {
    try {
      if (!window.speechSynthesis) return;
      var u = new SpeechSynthesisUtterance(text);
      u.lang = lang || "en-IN"; u.rate = 0.9;
      window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
    } catch (e) {}
  }

  /* The four mastery dimensions, in ring order. */
  var DIMS = [
    { key: "concept", name: "Concept", fill: "var(--blue, #4285f4)", ink: "var(--blue-ink, #1967d2)" },
    { key: "words", name: "Words", fill: "var(--red, #ea4335)", ink: "var(--red-ink, #c5221f)" },
    { key: "english", name: "English", fill: "var(--yellow, #fbbc05)", ink: "var(--yellow-ink, #9a5500)" },
    { key: "lab", name: "Lab", fill: "var(--green, #34a853)", ink: "var(--green-ink, #137333)" }
  ];

  /* Sample content: the worked example used across previews. Odia copy needs native-speaker review. */
  var GLOSSARY = {
    "diode": { odia: "ଗୋଟିଏ ଦିଗରେ current ଯିବାକୁ ଦେଉଥିବା ଏକ ଉପାଦାନ", example: "Every phone charger has diodes inside it." },
    "current": { odia: "ବିଦ୍ୟୁତ୍ ପ୍ରବାହ", example: "Current is measured in amperes (A)." },
    "forward bias": { odia: "ଯେତେବେଳେ p-side କୁ positive voltage ଦିଆଯାଏ", example: "In forward bias, the diode conducts." },
    "reverse bias": { odia: "ଯେତେବେଳେ n-side କୁ positive voltage ଦିଆଯାଏ", example: "In reverse bias, the diode blocks current." },
    "cut-in voltage": { odia: "ଯେଉଁ voltage ପରେ diode ରେ current ବହିବା ଆରମ୍ଭ ହୁଏ", example: "For a silicon diode the cut-in voltage is about 0.7 V." },
    "conducts": { odia: "current ଯିବାକୁ ଦିଏ", example: "The diode conducts when it is forward biased." }
  };
  function T(term) { return { term: term }; }
  var DIODE_LEVELS = [
    [T("diode"), " କେବଳ ଗୋଟିଏ ଦିଗରେ ", T("current"), " ଯିବାକୁ ଦିଏ। ", T("forward bias"), "ରେ, ପ୍ରାୟ 0.7 V ର ", T("cut-in voltage"), " ପରେ ଏହା ", T("current"), " ପ୍ରବାହିତ କରେ। ", T("reverse bias"), "ରେ ଏହା ", T("current"), "କୁ ଅଟକାଇ ଦିଏ।"],
    [T("diode"), " କେବଳ one direction ରେ ", T("current"), " ଯିବାକୁ ଦିଏ। ", T("forward bias"), "ରେ, ପ୍ରାୟ 0.7 V ର ", T("cut-in voltage"), " ପରେ ଏହା ", T("conducts"), "। ", T("reverse bias"), "ରେ ଏହା block କରେ।"],
    [T("diode"), " ", T("current"), " କୁ only one direction ରେ ଯିବାକୁ ଦିଏ। ", T("forward bias"), " ରେ, about 0.7 V ", T("cut-in voltage"), " ପରେ ଏହା ", T("conducts"), "। ", T("reverse bias"), " ରେ ଏହା ", T("current"), " କୁ block କରେ।"],
    ["A ", T("diode"), " lets ", T("current"), " flow in only one direction. In ", T("forward bias"), ", it ", T("conducts"), " once the voltage crosses the ", T("cut-in voltage"), " of about 0.7 V. ", T("reverse bias"), " ରେ ଏହା ", T("current"), "କୁ ଅଟକାଇ ଦିଏ।"],
    ["A ", T("diode"), " lets ", T("current"), " flow in only one direction. In ", T("forward bias"), ", it ", T("conducts"), " once the voltage crosses the ", T("cut-in voltage"), " of about 0.7 V. In ", T("reverse bias"), ", it blocks the ", T("current"), "."]
  ];
  var LEVEL_NAMES = ["Odia, with English terms", "Mostly Odia", "Half and half", "Mostly English", "English, Odia on tap"];

  /* Split a string into runs of Odia script and everything else, so Odia gets its own size and line height. */
  var ODIA_RUN = /([଀-୿][଀-୿\s।॥]*)/;
  function withOdia(text, key) {
    var parts = String(text).split(ODIA_RUN);
    return parts.map(function (p, i) {
      if (!p) return null;
      return /[଀-୿]/.test(p) ? h("span", { key: key + "-" + i, className: "bb-or", lang: "or" }, p) : p;
    });
  }

  /* ---------- Button ---------- */
  function Button(props) {
    var variant = props.variant || "filled";
    var rest = omit(props, ["variant", "className", "icon", "children"]);
    return h("button", Object.assign({ type: "button" }, rest, { className: cx("bb-btn", "bb-btn-" + variant, props.className) }),
      props.icon ? icon(props.icon, variant === "filled") : null, props.children);
  }

  /* ---------- Kiki ---------- */
  var KIKI_POS = {
    idle: [[24, 24], [40, 24], [24, 40], [40, 40]],
    listening: [[14, 32], [26, 32], [38, 32], [50, 32]],
    thinking: [[14, 34], [26, 34], [38, 34], [50, 34]],
    speaking: [[24, 24], [40, 24], [24, 40], [40, 40]],
    pointing: [[10, 32], [23, 32], [36, 32], [51, 32]],
    asking: [[22, 15], [37, 13], [42, 27], [32, 52]],
    celebrating: [[9, 9], [55, 9], [9, 55], [55, 55]],
    unsure: [[15, 21], [47, 13], [21, 49], [50, 44]],
    examiner: [[14, 32], [26, 32], [38, 32], [50, 32]]
  };
  var KIKI_COLORS = ["var(--blue, #4285f4)", "var(--red, #ea4335)", "var(--yellow, #fbbc05)", "var(--green, #34a853)"];
  var KIKI_LABELS = { idle: "Kiki", listening: "Kiki is listening", thinking: "Kiki is thinking", speaking: "Kiki is speaking", pointing: "Kiki is pointing", asking: "Kiki is asking a question", celebrating: "Kiki is celebrating", unsure: "Kiki is not sure", examiner: "Kiki in examiner mode" };
  function Kiki(props) {
    var state = KIKI_POS[props.state] ? props.state : "idle";
    var size = props.size || 64;
    var lead = props.lead; /* "concept" | "words" | "english" | "lab": that dot leads */
    var leadIndex = DIMS.map(function (d) { return d.key; }).indexOf(lead);
    var pos = KIKI_POS[state];
    var rot = state === "pointing" && props.direction ? props.direction : 0;
    return h("svg", { className: cx("bb-kiki", "bb-kiki-" + state, props.className), width: size, height: size, viewBox: "0 0 64 64", role: "img", "aria-label": props.label || KIKI_LABELS[state] },
      h("g", { style: { transform: "rotate(" + rot + "deg)", transformOrigin: "32px 32px", transition: "transform 300ms ease" } },
        pos.map(function (p, i) {
          var r = state === "examiner" ? 5 : (i === leadIndex ? 8.5 : 7);
          var w = state === "examiner" ? 10 : r * 2;
          return h("g", { key: i, className: "bb-kiki-dot-g", style: { transform: "translate(" + p[0] + "px," + p[1] + "px)" } },
            h("rect", { className: "bb-kiki-dot", x: -w / 2, y: -r, width: w, height: r * 2, rx: state === "examiner" ? 2 : r, fill: KIKI_COLORS[i], style: { animationDelay: (i * 0.12) + "s" } }));
        })));
  }

  /* ---------- MasteryRing ---------- */
  function MasteryRing(props) {
    var size = props.size || 96;
    var stroke = props.stroke || Math.max(4, Math.round(size * 0.1));
    var r = (size - stroke) / 2, c = size / 2, circ = 2 * Math.PI * r;
    var gapFrac = size < 48 ? 0.05 : 0.03;
    var seg = 0.25 - gapFrac;
    var values = props.values || {};
    var locked = props.locked || [];
    var complete = DIMS.every(function (d) { return (values[d.key] || 0) >= 1; });
    var summary = DIMS.map(function (d) { return d.name + " " + Math.round(Math.min(1, values[d.key] || 0) * 100) + "%" + (locked.indexOf(d.key) >= 0 ? " (locked)" : ""); }).join(", ");
    return h("div", { className: cx("bb-ring", props.flicker && "bb-ring-flicker", complete && "bb-ring-complete", props.className), style: { width: size, height: size }, role: "img", "aria-label": (props.label ? props.label + ": " : "") + summary },
      h("svg", { width: size, height: size, viewBox: "0 0 " + size + " " + size },
        DIMS.map(function (d, i) {
          var start = (i * 0.25 + gapFrac / 2) * circ;
          var isLocked = locked.indexOf(d.key) >= 0;
          var v = Math.max(0, Math.min(1, values[d.key] || 0));
          var segLen = seg * circ;
          var lockedDash = null;
          if (isLocked) {
            var dash = Math.max(2, stroke * 0.5), space = Math.max(3, stroke * 0.6), parts = [], used = 0;
            while (used + dash <= segLen) { parts.push(dash, space); used += dash + space; }
            parts[parts.length - 1] = circ; lockedDash = parts.join(" ");
          }
          return h("g", { key: d.key },
            isLocked
              ? h("circle", { className: "bb-ring-locked", cx: c, cy: c, r: r, strokeWidth: Math.max(2, stroke * 0.45), strokeDasharray: lockedDash, strokeDashoffset: -start })
              : h("circle", { className: "bb-ring-track", cx: c, cy: c, r: r, strokeWidth: stroke, strokeLinecap: "round", strokeDasharray: segLen + " " + circ, strokeDashoffset: -start }),
            !isLocked && v > 0 ?h("circle", { className: "bb-ring-fill", cx: c, cy: c, r: r, stroke: d.fill, strokeWidth: stroke, strokeLinecap: "round", strokeDasharray: (v * seg * circ) + " " + circ, strokeDashoffset: -start }) : null);
        })),
      props.children ? h("div", { className: "bb-ring-center" }, props.children) : null);
  }

  /* ---------- LanguageDial ---------- */
  function LanguageDial(props) {
    var controlled = typeof props.value === "number";
    var st = useState(props.defaultValue || 1); var inner = st[0], setInner = st[1];
    var value = controlled ? props.value : inner;
    var trackRef = useRef(null);
    var dragging = useRef(false);
    var notches = 5;
    function pct(v) { return (v - 1) / (notches - 1); }
    function setValue(v) {
      v = Math.max(1, Math.min(notches, v));
      if (v === value) return;
      buzz(10);
      if (!controlled) setInner(v);
      if (props.onChange) props.onChange(v);
    }
    function fromPointer(e) {
      var el = trackRef.current; if (!el) return;
      var rect = el.getBoundingClientRect();
      var x = e.clientX - rect.left - 18, w = rect.width - 36;
      setValue(Math.round(Math.max(0, Math.min(1, x / w)) * (notches - 1)) + 1);
    }
    function leftFor(v) { return "calc(18px + (100% - 36px) * " + pct(v) + ")"; }
    var suggested = props.suggested && props.suggested !== value ? props.suggested : null;
    return h("div", { className: cx("bb-dial", props.className) },
      h("div", { className: "bb-dial-ends" }, h("span", { className: "bb-or", lang: "or" }, "ଓଡ଼ିଆ"), h("span", null, "English")),
      h("div", {
        className: "bb-dial-track", ref: trackRef,
        onPointerDown: function (e) { dragging.current = true; try { e.currentTarget.setPointerCapture(e.pointerId); } catch (err) {} fromPointer(e); },
        onPointerMove: function (e) { if (dragging.current) fromPointer(e); },
        onPointerUp: function () { dragging.current = false; },
        onPointerCancel: function () { dragging.current = false; }
      },
        h("div", { className: "bb-dial-rail" }),
        [1, 2, 3, 4, 5].map(function (n) { return h("div", { key: n, className: "bb-dial-notch", style: { left: leftFor(n) } }); }),
        suggested ? h("div", { className: "bb-dial-ghost", style: { left: leftFor(suggested) }, "aria-hidden": "true" }) : null,
        h("div", {
          className: "bb-dial-knob", role: "slider", tabIndex: 0, "aria-label": "Language mix", "aria-valuemin": 1, "aria-valuemax": 5, "aria-valuenow": value, "aria-valuetext": LEVEL_NAMES[value - 1],
          style: { left: leftFor(value), "--bb-knob-angle": (-120 + pct(value) * 240) + "deg" },
          onKeyDown: function (e) {
            if (e.key === "ArrowRight" || e.key === "ArrowUp") { e.preventDefault(); setValue(value + 1); }
            if (e.key === "ArrowLeft" || e.key === "ArrowDown") { e.preventDefault(); setValue(value - 1); }
            if (e.key === "Home") { e.preventDefault(); setValue(1); }
            if (e.key === "End") { e.preventDefault(); setValue(5); }
          }
        })),
      h("div", { className: "bb-dial-caption" },
        h("span", null, h("b", null, value + " of 5 · "), LEVEL_NAMES[value - 1]),
        suggested ? h("button", { type: "button", className: "bb-dial-try", onClick: function () { setValue(suggested); if (props.onAcceptSuggestion) props.onAcceptSuggestion(suggested); } },
          icon("arrow_forward"), suggested > value ? "Try one notch more English?" : "Make this one easier?") : null));
  }

  /* ---------- TermChip ---------- */
  function TermChip(props) {
    var st = useState(false); var open = st[0], setOpen = st[1];
    var ref = useOutsideClose(open, setOpen);
    var entry = props.entry || GLOSSARY[props.term] || {};
    var state = props.state || "new";
    return h("span", { className: "bb-term-wrap", ref: ref },
      h("button", { type: "button", className: cx("bb-term", "bb-term-" + state, props.pulse && "bb-term-pulse"), "aria-expanded": open,
        onClick: function () { setOpen(!open); if (!open && props.onOpen) props.onOpen(props.term); } }, props.term),
      open ? h("span", { className: "bb-sheet", role: "dialog", "aria-label": props.term },
        h("span", { className: "bb-sheet-term" }, props.term),
        entry.odia ? h("span", null, withOdia(entry.odia, "o")) : null,
        h("span", { className: "bb-sheet-row" },
          h(Button, { variant: "tonal", icon: "volume_up", onClick: function () { speak(props.term, "en-IN"); } }, "Hear it"),
          h("span", { className: "bb-label", style: { color: "var(--red-ink, #c5221f)" } }, state === "owned" ? "Owned" : state === "collected" ? "In your deck" : "New word")),
        entry.example ? h("span", { className: "bb-sheet-example" }, entry.example) : null) : null);
  }

  /* ---------- MorphText ---------- */
  function MorphText(props) {
    var levels = props.levels || DIODE_LEVELS;
    var level = Math.max(1, Math.min(levels.length, props.level || 1));
    var glossary = props.glossary || GLOSSARY;
    var states = props.termStates || {};
    var segs = levels[level - 1];
    return h(React.Fragment, null, h("p", { key: "level-" + level, className: cx("bb-morph", !prefersReduced() && "bb-morph-anim", props.className), lang: level <= 3 ? "or" : "en" },
      segs.map(function (s, i) {
        if (typeof s === "string") return h(React.Fragment, { key: i }, withOdia(s, i));
        return h(TermChip, { key: i + "-" + s.term, term: s.term, entry: glossary[s.term], state: states[s.term], pulse: true, onOpen: props.onTermOpen });
      })));
  }

  /* ---------- WordSticker ---------- */
  function WordSticker(props) {
    var st = useState(false); var flipped = st[0], setFlipped = st[1];
    var entry = props.entry || GLOSSARY[props.term] || {};
    var state = props.state || "collected";
    var stateWord = state === "new" ? "NEW" : state === "owned" ? "OWNED" : "COLLECTED";
    return h("button", { type: "button", className: cx("bb-sticker", "bb-sticker-" + state, flipped && "bb-sticker-flipped", props.className),
      "aria-label": props.term + ", " + stateWord.toLowerCase() + ". Tap to flip.", onClick: function () { setFlipped(!flipped); } },
      h("span", { className: "bb-sticker-inner" },
        h("span", { className: "bb-sticker-face bb-sticker-front" },
          h("span", { className: "bb-sticker-state", style: { color: state === "owned" ? "#ffffff" : "var(--red-ink, #c5221f)" } }, stateWord),
          h("span", { className: "bb-sticker-term" }, props.term),
          h("span", { style: { fontSize: 13, opacity: 0.8 } }, icon("touch_app"), " Flip for meaning")),
        h("span", { className: "bb-sticker-face bb-sticker-back" },
          h("span", { style: { fontSize: 15 } }, withOdia(entry.odia || "", "b")),
          h("span", { style: { fontSize: 13, color: "var(--pencil, #5f6368)" } }, entry.example || ""))));
  }

  /* ---------- LessonProgress ---------- */
  function LessonProgress(props) {
    var values = props.values || {};
    return h("div", { className: cx("bb-progress", props.className), role: "group", "aria-label": "Lesson progress" },
      DIMS.map(function (d) {
        var v = Math.max(0, Math.min(1, values[d.key] || 0));
        return h("div", { key: d.key, className: "bb-progress-seg", role: "progressbar", "aria-label": d.name, "aria-valuemin": 0, "aria-valuemax": 100, "aria-valuenow": Math.round(v * 100) },
          h("div", { className: "bb-progress-fill", style: { width: (v * 100) + "%", background: d.fill } }));
      }));
  }

  /* ---------- DiodeExplorable ---------- */
  function diodeCurrent(v) { if (v <= 0) return 0; return 1e-6 * (Math.exp(v / 0.045) - 1); } /* mA */
  function DiodeExplorable(props) {
    var st = useState(typeof props.defaultVoltage === "number" ? props.defaultVoltage : 0.3); var v = st[0], setV = st[1];
    var i = diodeCurrent(v);
    var W = 300, H = 180, vmin = -2, vmax = 1, imax = 20;
    function X(x) { return 34 + (x - vmin) / (vmax - vmin) * (W - 46); }
    function Y(y) { return H - 26 - Math.min(y, imax) / imax * (H - 40); }
    var pts = [];
    for (var k = 0; k <= 120; k++) { var vx = vmin + (vmax - vmin) * k / 120; pts.push(X(vx).toFixed(1) + "," + Y(diodeCurrent(vx)).toFixed(1)); }
    var speed = i > 0.05 ? Math.max(0.35, 3.2 / Math.sqrt(i)) : 0;
    var note = v < 0 ? "Reverse bias: the diode blocks current." : v < 0.6 ? "Forward bias, but below the cut-in voltage: almost no current." : "Past the cut-in voltage: current rises fast. See the knee near 0.7 V.";
    var kstate = v >= 0.6 && v <= 0.8 ? "pointing" : "idle";
    return h("div", { className: cx("bb-explore", props.className) },
      h("div", { className: "bb-explore-figs" },
        h("svg", { viewBox: "0 0 160 150", role: "img", "aria-label": "Circuit: battery, resistor and diode in a loop" },
          h("rect", { x: 20, y: 20, width: 120, height: 100, rx: 10, fill: "none", stroke: "var(--pencil, #5f6368)", strokeWidth: 2.5 }),
          speed ? h("rect", { className: "bb-current", x: 20, y: 20, width: 120, height: 100, rx: 10, fill: "none", stroke: "var(--blue, #4285f4)", strokeWidth: 4, style: { animationDuration: speed + "s" } }) : null,
          h("rect", { x: 8, y: 54, width: 24, height: 32, fill: "var(--paper-raised, #ffffff)" }),
          h("line", { x1: 10, y1: 62, x2: 30, y2: 62, stroke: "var(--ink, #1f1f1f)", strokeWidth: 3 }),
          h("line", { x1: 14, y1: 72, x2: 26, y2: 72, stroke: "var(--ink, #1f1f1f)", strokeWidth: 3 }),
          h("text", { x: 36, y: 66, fontSize: 11, fill: "var(--pencil, #5f6368)", fontFamily: "Roboto Mono, monospace" }, v.toFixed(2) + "V"),
          h("rect", { x: 62, y: 12, width: 36, height: 16, rx: 3, fill: "var(--paper-raised, #ffffff)", stroke: "var(--ink, #1f1f1f)", strokeWidth: 2 }),
          h("text", { x: 80, y: 44, fontSize: 10, fill: "var(--pencil, #5f6368)", textAnchor: "middle" }, "R"),
          h("g", { transform: "translate(140,70)" },
            h("rect", { x: -12, y: -14, width: 24, height: 28, fill: "var(--paper-raised, #ffffff)" }),
            h("polygon", { points: "-9,-10 9,-10 0,6", fill: i > 0.05 ? "var(--blue, #4285f4)" : "var(--paper-raised, #ffffff)", stroke: "var(--ink, #1f1f1f)", strokeWidth: 2 }),
            h("line", { x1: -10, y1: 7, x2: 10, y2: 7, stroke: "var(--ink, #1f1f1f)", strokeWidth: 2.5 })),
          h("text", { x: 128, y: 104, fontSize: 10, fill: "var(--pencil, #5f6368)", textAnchor: "end" }, "diode")),
        h("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "V-I curve of a silicon diode" },
          h("line", { x1: X(vmin), y1: Y(0), x2: X(vmax), y2: Y(0), stroke: "var(--line, #d9d6cf)", strokeWidth: 1.5 }),
          h("line", { x1: X(0), y1: 10, x2: X(0), y2: H - 22, stroke: "var(--line, #d9d6cf)", strokeWidth: 1.5 }),
          h("line", { x1: X(0.7), y1: 10, x2: X(0.7), y2: H - 22, stroke: "var(--blue-ink, #1967d2)", strokeWidth: 1, strokeDasharray: "3 4", opacity: 0.6 }),
          h("text", { x: X(0.7), y: H - 8, fontSize: 10, fill: "var(--blue-ink, #1967d2)", textAnchor: "middle", fontFamily: "Roboto Mono, monospace" }, "0.7 V"),
          h("text", { x: X(vmin), y: H - 8, fontSize: 10, fill: "var(--pencil, #5f6368)", fontFamily: "Roboto Mono, monospace" }, "-2 V"),
          h("text", { x: X(0) + 4, y: 16, fontSize: 10, fill: "var(--pencil, #5f6368)", fontFamily: "Roboto Mono, monospace" }, "I (mA)"),
          h("polyline", { points: pts.join(" "), fill: "none", stroke: "var(--ink, #1f1f1f)", strokeWidth: 2 }),
          h("circle", { cx: X(v), cy: Y(i), r: 6, fill: "var(--blue, #4285f4)", stroke: "var(--paper-raised, #ffffff)", strokeWidth: 2 }))),
      h("label", { className: "bb-label", htmlFor: props.id || "bb-diode-v" }, "Voltage across the diode"),
      h("input", { id: props.id || "bb-diode-v", type: "range", min: -2, max: 1, step: 0.01, value: v, onChange: function (e) { setV(parseFloat(e.target.value)); } }),
      h("div", { className: "bb-explore-read bb-mono" }, h("span", null, "V = " + v.toFixed(2) + " V"), h("span", null, "I = " + (i < 0.01 ? "0.00" : Math.min(i, 99).toFixed(2)) + " mA")),
      h("div", { className: "bb-explore-kiki", "aria-live": "polite" }, h(Kiki, { state: kstate, size: 36, lead: "concept", direction: 0 }), h("span", null, note)));
  }

  /* ---------- DiagnosisCard ---------- */
  var DIAG = {
    solid: { title: "Both solid.", msg: "Concept and English are both there. On to the next step.", c: true, e: true, action: "Continue" },
    language: { title: "You understand this.", msg: "You just need the English words. Let's practise them, then try an easier English version.", c: true, e: false, action: "Practise the words" },
    concept: { title: "Let's go one step back.", msg: "Forward and reverse bias first, then this question again.", c: false, e: false, action: "Rerouting…" }
  };
  function DiagnosisCard(props) {
    var d = DIAG[props.variant] || DIAG.solid;
    return h("div", { className: cx("bb-diag", props.className), role: "status" },
      h("div", { className: "bb-diag-pills" },
        h("span", { className: cx("bb-pill", d.c ? "bb-pill-concept-yes" : "bb-pill-notyet") }, icon(d.c ? "check_circle" : "hourglass_empty", d.c), "Concept: ", d.c ? "yes" : "not yet"),
        h("span", { className: cx("bb-pill", d.e ? "bb-pill-english-yes" : "bb-pill-notyet") }, icon(d.e ? "check_circle" : "hourglass_empty", d.e), "English: ", d.e ? "yes" : "not yet")),
      h("div", { className: "bb-diag-title" }, props.title || d.title),
      h("div", { className: "bb-diag-msg" }, props.message || d.msg),
      h("div", null, h(Button, { variant: props.variant === "concept" ? "tonal" : "filled", icon: props.variant === "concept" ? "alt_route" : props.variant === "language" ? "style" : "arrow_forward", onClick: props.onAction }, props.actionLabel || d.action)));
  }

  /* ---------- VoiceScope ---------- */
  function VoiceScope(props) {
    var st = useState(props.defaultState || "ready"); var mode = st[0], setMode = st[1];
    var canvasRef = useRef(null), samples = useRef([]), raf = useRef(0), t0 = useRef(0);
    var draw = useCallback(function (playhead) {
      var cv = canvasRef.current; if (!cv) return;
      var dpr = window.devicePixelRatio || 1, w = cv.clientWidth, hgt = cv.clientHeight;
      if (cv.width !== w * dpr) { cv.width = w * dpr; cv.height = hgt * dpr; }
      var g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, hgt);
      var css = getComputedStyle(cv);
      g.strokeStyle = css.getPropertyValue("--scope-grid").trim() || "#23303a"; g.lineWidth = 1;
      for (var gx = 0; gx < w; gx += w / 10) { g.beginPath(); g.moveTo(gx, 0); g.lineTo(gx, hgt); g.stroke(); }
      for (var gy = 0; gy < hgt; gy += hgt / 4) { g.beginPath(); g.moveTo(0, gy); g.lineTo(w, gy); g.stroke(); }
      var s = samples.current, n = s.length; if (!n) return;
      g.strokeStyle = css.getPropertyValue("--yellow").trim() || "#fbbc05"; g.lineWidth = 2; g.beginPath();
      for (var k = 0; k < n; k++) { var x = k / Math.max(1, n - 1) * w, y = hgt / 2 - s[k] * hgt * 0.42; if (k) g.lineTo(x, y); else g.moveTo(x, y); }
      g.stroke();
      if (typeof playhead === "number") { g.strokeStyle = "#ffffff"; g.lineWidth = 1.5; g.beginPath(); g.moveTo(playhead * w, 0); g.lineTo(playhead * w, hgt); g.stroke(); }
    }, []);
    useEffect(function () {
      cancelAnimationFrame(raf.current);
      if (mode === "recording") {
        samples.current = []; t0.current = performance.now();
        var tick = function () {
          var t = (performance.now() - t0.current) / 1000;
          var env = 0.35 + 0.65 * Math.abs(Math.sin(t * 2.3)) * (0.6 + 0.4 * Math.sin(t * 7.1));
          for (var q = 0; q < 3; q++) samples.current.push((Math.random() * 2 - 1) * env);
          if (samples.current.length > 900) samples.current = samples.current.slice(-900);
          draw(); raf.current = requestAnimationFrame(tick);
        };
        tick();
      } else if (mode === "playback") {
        var start = performance.now(), dur = 2600;
        var play = function () { var p = Math.min(1, (performance.now() - start) / dur); draw(p); if (p < 1) raf.current = requestAnimationFrame(play); else setMode("feedback"); };
        play();
      } else {
        if (!samples.current.length) { for (var z = 0; z < 600; z++) samples.current.push(Math.sin(z / 9) * 0.25 * Math.abs(Math.sin(z / 70))); }
        draw();
      }
      return function () { cancelAnimationFrame(raf.current); };
    }, [mode, draw]);
    var label = mode === "recording" ? "Release to stop" : mode === "ready" ? "Hold to speak" : "Hold to try again";
    return h("div", { className: cx("bb-scope", props.className) },
      h("div", { className: "bb-scope-screen" }, h("canvas", { ref: canvasRef, "aria-hidden": "true" }),
        h("span", { className: "bb-scope-tag" }, mode === "recording" ? "● REC" : mode === "playback" ? "PLAYBACK" : "VOICE")),
      h("div", { className: "bb-scope-row" },
        h("button", { type: "button", className: cx("bb-mic", mode === "recording" && "bb-mic-rec"), "aria-label": label,
          onPointerDown: function () { setMode("recording"); },
          onPointerUp: function () { setMode("playback"); },
          onPointerLeave: function () { if (mode === "recording") setMode("playback"); },
          onKeyDown: function (e) { if ((e.key === " " || e.key === "Enter") && mode !== "recording") { e.preventDefault(); setMode("recording"); } },
          onKeyUp: function (e) { if (e.key === " " || e.key === "Enter") { e.preventDefault(); setMode("playback"); } } }, icon("mic", true)),
        h("div", { style: { display: "grid", gap: 4 } },
          h("span", { className: "bb-label" }, label),
          h("span", { style: { fontSize: 14, color: "var(--pencil, #5f6368)" } }, props.prompt || "A diode conducts when…"))),
      mode === "feedback" || mode === "playback" ? h("div", { className: "bb-scope-transcript" }, props.transcript || h(React.Fragment, null, "A diode passes current when it is in ", h(TermChip, { term: "forward bias", state: "collected" }), " and the voltage is more than 0.7 V.")) : null,
      mode === "feedback" ? h("div", { className: "bb-scope-fix" }, icon("lightbulb"), " ", props.feedback || "You used forward bias correctly. Try “conducts” instead of “passes”.") : null);
  }

  /* ---------- ReceiptCompare ---------- */
  function ReceiptCompare(props) {
    var before = props.before || { time: "10 MINUTES AGO", answer: "I don't know yet." };
    var after = props.after || { time: "NOW", answer: "In reverse bias the depletion region widens, so the diode blocks current.", verdict: "Correct, in English" };
    return h("div", { className: cx("bb-receipt", props.className) },
      h("div", { className: "bb-receipt-card" }, h("span", { className: "bb-receipt-time" }, before.time), h("span", { className: "bb-receipt-answer" }, before.answer)),
      h("div", { className: "bb-receipt-card bb-receipt-now" }, h("span", { className: "bb-receipt-time" }, after.time), h("span", { className: "bb-receipt-answer" }, after.answer),
        after.verdict ? h("span", { className: "bb-receipt-verdict" }, icon("check_circle", true), " ", after.verdict) : null));
  }

  /* ---------- MapNode ---------- */
  function MapNode(props) {
    var state = props.state || "available";
    var values = props.values || (state === "mastered" || state === "flicker" ? { concept: 1, words: 1, english: 1, lab: 1 } : {});
    return h("div", { className: cx("bb-node", "bb-node-" + state, props.className) },
      h("div", { className: "bb-node-body", role: "button", tabIndex: state === "locked" ? -1 : 0, "aria-label": props.label + ", " + state, onClick: props.onClick },
        props.here ? h("span", { className: "bb-node-pin" }, h(Kiki, { state: "idle", size: 26, label: "You are here" })) : null,
        h("span", { className: "bb-node-led", "aria-hidden": "true" }),
        state === "locked" ? icon("lock") : h(MasteryRing, { size: 44, values: values, flicker: state === "flicker" }),
        props.heat ? h("span", { className: "bb-node-heat", title: "Asked in " + props.heat + " past papers" }, props.heat) : null),
      h("span", { className: "bb-node-label" }, props.label),
      props.odia ? h("span", { className: "bb-or", lang: "or", style: { fontSize: 12, color: "var(--pencil, #5f6368)" } }, props.odia) : null);
  }

  /* ---------- Snackbar ---------- */
  function Snackbar(props) {
    return h("div", { className: cx("bb-snack", props.className), role: "status", "aria-live": "polite" },
      props.tone === "route" ? h("span", { className: "bb-route-line", "aria-hidden": "true" }) : props.icon ? icon(props.icon) : null,
      h("span", null, props.message),
      props.actionLabel ? h("button", { type: "button", className: "bb-snack-action", onClick: props.onAction }, props.actionLabel) : null);
  }

  /* ---------- SourceTag ---------- */
  function SourceTag(props) {
    var st = useState(false); var open = st[0], setOpen = st[1];
    var ref = useOutsideClose(open, setOpen);
    return h("span", { className: "bb-term-wrap", ref: ref },
      h("button", { type: "button", className: "bb-source", "aria-expanded": open, onClick: function () { setOpen(!open); } }, icon("description"), props.label || "From your notes, page 7"),
      open ? h("span", { className: "bb-sheet", role: "dialog", "aria-label": "Source" },
        h("span", { className: "bb-label", style: { color: "var(--pencil, #5f6368)" } }, props.source || "Prof. notes · Unit 2.pdf"),
        h("span", { className: "bb-source-snippet" }, props.snippet || "Si diode: cut-in voltage Vγ = 0.6 V (use this value in exam)"),
        props.conflict ? h("span", { style: { fontSize: 13 } }, icon("info"), " ", props.conflict) : null) : null);
  }

  /* ---------- PredictionCanvas ---------- */
  var EXPECTED = {
    halfwave: function (x) { var s = Math.sin(x * Math.PI * 4); return s > 0 ? s : 0; },
    fullwave: function (x) { return Math.abs(Math.sin(x * Math.PI * 4)); },
    sine: function (x) { return Math.sin(x * Math.PI * 4); }
  };
  function PredictionCanvas(props) {
    var expected = typeof props.expected === "function" ? props.expected : EXPECTED[props.expected || "halfwave"];
    var cvRef = useRef(null), pts = useRef([]), drawing = useRef(false);
    var st = useState("drawing"); var phase = st[0], setPhase = st[1];
    var ms = useState(""); var msg = ms[0], setMsg = ms[1];
    var render = useCallback(function (reveal) {
      var cv = cvRef.current; if (!cv) return;
      var dpr = window.devicePixelRatio || 1, w = cv.clientWidth, hgt = cv.clientHeight;
      if (cv.width !== w * dpr) { cv.width = w * dpr; cv.height = hgt * dpr; }
      var g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, hgt);
      var css = getComputedStyle(cv);
      var grid = css.getPropertyValue("--scope-grid").trim() || "#23303a";
      g.strokeStyle = grid; g.lineWidth = 1;
      for (var gx = 0; gx <= w; gx += w / 10) { g.beginPath(); g.moveTo(gx, 0); g.lineTo(gx, hgt); g.stroke(); }
      for (var gy = 0; gy <= hgt; gy += hgt / 6) { g.beginPath(); g.moveTo(0, gy); g.lineTo(w, gy); g.stroke(); }
      function curve(fn, color, width, dash) {
        g.setLineDash(dash || []); g.strokeStyle = color; g.lineWidth = width; g.beginPath();
        for (var k = 0; k <= 200; k++) { var x = k / 200, y = hgt / 2 - fn(x) * hgt * 0.36; if (k) g.lineTo(x * w, y); else g.moveTo(x * w, y); }
        g.stroke(); g.setLineDash([]);
      }
      curve(EXPECTED.sine, "rgba(201,214,223,0.45)", 1.5, [5, 5]);
      var p = pts.current;
      if (p.length > 1) { g.strokeStyle = css.getPropertyValue("--blue").trim() || "#4285f4"; g.lineWidth = 3; g.lineCap = "round"; g.lineJoin = "round"; g.beginPath(); p.forEach(function (q, i) { if (i) g.lineTo(q[0] * w, q[1] * hgt); else g.moveTo(q[0] * w, q[1] * hgt); }); g.stroke(); }
      if (reveal) curve(expected, css.getPropertyValue("--scope-trace").trim() || "#5be38a", 2.5);
    }, [expected]);
    useEffect(function () { render(phase === "revealed"); var onR = function () { render(phase === "revealed"); }; window.addEventListener("resize", onR); return function () { window.removeEventListener("resize", onR); }; }, [phase, render]);
    function pos(e) { var r = cvRef.current.getBoundingClientRect(); return [Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)), Math.max(0, Math.min(1, (e.clientY - r.top) / r.height))]; }
    function score() {
      var p = pts.current.slice().sort(function (a, b) { return a[0] - b[0]; }); if (p.length < 8) return 0;
      var err = 0, n = 0;
      for (var k = 1; k < 40; k++) {
        var x = k / 40, near = null, best = 1;
        p.forEach(function (q) { var d = Math.abs(q[0] - x); if (d < best) { best = d; near = q; } });
        if (near && best < 0.05) { var drawn = (0.5 - near[1]) / 0.36; err += Math.abs(drawn - expected(x)); n++; }
      }
      if (n < 15) return 0;
      return Math.max(0, 1 - err / n / 0.9);
    }
    function run() {
      var s = score(); setPhase("revealed");
      var m = s > 0.78 ? "Spot on! That is the rectified output." : s > 0.45 ? "Close! Look again at the negative half: the diode blocks it, so it stays flat." : pts.current.length < 8 ? "Draw your guess first, then run." : "Not quite. What happens to the wave below zero?";
      setMsg(m); if (props.onResult) props.onResult(s);
    }
    function reset() { pts.current = []; setPhase("drawing"); setMsg(""); render(false); }
    return h("div", { className: cx("bb-predict", props.className) },
      h("div", { className: "bb-predict-screen",
        onPointerDown: function (e) { if (phase !== "drawing") return; drawing.current = true; try { e.currentTarget.setPointerCapture(e.pointerId); } catch (err) {} pts.current = [pos(e)]; render(false); },
        onPointerMove: function (e) { if (!drawing.current) return; pts.current.push(pos(e)); render(false); },
        onPointerUp: function () { drawing.current = false; } },
        h("canvas", { ref: cvRef, role: "img", "aria-label": "Drawing area: sketch the output waveform you expect" })),
      h("div", { className: "bb-predict-legend" },
        h("span", null, h("span", { className: "bb-swatch", style: { background: "#c9d6df" } }), "Input (AC sine)"),
        h("span", null, h("span", { className: "bb-swatch", style: { background: "var(--blue, #4285f4)" } }), "Your prediction"),
        h("span", null, h("span", { className: "bb-swatch", style: { background: "var(--scope-trace, #5be38a)" } }), "Real output")),
      h("div", { className: "bb-predict-msg", "aria-live": "polite" }, msg || (phase === "drawing" ? "Draw what you expect the output to look like." : "")),
      h("div", { style: { display: "flex", gap: 8, flexWrap: "wrap" } },
        h(Button, { icon: "play_arrow", onClick: run, disabled: phase !== "drawing" }, "Run simulation"),
        h(Button, { variant: "text", icon: "restart_alt", onClick: reset }, "Draw again")));
  }

  /* ---------- LabStepper ---------- */
  var LAB_STEPS = ["Predict", "Act", "Observe", "Explain", "Debug"];
  function LabStepper(props) {
    var steps = props.steps || LAB_STEPS;
    var current = Math.max(0, Math.min(steps.length - 1, props.current || 0));
    return h("div", { className: cx("bb-stepper", props.className) },
      h("ol", { className: "bb-steps", "aria-label": "Lab steps" },
        steps.map(function (s, i) {
          return h("li", { key: s, className: cx("bb-step", i < current && "bb-step-done", i === current && "bb-step-now"), "aria-current": i === current ? "step" : undefined },
            i < current ? icon("check", true) : h("span", { className: "bb-mono", style: { fontSize: 12 } }, i + 1), s);
        })),
      h("div", { className: "bb-step-card" },
        h(Kiki, { state: props.kikiState || "pointing", size: 40, lead: "lab" }),
        h("div", { style: { display: "grid", gap: 8 } },
          h("div", { style: { fontWeight: 600 } }, props.title || "Pick the diode from the parts panel"),
          h("div", { style: { fontSize: 14, color: "var(--pencil, #5f6368)" } }, props.hint || "It's the triangle with a bar. Drag it between the transformer and the load resistor."),
          props.onNext ? h("div", null, h(Button, { variant: "tonal", icon: "arrow_forward", onClick: props.onNext }, props.nextLabel || "Done, next step")) : null)));
  }

  /* ---------- Spotlight ---------- */
  function Spotlight(props) {
    return h("div", { className: cx("bb-spot", props.className), style: props.style },
      props.active === false ? null : h("div", { className: "bb-spot-dim", "aria-hidden": "true" }),
      props.children);
  }
  function SpotlightTarget(props) {
    return h("span", { className: "bb-spot-target", style: { display: "inline-block" } }, props.children, h("span", { className: "bb-spot-ring", "aria-hidden": "true" }));
  }
  Spotlight.Target = SpotlightTarget;

  /* ---------- FaultCard ---------- */
  function FaultCard(props) {
    var questions = props.questions || ["What do you see on the scope that you didn't predict?", "Which half of the wave is passing now?", "Which way is the diode pointing?"];
    var sq = useState(1); var shown = sq[0], setShown = sq[1];
    var sf = useState(!!props.fixed); var fixed = sf[0], setFixed = sf[1];
    return h("div", { className: cx("bb-fault", fixed && "bb-fault-fixed", props.className) },
      h("div", { className: "bb-fault-head" },
        h("span", { className: "bb-fault-type" }, icon("build"), (props.type || "Flipped").toUpperCase()),
        h("span", { className: "bb-label", style: { color: fixed ? "var(--green-ink, #137333)" : "var(--pencil, #5f6368)" } }, fixed ? "Fixed" : "Your lab partner changed something")),
      h("div", { style: { fontSize: 15 } }, h("b", null, "Symptom: "), props.symptom || "Only the negative half-cycles appear on the scope."),
      fixed ? h("div", { style: { fontSize: 15 } }, icon("check_circle", true), " ", props.fixedMessage || "Fixed. Now explain in English why the output changed.")
        : h(React.Fragment, null,
          questions.slice(0, shown).map(function (q, i) { return h("div", { key: i, className: "bb-fault-q" }, h(Kiki, { state: "asking", size: 26 }), h("span", null, q)); }),
          h("div", { className: "bb-fault-actions" },
            shown < questions.length ? h(Button, { variant: "tonal", icon: "help", onClick: function () { setShown(shown + 1); } }, "Another hint") : null,
            h(Button, { icon: "check", onClick: function () { setFixed(true); if (props.onFixed) props.onFixed(); } }, "I fixed it"))));
  }

  /* ---------- AnswerOverlay (Snap your answer) ---------- */
  var SNAP_SAMPLE = {
    question: "Explain the working of a half-wave rectifier with a neat diagram. (5 marks)",
    score: { concept: "4/5", english: "English cost you 1 mark" },
    lines: [
      { tick: { label: "Def", ok: true }, parts: ["A half wave rectifier converts AC in to pulsating DC."] },
      { tick: { label: "Work", ok: true }, parts: ["In positive half cycle the ", { issue: 0, text: "diode is pass current" }, " so output comes."] },
      { tick: { label: "Work", ok: true }, parts: ["In negative half cycle diode is reverse bias and blocks."] },
      { tick: { label: "Wave", ok: true }, parts: [{ issue: 1, text: "When voltage is more than 0.7 the current start." }] },
      { tick: { label: "Diag", ok: false }, parts: ["(diagram: transformer, diode, Rʟ)"] }
    ],
    issues: [
      { kind: "mark", odia: "ଏଠାରେ 'pass' ବଦଳରେ 'conducts' ଲେଖ। ପରୀକ୍ଷାରେ ଏହା ସଠିକ୍ technical ଶବ୍ଦ।", fix: "the diode conducts current", cost: "This cost 1 mark." },
      { kind: "tip", odia: "'start' ବଦଳରେ 'starts' ଲେଖ। ଏହା ପାଇଁ ମାର୍କ କଟିନି, କେବଳ ଏକ tip।", fix: "Once the voltage crosses 0.7 V, current starts to flow.", cost: "Tip only: no marks lost." }
    ]
  };
  function SnapMark(props) {
    var st = useState(false); var open = st[0], setOpen = st[1];
    var ref = useOutsideClose(open, setOpen);
    var issue = props.issue;
    return h("span", { className: "bb-term-wrap", ref: ref },
      h("button", { type: "button", className: cx("bb-snap-mark", issue.kind === "tip" && "bb-snap-tip"), "aria-expanded": open, onClick: function () { setOpen(!open); } }, props.text),
      open ? h("span", { className: "bb-snap-pop", role: "dialog", "aria-label": "Explanation" },
        h("span", { className: "bb-label", style: { color: "var(--yellow-ink, #9a5500)" } }, issue.cost),
        h("span", null, withOdia(issue.odia, "s")),
        h("span", { className: "bb-snap-fix" }, issue.fix)) : null);
  }
  function AnswerOverlay(props) {
    var data = props.data || SNAP_SAMPLE;
    return h("div", { className: cx("bb-snap", props.className) },
      h("div", { style: { fontSize: 14, color: "var(--pencil, #5f6368)" } }, data.question),
      h("div", { className: "bb-snap-score" },
        h("span", { className: "bb-pill bb-pill-concept-yes" }, icon("check_circle", true), "Concept " + data.score.concept),
        h("span", { className: "bb-pill bb-pill-english-yes" }, icon("edit_note"), data.score.english)),
      h("div", { className: "bb-snap-paper", role: "group", "aria-label": "Your handwritten answer with marks" },
        data.lines.map(function (ln, i) {
          return h("div", { key: i, className: "bb-snap-line" },
            ln.tick ? h("span", { className: cx("bb-snap-tick", !ln.tick.ok && "bb-snap-tick-miss") }, icon(ln.tick.ok ? "check" : "remove"), ln.tick.label) : null,
            ln.parts.map(function (p, j) { return typeof p === "string" ? h(React.Fragment, { key: j }, p) : h(SnapMark, { key: j, text: p.text, issue: data.issues[p.issue] }); }));
        })),
      h("div", { style: { fontSize: 13, color: "var(--pencil, #5f6368)" } }, "Tap a yellow mark for the Odia explanation and the exam-ready English."));
  }

  /* ---------- ClassPulseBar ---------- */
  function ClassPulseBar(props) {
    var m = props.mastered || 0, l = props.language || 0, c = props.concept || 0;
    return h("div", { className: cx("bb-pulse", props.className) },
      h("div", { className: "bb-pulse-head" },
        h("span", { className: "bb-pulse-name" }, props.label || "Reverse bias"),
        props.students ? h("span", { className: "bb-mono", style: { fontSize: 12, color: "var(--pencil, #5f6368)" } }, props.students + " students") : null),
      props.hidden ? h("div", { style: { fontSize: 13, color: "var(--pencil, #5f6368)" } }, "Hidden: fewer than 10 students have tried this.")
        : h(React.Fragment, null,
          h("div", { className: "bb-pulse-bar", role: "img", "aria-label": m + "% mastered, " + l + "% language gap, " + c + "% concept gap" },
            h("span", { className: "bb-pulse-mastered", style: { width: m + "%" } }),
            h("span", { className: "bb-pulse-language", style: { width: l + "%" } }),
            h("span", { className: "bb-pulse-concept", style: { width: c + "%" } })),
          h("div", { className: "bb-pulse-legend" },
            h("span", null, h("b", null, m + "%"), " mastered"),
            h("span", null, h("b", null, l + "%"), " language gap"),
            h("span", null, h("b", null, c + "%"), " concept gap"))));
  }

  /* ---------- KikiPointer: Kiki's on-screen guide form ---------- */
  var KP_DOTS = {
    idle: [[46, 48], [53, 53], [60, 58], [67, 63]],
    pointing: [[40, 44], [45, 48], [50, 52], [55, 56]],
    tapping: [[46, 48], [53, 53], [60, 58], [67, 63]],
    dragging: [[44, 54], [52, 60], [60, 66], [68, 72]],
    tracing: [[48, 48], [56, 48], [64, 48], [72, 48]],
    thinking: [[26, 4], [54, 32], [26, 60], [-2, 32]],
    asking: [[48, 40], [56, 46], [64, 40], [72, 46]],
    listening: [[46, 46], [53, 46], [60, 46], [67, 46]],
    celebrating: [[64, 6], [76, 34], [66, 72], [34, 76]],
    unsure: [[54, 16], [72, 40], [46, 68], [74, 70]],
    waiting: [[46, 48], [53, 53], [60, 58], [67, 63]]
  };
  var KP_LABELS = { idle: "Kiki", pointing: "Kiki is pointing here", tapping: "Kiki says: tap here", dragging: "Kiki is showing how to drag this", tracing: "Kiki is reading this word with you", thinking: "Kiki is thinking", asking: "Kiki is asking you a question", listening: "Kiki is listening", celebrating: "Kiki is celebrating", unsure: "Kiki is not sure", waiting: "Kiki is waiting for you here" };
  var KP_BODY = "M12 8 L12 46 L21.5 37.5 L28.5 53 L35 50 L28 35 L40 35 Z";
  function KikiPointer(props) {
    var state = KP_DOTS[props.state] ? props.state : "idle";
    var size = props.size || 64;
    var leadIndex = DIMS.map(function (d) { return d.key; }).indexOf(props.lead);
    var leadColor = leadIndex >= 0 ? KIKI_COLORS[leadIndex] : KIKI_COLORS[0];
    var dots = KP_DOTS[state];
    var eyes;
    if (state === "celebrating") eyes = h("g", { className: "kp-eyes-happy", fill: "none", stroke: "#ffffff", strokeWidth: 1.8, strokeLinecap: "round" }, h("path", { d: "M14.8 26 q2.2 -3.2 4.4 0" }), h("path", { d: "M20.8 26 q2.2 -3.2 4.4 0" }));
    else {
      var up = state === "thinking" || state === "asking";
      eyes = h("g", { className: cx("kp-eyes", state === "unsure" && "kp-look") }, h("circle", { cx: 16.8, cy: up ? 23 : 25, r: 2.8, fill: "#ffffff" }), h("circle", { cx: 23.4, cy: up ? 23 : 25, r: 2.8, fill: "#ffffff" }));
    }
    var dotEls = dots.map(function (p, i) {
      var r = i === leadIndex ? 4.2 : 3.2;
      return h("g", { key: i, className: "kp-dot-g", style: { transform: "translate(" + p[0] + "px," + p[1] + "px)" } },
        h("rect", { className: "kp-dot", x: -r, y: -r, width: r * 2, height: r * 2, rx: r, fill: KIKI_COLORS[i], style: { animationDelay: (i * 0.12) + "s" } }));
    });
    return h("svg", { className: cx("kp", "kp-" + state, props.className), width: size, height: size, viewBox: "0 0 80 80", role: "img", "aria-label": props.label || KP_LABELS[state], style: Object.assign({ transform: props.flip ? "scaleX(-1)" : undefined }, props.style) },
      state === "waiting" ? h("circle", { className: "kp-wait-ring", cx: 12, cy: 8, r: 9, fill: "none", stroke: leadColor, strokeWidth: 2.5, strokeDasharray: "4 3" }) : null,
      state === "asking" ? h("text", { className: "kp-q", x: 50, y: 30, fontSize: 26, fontWeight: 700, fill: leadColor, fontFamily: "Baloo 2, sans-serif" }, "?") : null,
      state === "tapping" ? h("circle", { className: "kp-ripple", cx: 12, cy: 8, r: 9, fill: "none", stroke: leadColor, strokeWidth: 3 }) : null,
      state === "thinking" ? h("g", { className: "kp-orbit" }, dotEls) : h("g", null, dotEls),
      h("g", { className: "kp-body" },
        state === "dragging" ? h("rect", { x: 2, y: 0, width: 22, height: 12, rx: 4, fill: "var(--green-tint, #e6f4ea)", stroke: "var(--green, #34a853)", strokeWidth: 2, opacity: 0.95 }) : null,
        h("path", { d: KP_BODY, fill: "#1f1f1f", stroke: "#ffffff", strokeWidth: 3, strokeLinejoin: "round" }),
        eyes));
  }

  /* ---------- KikiWalkthrough: Kiki explains a lesson card ---------- */
  var WALK_SAMPLE = {
    paragraph: [{ id: "diode", text: "Diode" }, " current କୁ only one direction ରେ ଯିବାକୁ ଦିଏ। ", { id: "fb", text: "forward bias" }, " ରେ, about 0.7 V ", { id: "civ", text: "cut-in voltage" }, " ପରେ ଏହା ", { id: "cond", text: "conducts" }, "। ", { id: "rb", text: "reverse bias" }, " ରେ ଏହା ", { id: "block", text: "current କୁ block କରେ", phrase: true }, "।"],
    steps: [
      { target: "diode", action: "sweep", dim: "words", odia: "ପ୍ରଥମେ ଶବ୍ଦଟି ଦେଖ: diode। ଏହା current ପାଇଁ ଏକ one-way gate।", en: "Start with the word itself: diode. It is a one-way gate for current." },
      { target: "fb", action: "marker", dim: "words", odia: "forward bias ମାନେ p-side ରେ positive voltage। ସେତେବେଳେ current ଯାଏ।", en: "Forward bias means positive voltage on the p-side. That is when current flows." },
      { target: "civ", action: "lens", dim: "words", odia: "ଏପରି ଯେକୌଣସି ଶବ୍ଦ ଛୁଇଁଲେ ତାର ଓଡ଼ିଆ ଅର୍ଥ ଦେଖିବ।", en: "Cut-in voltage. Tap any word like this to see it up close with its Odia meaning." },
      { target: "civ", action: "connect", to: "knee", dim: "concept", odia: "graph ରେ ଦେଖ: ପ୍ରାୟ 0.7 V ପର୍ଯ୍ୟନ୍ତ current ନାହିଁ, ତା'ପରେ ହଠାତ୍ ବଢ଼େ।", en: "On the graph: almost no current until about 0.7 V, then it rises fast." },
      { target: "block", action: "marker", dim: "concept", odia: "ମୁଖ୍ୟ କଥା: reverse bias ରେ ଏହା current କୁ ଅଟକାଏ।", en: "The key idea: in reverse bias, it blocks the current." },
      { target: "cond", action: "circle", dim: "english", odia: "ପରୀକ୍ଷାରେ 'passes' ନୁହେଁ, 'conducts' ଲେଖ।", en: "Exam word: write “conducts”, not “passes”." }
    ]
  };
  var WALK_POINTER = { sweep: "tracing", marker: "tracing", lens: "pointing", connect: "pointing", circle: "tracing", point: "pointing", tap: "tapping" };
  function MiniCurve() {
    var pts = [];
    for (var k = 0; k <= 60; k++) { var v = -1 + 2 * k / 60; var i = diodeCurrent(v); pts.push((20 + (v + 1) / 2 * 170).toFixed(1) + "," + (100 - Math.min(i, 20) / 20 * 84).toFixed(1)); }
    var kx = 20 + (0.7 + 1) / 2 * 170;
    return h("svg", { className: "kk-fig", viewBox: "0 0 200 116", role: "img", "aria-label": "Diode V-I curve with the knee near 0.7 V" },
      h("line", { x1: 20, y1: 100, x2: 192, y2: 100, stroke: "var(--line, #d9d6cf)", strokeWidth: 1.5 }),
      h("line", { x1: 105, y1: 10, x2: 105, y2: 104, stroke: "var(--line, #d9d6cf)", strokeWidth: 1.5 }),
      h("polyline", { points: pts.join(" "), fill: "none", stroke: "var(--ink, #1f1f1f)", strokeWidth: 2 }),
      h("text", { x: kx, y: 113, fontSize: 9, textAnchor: "middle", fill: "var(--pencil, #5f6368)", fontFamily: "Roboto Mono, monospace" }, "0.7 V"),
      h("circle", { "data-kk-point": "knee", cx: kx, cy: 100 - diodeCurrent(0.7) / 20 * 84, r: 4, fill: "var(--blue, #4285f4)" }));
  }
  function KikiWalkthrough(props) {
    var data = props.data || WALK_SAMPLE;
    var steps = data.steps;
    var ss = useState(0); var step = ss[0], setStep = ss[1];
    var sp = useState(!!props.autoPlay); var playing = sp[0], setPlaying = sp[1];
    var sg = useState(null); var geo = sg[0], setGeo = sg[1];
    var boxRef = useRef(null);
    var cur = steps[step];
    var size = 44;
    var measure = useCallback(function () {
      var box = boxRef.current; if (!box) return;
      var b = box.getBoundingClientRect();
      var el = box.querySelector('[data-kk="' + cur.target + '"]'); if (!el) return;
      var r = el.getBoundingClientRect();
      var g = { x: r.left - b.left, y: r.top - b.top, w: r.width, h: r.height, bw: b.width };
      if (cur.to) { var pt = box.querySelector('[data-kk-point="' + cur.to + '"]'); if (pt) { var pr = pt.getBoundingClientRect(); g.px = pr.left - b.left + pr.width / 2; g.py = pr.top - b.top + pr.height / 2; } }
      setGeo(g);
    }, [cur]);
    useEffect(function () {
      measure();
      var t = setTimeout(measure, 350);
      window.addEventListener("resize", measure);
      return function () { clearTimeout(t); window.removeEventListener("resize", measure); };
    }, [measure]);
    useEffect(function () {
      if (!playing) return undefined;
      var t = setTimeout(function () { if (step < steps.length - 1) setStep(step + 1); else setPlaying(false); }, props.stepMs || 3800);
      return function () { clearTimeout(t); };
    }, [playing, step]);
    var focus = cur.action !== "sweep";
    var dimClass = "kk-d-" + (cur.dim || "words");
    var tipX = geo ? geo.x + Math.min(geo.w * 0.5, 30) : 0, tipY = geo ? geo.y + geo.h - 2 : 0;
    var lensEntry = cur.action === "lens" ? (GLOSSARY[(data.paragraph.filter(function (s) { return s.id === cur.target; })[0] || {}).text] || {}) : null;
    var lensWord = cur.action === "lens" ? (data.paragraph.filter(function (s) { return s.id === cur.target; })[0] || {}).text : "";
    return h("div", { className: cx("kk", props.className) },
      h("div", { className: cx("kk-stage", focus && "kk-focus", dimClass), ref: boxRef },
        h("p", { className: "kk-para" }, data.paragraph.map(function (s, i) {
          if (typeof s === "string") return h("span", { key: i, className: "kk-plain" }, withOdia(s, i));
          var active = s.id === cur.target;
          var seen = steps.slice(0, step).some(function (x) { return x.target === s.id; });
          var act = active ? (cur.action === "lens" || cur.action === "connect" ? "marker" : cur.action) : null;
          return h("span", { key: i, "data-kk": s.id, className: cx("kk-tgt", s.phrase ? "kk-phrase" : "kk-term", active && "kk-active", act && "kk-" + act, seen && !active && "kk-seen") }, withOdia(s.text, "t" + i));
        })),
        data.figure === false ? null : h("div", { className: "kk-figwrap" }, h(MiniCurve), h("span", { className: "bb-label", style: { color: "var(--pencil, #5f6368)" } }, "V-I curve")),
        geo && cur.action === "circle" ? h("svg", { className: "kk-overlay", "aria-hidden": "true" },
          h("ellipse", { className: "kk-circle", cx: geo.x + geo.w / 2, cy: geo.y + geo.h / 2, rx: geo.w / 2 + 10, ry: geo.h / 2 + 7, transform: "rotate(-4 " + (geo.x + geo.w / 2) + " " + (geo.y + geo.h / 2) + ")" })) : null,
        geo && cur.action === "connect" && geo.px != null ? h("svg", { className: "kk-overlay", "aria-hidden": "true" },
          h("path", { className: "kk-connect", d: "M" + (geo.x + geo.w / 2) + " " + (geo.y + geo.h + 4) + " C " + (geo.x + geo.w / 2) + " " + (geo.py - 30) + ", " + geo.px + " " + (geo.y + geo.h + 40) + ", " + geo.px + " " + (geo.py - 7) }),
          h("circle", { className: "kk-ping", cx: geo.px, cy: geo.py, r: 10 })) : null,
        geo && cur.action === "lens" ? h("div", { className: "kk-lens", role: "dialog", "aria-label": lensWord, style: { left: Math.max(0, Math.min(geo.x - 20, geo.bw - 240)), top: geo.y + geo.h + 12 } },
          h("span", { className: "kk-lens-word" }, lensWord),
          lensEntry && lensEntry.odia ? h("span", null, withOdia(lensEntry.odia, "l")) : null,
          h("span", { className: "bb-sheet-row" }, h(Button, { variant: "tonal", icon: "volume_up", onClick: function () { speak(lensWord, "en-IN"); } }, "Hear it"))) : null,
        geo ? h("div", { className: "kk-pointer", style: { left: tipX - 12 / 80 * size, top: tipY - 8 / 80 * size } }, h(KikiPointer, { state: playing || step > 0 ? WALK_POINTER[cur.action] || "pointing" : "waiting", size: size, lead: cur.dim })) : null),
      h("div", { className: "kk-caption", "aria-live": "polite" },
        h(Kiki, { state: playing ? "speaking" : "idle", size: 34, lead: cur.dim }),
        h("div", { className: "kk-lines" },
          h("span", { className: "kk-odia" }, withOdia(cur.odia || "", "c")),
          h("span", { className: "kk-en" }, cur.en)),
        h("div", { className: "kk-controls" },
          h("button", { type: "button", className: "kk-ctrl", "aria-label": "Previous", disabled: step === 0, onClick: function () { setStep(Math.max(0, step - 1)); } }, icon("skip_previous")),
          h("button", { type: "button", className: "kk-ctrl kk-play", "aria-label": playing ? "Pause" : step === steps.length - 1 ? "Replay" : "Play", onClick: function () { if (!playing && step === steps.length - 1) setStep(0); setPlaying(!playing); } }, icon(playing ? "pause" : step === steps.length - 1 ? "replay" : "play_arrow", true)),
          h("button", { type: "button", className: "kk-ctrl", "aria-label": "Next", disabled: step === steps.length - 1, onClick: function () { setStep(Math.min(steps.length - 1, step + 1)); } }, icon("skip_next")))),
      h("div", { className: "kk-steps", "aria-hidden": "true" }, steps.map(function (x, i) { return h("span", { key: i, className: cx(i === step && "kk-on", i < step && "kk-done"), style: { background: i <= step ? DIMS.filter(function (d) { return d.key === x.dim; })[0].fill : undefined } }); })));
  }

  /* ---------- LabGuide: Kiki guiding inside a lab tool ---------- */
  function LabGuide(props) {
    var sp = useState("intro"); var phase = sp[0], setPhase = sp[1];
    var sk = useState({ state: "waiting", target: "diode", text: "I'll show you once, then it's your turn.", ghost: false }); var k = sk[0], setK = sk[1];
    var sf = useState(false); var placed = sf[0], setPlaced = sf[1];
    var ss = useState(false); var selected = ss[0], setSelected = ss[1];
    var sr = useState(false); var ran = sr[0], setRan = sr[1];
    var sg = useState({}); var pos = sg[0], setPos = sg[1];
    var boxRef = useRef(null), timers = useRef([]);
    var size = 46;
    function at(name) {
      var box = boxRef.current; if (!box) return null;
      var el = box.querySelector('[data-lg="' + name + '"]'); if (!el) return null;
      var b = box.getBoundingClientRect(), r = el.getBoundingClientRect();
      return { x: r.left - b.left + r.width * 0.55, y: r.top - b.top + r.height * 0.6, w: b.width };
    }
    var remeasure = useCallback(function () { var p = at(k.target); if (p) setPos(p); }, [k.target, placed, ran]);
    useEffect(function () { remeasure(); var t = setTimeout(remeasure, 300); window.addEventListener("resize", remeasure); return function () { clearTimeout(t); window.removeEventListener("resize", remeasure); }; }, [remeasure]);
    useEffect(function () { return function () { timers.current.forEach(clearTimeout); }; }, []);
    function later(fn, ms) { timers.current.push(setTimeout(fn, ms)); }
    function showMe() {
      timers.current.forEach(clearTimeout); timers.current = [];
      setPlaced(false); setRan(false); setSelected(false); setPhase("demo");
      setK({ state: "pointing", target: "diode", text: "This is the diode: the triangle with a bar.", ghost: false });
      later(function () { setK({ state: "dragging", target: "slotB", text: "Drag it into the gap between the transformer and the resistor.", ghost: true }); }, 1400);
      later(function () { setK({ state: "celebrating", target: "slotB", text: "Like that.", ghost: false }); }, 3000);
      later(function () { setPhase("yourturn"); setK({ state: "waiting", target: "diode", text: "Your turn. Tap the diode, then tap the empty slot.", ghost: false }); }, 4200);
    }
    function pickDiode() { if (phase !== "yourturn" || placed) return; setSelected(true); setK({ state: "pointing", target: "slotB", text: "Now tap the empty slot.", ghost: false }); }
    function pickSlot(name) {
      if (phase !== "yourturn" || placed) return;
      if (!selected) { setK({ state: "unsure", target: "diode", text: "Pick the diode first. It's in the parts panel.", ghost: false }); return; }
      if (name !== "slotB") { setK({ state: "unsure", target: name, text: name === "slotA" ? "That slot has the transformer. The diode goes in the gap after it." : "That slot has the resistor. The diode goes before it.", ghost: false }); return; }
      setPlaced(true); setSelected(false); setK({ state: "celebrating", target: "slotB", text: "Spot on. The circuit is complete.", ghost: false });
      later(function () { setPhase("run"); setK({ state: "tapping", target: "run", text: "Now run the simulation.", ghost: false }); }, 1300);
    }
    function run() { if (phase !== "run") return; setRan(true); setPhase("ask"); setK({ state: "asking", target: "scope", text: "Why is the bottom half of the wave flat? You'll answer in English next.", ghost: false }); }
    var dimOthers = phase === "run";
    var wave = []; for (var q = 0; q <= 80; q++) { var x = q / 80, sv = Math.sin(x * Math.PI * 4); wave.push((x * 200).toFixed(1) + "," + (50 - (ran ? Math.max(0, sv) : 0) * 38).toFixed(1)); }
    var inputWave = []; for (var q2 = 0; q2 <= 80; q2++) { var x2 = q2 / 80; inputWave.push((x2 * 200).toFixed(1) + "," + (50 - Math.sin(x2 * Math.PI * 4) * 38).toFixed(1)); }
    var calloutLeft = pos.x != null ? Math.min(Math.max(8, pos.x + 30), (pos.w || 600) - 236) : 0;
    return h("div", { className: cx("lg", props.className) },
      h("div", { className: "lg-tool", ref: boxRef },
        h("div", { className: "lg-bar" }, h("span", { className: "bb-mono" }, "rectifier-lab.sim"), h("span", { className: "lg-step" }, phase === "intro" ? "Ready" : phase === "demo" ? "Kiki is showing" : phase === "yourturn" ? "Your turn" : phase === "run" ? "Run it" : "Look at the output")),
        h("div", { className: cx("lg-body", dimOthers && "lg-dimmed") },
          h("div", { className: "lg-palette lg-dim-me" },
            h("span", { className: "lg-head" }, "PARTS"),
            h("button", { type: "button", className: "lg-part", disabled: true }, "Transformer"),
            h("button", { type: "button", "data-lg": "diode", className: cx("lg-part", selected && "lg-selected"), onClick: pickDiode, disabled: placed }, h("span", { className: "lg-sym" }, "▶|"), " Diode"),
            h("button", { type: "button", className: "lg-part", disabled: true }, "Resistor")),
          h("div", { className: "lg-board lg-dim-me" },
            h("span", { className: "lg-head" }, "BOARD"),
            h("div", { className: "lg-slots" },
              h("button", { type: "button", "data-lg": "slotA", className: "lg-slot lg-filled", onClick: function () { pickSlot("slotA"); } }, "Transformer"),
              h("span", { className: "lg-wire" }),
              h("button", { type: "button", "data-lg": "slotB", className: cx("lg-slot", placed ? "lg-filled lg-new" : "lg-empty"), onClick: function () { pickSlot("slotB"); } }, placed ? "▶| Diode" : "Empty"),
              h("span", { className: "lg-wire" }),
              h("button", { type: "button", "data-lg": "slotC", className: "lg-slot lg-filled", onClick: function () { pickSlot("slotC"); } }, "1 kΩ"))),
          h("div", { className: "lg-scope lg-dim-me", "data-lg": "scope" },
            h("span", { className: "lg-head" }, "SCOPE"),
            h("svg", { viewBox: "0 0 200 100", preserveAspectRatio: "none", "aria-label": ran ? "Output: only the positive half-cycles" : "Output: nothing yet", role: "img" },
              h("polyline", { points: inputWave.join(" "), fill: "none", stroke: "rgba(201,214,223,0.4)", strokeWidth: 1.5, strokeDasharray: "4 4" }),
              h("polyline", { points: wave.join(" "), fill: "none", stroke: "var(--scope-trace, #5be38a)", strokeWidth: 2.5 })))),
        h("div", { className: "lg-foot" },
          h("button", { type: "button", "data-lg": "run", className: cx("lg-run", dimOthers && "lg-lit"), onClick: run, disabled: phase !== "run" }, "▶ Run")),
        pos.x != null ? h("div", { className: "kk-pointer lg-pointer", style: { left: pos.x - 12 / 80 * size, top: pos.y - 8 / 80 * size } },
          k.ghost ? h("span", { className: "lg-ghost" }, "▶| Diode") : null,
          h(KikiPointer, { state: k.state, size: size, lead: "lab" })) : null,
        pos.x != null ? h("div", { className: "lg-callout", role: "status", style: { left: calloutLeft, top: Math.max(8, pos.y + 34) } }, k.text) : null),
      h("div", { className: "lg-actions" },
        h(Button, { variant: phase === "intro" ? "filled" : "tonal", icon: phase === "intro" ? "play_arrow" : "replay", onClick: showMe }, phase === "intro" ? "Show me" : "Show me again"),
        h("span", { style: { fontSize: 13, color: "var(--pencil, #5f6368)" } }, "Your own cursor stays normal. Kiki's pointer has eyes and four coloured dots.")));
  }

  /* ---------- PracticeReport: analysis of a written practice set ---------- */
  var PRACTICE_SAMPLE = {
    title: "Mid-sem practice set · Basic Electronics", time: "23 of 25 min", total: 25,
    questions: [
      { n: "Q1", topic: "Half-wave rectifier", got: 4, max: 5, english: 1, note: "Concept right. “pass” instead of “conducts” cost a mark." },
      { n: "Q2", topic: "Filter capacitor", got: 2, max: 5, english: 0, note: "Concept gap: why the capacitor smooths the output." },
      { n: "Q3", topic: "Ripple factor", got: 3, max: 5, english: 2, note: "Right formula. The explanation was unclear in English." },
      { n: "Q4", topic: "Diode V-I characteristic", got: 5, max: 5, english: 0, note: "Full marks." },
      { n: "Q5", topic: "Zener diode", got: 3, max: 5, english: 0, note: "Concept partly there. The diagram was missing." }
    ]
  };
  function PracticeReport(props) {
    var data = props.data || PRACTICE_SAMPLE;
    var got = 0, eng = 0, con = 0;
    data.questions.forEach(function (q) { got += q.got; eng += q.english; con += q.max - q.got - q.english; });
    var total = data.total || (got + eng + con);
    var weak = data.questions.filter(function (q) { return q.max - q.got - q.english >= 2 || q.english >= 1; }).map(function (q) {
      var c = q.max - q.got - q.english; return { topic: q.topic, kind: c >= 2 ? "concept" : "english", lost: c >= 2 ? c : q.english };
    });
    return h("div", { className: cx("pr", props.className) },
      h("div", { className: "pr-head" },
        h("span", { className: "bb-label", style: { color: "var(--pencil, #5f6368)" } }, data.title),
        h("div", { className: "pr-score" }, h("span", { className: "pr-big" }, got), h("span", { className: "pr-of" }, "/ " + total), h("span", { className: "bb-mono", style: { marginLeft: "auto", fontSize: 12, color: "var(--pencil, #5f6368)" } }, data.time)),
        h("div", { className: "bb-pulse-bar", role: "img", "aria-label": got + " marks earned, " + eng + " lost to English, " + con + " lost to concept gaps" },
          h("span", { className: "bb-pulse-mastered", style: { width: got / total * 100 + "%" } }),
          h("span", { className: "bb-pulse-language", style: { width: eng / total * 100 + "%" } }),
          h("span", { className: "bb-pulse-concept", style: { width: con / total * 100 + "%" } })),
        h("div", { className: "bb-pulse-legend" }, h("span", null, h("b", null, got), " earned"), h("span", null, h("b", null, eng), " lost to English"), h("span", null, h("b", null, con), " lost to concept gaps"))),
      h("div", { className: "pr-list" }, data.questions.map(function (q) {
        var c = q.max - q.got - q.english;
        return h("button", { key: q.n, type: "button", className: "pr-q", onClick: function () { if (props.onOpen) props.onOpen(q); } },
          h("span", { className: "pr-qn bb-mono" }, q.n),
          h("span", { className: "pr-qbody" },
            h("span", { className: "pr-topic" }, q.topic),
            h("span", { className: "pr-note" }, q.note)),
          h("span", { className: "pr-marks" },
            h("span", { className: "bb-mono" }, q.got + "/" + q.max),
            h("span", { className: "pr-mini", "aria-hidden": "true" },
              h("span", { className: "bb-pulse-mastered", style: { width: q.got / q.max * 100 + "%" } }),
              h("span", { className: "bb-pulse-language", style: { width: q.english / q.max * 100 + "%" } }),
              h("span", { className: "bb-pulse-concept", style: { width: c / q.max * 100 + "%" } }))));
      })),
      weak.length ? h("div", { className: "pr-weak" },
        h("span", { className: "bb-label" }, "Fix these before the exam"),
        weak.map(function (w) {
          return h("div", { key: w.topic, className: "pr-weak-row" },
            h("span", { className: cx("bb-pill", w.kind === "concept" ? "bb-pill-notyet" : "bb-pill-english-yes") }, icon(w.kind === "concept" ? "psychology" : "translate"), w.kind === "concept" ? "Concept" : "English"),
            h("span", { style: { flex: 1, minWidth: 0 } }, w.topic),
            h("span", { className: "bb-mono", style: { fontSize: 12, color: "var(--pencil, #5f6368)" } }, "−" + w.lost));
        }),
        props.onRepair !== false ? h(Button, { icon: "build", onClick: props.onRepair }, "Make my repair map") : null) : null);
  }

  var api = {
    Button: Button, Kiki: Kiki, MasteryRing: MasteryRing, LanguageDial: LanguageDial, TermChip: TermChip, MorphText: MorphText,
    WordSticker: WordSticker, LessonProgress: LessonProgress, DiodeExplorable: DiodeExplorable, DiagnosisCard: DiagnosisCard,
    VoiceScope: VoiceScope, ReceiptCompare: ReceiptCompare, MapNode: MapNode, Snackbar: Snackbar, SourceTag: SourceTag,
    PredictionCanvas: PredictionCanvas, LabStepper: LabStepper, Spotlight: Spotlight, FaultCard: FaultCard,
    AnswerOverlay: AnswerOverlay, ClassPulseBar: ClassPulseBar,
    KikiPointer: KikiPointer, KikiWalkthrough: KikiWalkthrough, LabGuide: LabGuide, PracticeReport: PracticeReport,
    samples: { glossary: GLOSSARY, diodeLevels: DIODE_LEVELS, levelNames: LEVEL_NAMES, snap: SNAP_SAMPLE, dims: DIMS, walkthrough: WALK_SAMPLE, practice: PRACTICE_SAMPLE }
  };
  window.Breadboard = Object.assign(window.Breadboard || {}, api);
})();
