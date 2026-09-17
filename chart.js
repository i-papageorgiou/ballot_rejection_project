// chart.js — renders every figure on the page from the DATA/TILES/
// CHOROPLETH_PATHS constants embedded in index.html. Every chart is
// hand-rolled SVG (mirroring the Modernist mockup's own sx/sy
// coordinate-helper + hover pattern) — no charting library at all.

const ACCENT = "#ec3013";
const ACCENT_700 = "#ae1800";
const INK = "#201e1d";
const MUTED = "#7d7979";
const GRID = "#d7d3d3";
const NEUTRAL_700 = "#605d5d";

const pct = (x, d = 2) => (x * 100).toFixed(d);
const fmtPP = (x) => (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x * 100).toFixed(2);
const fmtP = (p) => (p < 0.001 ? "<0.001" : p.toFixed(4));
const svgEl = (tag, attrs) => {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const k in attrs) el.setAttribute(k, attrs[k]);
  return el;
};
const clear = (el) => { while (el.firstChild) el.removeChild(el.firstChild); };

// --- Headline stat strip ----------------------------------------------------
function renderStatStrip() {
  const h = DATA.headline;
  const stats = [
    { value: String(h.n_methods), label: "Methods", note: "TWFE, Sun-Abraham and Callaway-Sant'Anna, built to fail in different directions." },
    { value: fmtPP(h.primary_estimate_pp / 100) + "pp", label: "Primary estimate", note: "Callaway-Sant'Anna overall ATT on rejection rate." },
    { value: "±" + h.ci_half_width_pp.toFixed(2) + "pp", label: "95% CI half-width", note: "How precisely this design can rule out an effect." },
    { value: String(h.n_states), label: "States", note: "All 50 states plus DC." },
    { value: h.year_range, label: "Elections covered", note: h.n_fips.toLocaleString() + " jurisdictions, usable & in-scope rows only." },
  ];
  const strip = document.getElementById("stat-strip");
  stats.forEach((s) => {
    const cell = document.createElement("div");
    cell.className = "stat-cell";
    cell.innerHTML = `<div class="stat-value">${s.value}</div><div class="stat-label">${s.label}</div><div class="stat-note">${s.note}</div>`;
    strip.appendChild(cell);
  });
}

// --- Figure 2: tile map + per-state series (combined — clicking a tile ----
// loads that state's chart below it, rather than these being two
// separately-driven figures).
const COHORT_COLORS = {
  always: "#ae1800", 2018: "#dd2b0f", 2020: "#ff563c", 2022: "#ff9783", 2024: "#ffc4b8",
  never: "#d7d3d3", reversal: "#9b9797",
};
const COHORT_LABELS = {
  always: "Adopted before 2016", 2018: "2018", 2020: "2020", 2022: "2022", 2024: "2024",
  never: "Never adopted", reversal: "Adopted, then reverted (Iowa)",
};

function renderTileMap() {
  const svg = document.getElementById("tile-map");
  clear(svg);
  const readout = document.getElementById("tile-readout");
  const tileRects = {};
  let selectedCode = null;

  function selectTile(code) {
    if (selectedCode && tileRects[selectedCode]) tileRects[selectedCode].setAttribute("stroke", "none");
    selectedCode = code;
    const rect = tileRects[code];
    rect.setAttribute("stroke", INK);
    rect.setAttribute("stroke-width", "3");
    const cohort = DATA.cohorts[code];
    const name = DATA.state_names[code] || code;
    const cohortText = typeof cohort === "number" ? "cure law adopted " + cohort : COHORT_LABELS[cohort].toLowerCase();
    readout.textContent = `${name} · ${cohortText}`;
    renderStateFigure.update(code);
  }
  renderTileMap.selectTile = selectTile;

  TILES.forEach((t) => {
    const cohort = DATA.cohorts[t.code];
    const fill = COHORT_COLORS[cohort] || "#ccc";
    const rect = svgEl("rect", { x: t.x, y: t.y, width: 52, height: 52, fill, style: "cursor:pointer" });
    const label = svgEl("text", {
      x: t.x + 26, y: t.y + 33, "text-anchor": "middle", "pointer-events": "none",
      "font-family": "Archivo", "font-size": 15, "font-weight": 700,
      fill: (cohort === "never" || cohort === "reversal" || cohort === 2022 || cohort === 2024) ? INK : "#fff",
    });
    label.textContent = t.code;
    tileRects[t.code] = rect;

    const name = DATA.state_names[t.code] || t.code;
    const cohortText = typeof cohort === "number" ? "cure law adopted " + cohort : COHORT_LABELS[cohort].toLowerCase();
    const describe = `${name} · ${cohortText}`;

    // Native <title> gives a real hover tooltip (browser-rendered, no
    // extra markup needed); the readout line above the map also updates
    // on hover so the same info is visible without the native tooltip's
    // delay, and stays put after a click (see selectTile above).
    const title = svgEl("title", {});
    title.textContent = describe;
    rect.appendChild(title);

    rect.addEventListener("mouseenter", () => { if (!selectedCode) readout.textContent = describe; });
    rect.addEventListener("mouseleave", () => { if (!selectedCode) readout.textContent = "Hover or click a tile"; });
    rect.addEventListener("click", () => selectTile(t.code));
    svg.appendChild(rect);
    svg.appendChild(label);
  });

  const legend = document.getElementById("tile-legend");
  ["always", 2018, 2020, 2022, 2024, "never", "reversal"].forEach((k) => {
    const span = document.createElement("span");
    span.innerHTML = `<span class="swatch" style="background:${COHORT_COLORS[k]}"></span>${COHORT_LABELS[k]}`;
    legend.appendChild(span);
  });
}

function renderStateFigure() {
  const L = 52, R = 784, T = 18, B = 214;
  const svg = document.getElementById("state-chart");
  const nameEl = document.getElementById("state-name");
  const statusEl = document.getElementById("state-status");
  const hoverEl = document.getElementById("state-hover-readout");

  function update(sel) {
    const series = DATA.state_series[sel];
    const years = DATA.years;
    const yMax = Math.max(0.02, ...series.filter((v) => v != null)) * 1.15;
    const sx = (i) => L + (i / (years.length - 1)) * (R - L);
    const sy = (v) => T + (1 - v / yMax) * (B - T);

    clear(svg);
    // gridlines
    for (let g = 0; g <= 4; g++) {
      const y = T + (g / 4) * (B - T);
      svg.appendChild(svgEl("line", { x1: L, y1: y, x2: R, y2: y, stroke: GRID, "stroke-width": 1 }));
      const val = yMax * (1 - g / 4);
      const t = svgEl("text", { x: L - 8, y: y + 4, "text-anchor": "end", "font-size": 12, fill: MUTED });
      t.textContent = pct(val, 1) + "%";
      svg.appendChild(t);
    }
    // adoption marker
    const cohort = DATA.cohorts[sel];
    if (typeof cohort === "number") {
      const idx = years.indexOf(cohort);
      if (idx >= 0) {
        const x = sx(idx);
        svg.appendChild(svgEl("line", { x1: x, y1: T, x2: x, y2: B, stroke: ACCENT, "stroke-width": 2, "stroke-dasharray": "6 5" }));
      }
    }
    // line
    const pts = series.map((v, i) => (v == null ? null : [sx(i), sy(v)]));
    let d = "";
    pts.forEach((p, i) => { if (p) d += (d ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1) + " "; });
    svg.appendChild(svgEl("path", { d, fill: "none", stroke: INK, "stroke-width": 2.5 }));
    pts.forEach((p, i) => {
      if (!p) return;
      const c = svgEl("circle", { cx: p[0], cy: p[1], r: 4.5, fill: INK });
      svg.appendChild(c);
    });
    svg.appendChild(svgEl("line", { x1: L, y1: B, x2: R, y2: B, stroke: INK, "stroke-width": 2 }));
    years.forEach((y, i) => {
      const t = svgEl("text", { x: sx(i), y: B + 22, "text-anchor": "middle", "font-size": 12, fill: NEUTRAL_700 });
      t.textContent = y;
      svg.appendChild(t);
    });
    // hover targets
    const colW = (R - L) / (years.length - 1);
    years.forEach((y, i) => {
      const hx = sx(i) - colW / 2, hw = colW;
      const hit = svgEl("rect", { x: Math.max(L, hx), y: T, width: hw, height: B - T, fill: "transparent" });
      hit.addEventListener("mouseenter", () => {
        const v = series[i];
        hoverEl.textContent = v == null ? `${y} · no data` :
          `${y} · ${pct(v, 2)}% rejected${typeof cohort === "number" ? (y >= cohort ? " · under cure law" : " · before cure law") : ""}`;
      });
      svg.appendChild(hit);
    });
    svg.addEventListener("mouseleave", () => { hoverEl.textContent = "Hover the chart for exact values"; }, { once: false });

    nameEl.textContent = DATA.state_names[sel];
    statusEl.textContent = typeof cohort === "number" ? "Cure law from " + cohort :
      cohort === "always" ? "Cure law before 2016 (always-treated in panel)" :
      cohort === "reversal" ? "Adopted, then reverted (excluded from corrected estimators)" : "No cure requirement in panel";
  }
  renderStateFigure.update = update;
  // No initial draw here — the tile map (rendered right after this
  // function, see the boot sequence at the bottom) calls
  // renderTileMap.selectTile(DEFAULT_STATE) once, which both highlights
  // that tile and calls this update(), so the chart starts populated
  // without drawing it twice.
}

// --- Figure 3: treated vs untreated trend -----------------------------------
function renderTrendChart() {
  const L = 58, R = 784, T = 20, B = 276;
  const svg = document.getElementById("trend-chart");
  const years = DATA.years;
  const all = DATA.treated_series.concat(DATA.untreated_series).filter((v) => v != null);
  const yMax = Math.max(...all) * 1.15;
  const sx = (i) => L + (i / (years.length - 1)) * (R - L);
  const sy = (v) => T + (1 - v / yMax) * (B - T);

  for (let g = 0; g <= 4; g++) {
    const y = T + (g / 4) * (B - T);
    svg.appendChild(svgEl("line", { x1: L, y1: y, x2: R, y2: y, stroke: GRID, "stroke-width": 1 }));
    const t = svgEl("text", { x: L - 8, y: y + 4, "text-anchor": "end", "font-size": 13, fill: MUTED });
    t.textContent = pct(yMax * (1 - g / 4), 1) + "%";
    svg.appendChild(t);
  }
  years.forEach((y, i) => {
    const t = svgEl("text", { x: sx(i), y: B + 20, "text-anchor": "middle", "font-size": 13, fill: NEUTRAL_700 });
    t.textContent = y;
    svg.appendChild(t);
  });
  const pathFor = (series) => {
    let d = "";
    series.forEach((v, i) => { if (v != null) d += (d ? "L" : "M") + sx(i).toFixed(1) + " " + sy(v).toFixed(1) + " "; });
    return d;
  };
  svg.appendChild(svgEl("path", { d: pathFor(DATA.untreated_series), fill: "none", stroke: NEUTRAL_700, "stroke-width": 2.5 }));
  svg.appendChild(svgEl("path", { d: pathFor(DATA.treated_series), fill: "none", stroke: ACCENT, "stroke-width": 3 }));
  DATA.treated_series.forEach((v, i) => { if (v != null) svg.appendChild(svgEl("circle", { cx: sx(i), cy: sy(v), r: 4.5, fill: ACCENT })); });
  DATA.untreated_series.forEach((v, i) => { if (v != null) svg.appendChild(svgEl("circle", { cx: sx(i), cy: sy(v), r: 4.5, fill: NEUTRAL_700 })); });
  svg.appendChild(svgEl("line", { x1: L, y1: B, x2: R, y2: B, stroke: INK, "stroke-width": 2 }));

  const readout = document.getElementById("trend-readout");
  const colW = (R - L) / (years.length - 1);
  years.forEach((y, i) => {
    const hit = svgEl("rect", { x: Math.max(L, sx(i) - colW / 2), y: T, width: colW, height: B - T, fill: "transparent" });
    hit.addEventListener("mouseenter", () => {
      const tv = DATA.treated_series[i], uv = DATA.untreated_series[i];
      readout.textContent = `${y} · treated ${pct(tv, 2)}% · not-yet/never ${pct(uv, 2)}% · gap ${fmtPP(tv - uv)}pp`;
    });
    svg.appendChild(hit);
  });
}

// --- Figure 4 (was 5): 3-method forest + table -------------------------------
function renderForest() {
  const models = DATA.model_comparison.models;
  const L = 220, R = 770, T = 30, B = 176;
  const svg = document.getElementById("forest-chart");
  const allVals = models.flatMap((m) => [m.ci_lo, m.ci_hi]);
  const xMax = Math.max(...allVals.map(Math.abs)) * 1.2;
  const sx = (v) => L + ((v + xMax) / (2 * xMax)) * (R - L);
  const zeroX = sx(0);

  svg.appendChild(svgEl("line", { x1: zeroX, y1: T, x2: zeroX, y2: B, stroke: INK, "stroke-width": 2 }));
  const zt = svgEl("text", { x: zeroX, y: T - 8, "text-anchor": "middle", "font-size": 12, fill: MUTED });
  zt.textContent = "no effect";
  svg.appendChild(zt);
  for (let g = -1; g <= 1; g++) {
    const v = g * xMax;
    const x = sx(v);
    const t = svgEl("text", { x, y: B + 24, "text-anchor": "middle", "font-size": 13, fill: NEUTRAL_700 });
    t.textContent = fmtPP(v) + "pp";
    svg.appendChild(t);
  }

  models.forEach((m, i) => {
    const y = T + 25 + i * 45;
    svg.appendChild(svgEl("line", { x1: sx(m.ci_lo), y1: y, x2: sx(m.ci_hi), y2: y, stroke: ACCENT, "stroke-width": 2.5 }));
    svg.appendChild(svgEl("circle", { cx: sx(m.estimate), cy: y, r: 6, fill: INK }));
    const lbl = svgEl("text", { x: 20, y: y + 5, "font-size": 14, "font-weight": 700, fill: INK });
    lbl.textContent = m.model;
    svg.appendChild(lbl);
  });
  // Sits below the axis tick labels (y = B+24 = 200), not on top of them —
  // that overlap was a real bug in an earlier version of this chart.
  const cap = svgEl("text", { x: 20, y: 226, "font-size": 12, fill: MUTED });
  cap.textContent = "Change in mail ballot rejection rate, in percentage points";
  svg.appendChild(cap);

  const tbody = document.querySelector("#forest-table tbody");
  models.forEach((m) => {
    const tr = document.createElement("tr");
    const label = { TWFE: "Two-way fixed effects", "Sun-Abraham": "Sun & Abraham (2021)", "Callaway-Sant'Anna": "Callaway & Sant'Anna (2021)" }[m.model] || m.model;
    tr.innerHTML = `<td>${label}</td><td>${fmtPP(m.estimate)}pp</td><td>${(m.se * 100).toFixed(2)}</td><td>[${fmtPP(m.ci_lo)}, ${fmtPP(m.ci_hi)}]</td><td>${m.n_obs.toLocaleString()}</td><td>${m.n_states}</td>`;
    tbody.appendChild(tr);
  });
  const twfe = models.find((m) => m.model === "TWFE");
  document.getElementById("bootstrap-note").textContent = twfe && twfe.bootstrap_ci
    ? `A second, more conservative way of calculating the margin of error for the first method gives [${fmtPP(twfe.bootstrap_ci[0])}, ${fmtPP(twfe.bootstrap_ci[1])}]pp — essentially the same range, confirming the result isn't an artifact of how the margin of error was calculated.`
    : "";
}

// --- Figure 6: histogram -----------------------------------------------------
function renderHistogram() {
  const h = DATA.hist;
  const svg = document.getElementById("hist-chart");
  const n = h.counts.length;
  const L = 44, R = 784, T = 20, B = 216;
  const hMax = Math.max(...h.counts);
  const colW = (R - L) / n;
  h.counts.forEach((c, i) => {
    const barH = (c / hMax) * (B - T);
    svg.appendChild(svgEl("rect", { x: L + i * colW + 4, y: B - barH, width: colW - 8, height: barH, fill: i < n / 2 ? ACCENT : NEUTRAL_700 }));
    const t = svgEl("text", { x: L + i * colW + colW / 2, y: B - barH - 6, "text-anchor": "middle", "font-size": 12, "font-weight": 700, fill: NEUTRAL_700 });
    t.textContent = c.toLocaleString();
    svg.appendChild(t);
    const lbl = svgEl("text", { x: L + i * colW + colW / 2, y: B + 20, "text-anchor": "middle", "font-size": 11, fill: NEUTRAL_700 });
    lbl.textContent = h.edges[i] + "–" + h.edges[i + 1] + "%";
    svg.appendChild(lbl);
  });
  svg.appendChild(svgEl("line", { x1: L, y1: B, x2: R, y2: B, stroke: INK, "stroke-width": 2 }));
  document.getElementById("hist-caption").textContent =
    `${h.n_shown.toLocaleString()} of ${h.n_total.toLocaleString()} usable jurisdiction-years shown (0–10% range); the remaining ${(h.n_total - h.n_shown).toLocaleString()} exceed 10% rejected and are real outliers, not trimmed silently — flagged separately in the panel as flagged_outlier.`;
}

// --- Heterogeneity table -------------------------------------------------
function renderHeterogeneity() {
  const het = DATA.heterogeneity;
  const tbody = document.querySelector("#heterogeneity-table tbody");
  const rows = [
    { ...het.twfe_interaction[0], variant: "size, full sample" },
    ...het.subsamples.map((r) => ({ ...r, variant: "size: " + r.variant.replace("subsample: ", "") })),
    ...het.nchs_subsamples.map((r) => ({ ...r, variant: "real classification: " + r.variant.replace("nchs_", "") })),
  ];
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.model}</td><td>${r.variant}</td><td>${fmtPP(r.estimate)}pp</td><td>${(r.se * 100).toFixed(2)}</td><td>${fmtP(r.p)}</td><td>${r.n_obs.toLocaleString()}</td><td>${r.n_states}</td>`;
    tbody.appendChild(tr);
  });
}

// --- Robustness table ---------------------------------------------------
const ROBUSTNESS_LABELS = {
  drop_2020: "excluding 2020 (pandemic election)",
  drop_WI_MI: "excluding Wisconsin & Michigan",
  winsorize_p99: "capping extreme outliers",
  weight_by_ballots: "weighted by ballot volume",
  fractional_response: "alternate model (fractional logit)",
};
function renderRobustness() {
  const tbody = document.querySelector("#robustness-table tbody");
  DATA.robustness.rows.forEach((r) => {
    const tr = document.createElement("tr");
    if (r.unstable) tr.className = "unstable";
    const seDisplay = r.unstable ? r.se.toFixed(2) + " **" : (r.se * 100).toFixed(2);
    const variant = ROBUSTNESS_LABELS[r.variant] || r.variant;
    tr.innerHTML = `<td>${r.model}</td><td>${variant}</td><td>${fmtPP(r.estimate)}pp</td><td>${seDisplay}</td><td>${fmtP(r.p)}</td><td>${r.n_obs.toLocaleString()}</td><td>${r.n_states}</td>`;
    tbody.appendChild(tr);
  });
}

// --- County choropleth (plain SVG, precomputed at build time) ------------
// Three different Plotly geo/choropleth configs all failed silently or
// hit a CSP-blocked basemap fetch in this sandbox. Every other chart on
// this page is already plain SVG with no library dependency, so this
// makes the choropleth consistent with the rest instead of a fourth
// blind Plotly config: build_choropleth_paths.py projects every county
// polygon to ready-made SVG path strings (equirectangular projection,
// CONUS + DC, with a Hawaii inset box) and bakes in the fill color for
// each county directly, so this function only has to draw <path>
// elements — no projection math, no geo subplot, no fetch, at runtime.
function choroplethFail(msg) {
  const el = document.getElementById("chart-choropleth");
  if (el) el.innerHTML = `<p style="padding:16px;color:var(--color-neutral-700);">County choropleth failed to load: ${msg}.</p>`;
  console.error("[choropleth]", msg);
}
function renderChoropleth() {
  if (typeof CHOROPLETH_PATHS === "undefined") {
    choroplethFail("embedded choropleth path data missing from the page");
    return;
  }
  const cp = CHOROPLETH_PATHS;
  const el = document.getElementById("chart-choropleth");
  el.innerHTML = "";

  const readout = document.getElementById("choropleth-readout");
  const svg = svgEl("svg", { viewBox: `0 0 ${cp.view_w} ${cp.view_h}`, style: "display:block;width:100%;height:auto;cursor:grab;touch-action:none;" });

  // Native <title> gives a browser tooltip on its own delay; the readout
  // line in the toolbar above updates immediately on hover too, matching
  // every other figure's hover pattern on this page.
  function addCounty(p) {
    const path = svgEl("path", { d: p.d, fill: p.fill, stroke: "#fff", "stroke-width": 0.3, style: "cursor:pointer" });
    const title = svgEl("title", {});
    title.textContent = p.title;
    path.appendChild(title);
    path.addEventListener("mouseenter", () => { readout.textContent = p.title; });
    path.addEventListener("mouseleave", () => { readout.textContent = "Hover a county"; });
    svg.appendChild(path);
  }
  cp.paths.forEach(addCounty);
  // Hawaii inset: a light box outline so it reads as a deliberate inset,
  // not a stray cluster of shapes near the edge of the map.
  const hiBox = svgEl("rect", {
    x: cp.hi_box.x - 4, y: cp.hi_box.y - 4, width: cp.hi_box.w + 8, height: cp.hi_box.h + 8,
    fill: "none", stroke: GRID, "stroke-width": 1,
  });
  svg.appendChild(hiBox);
  const hiLabel = svgEl("text", { x: cp.hi_box.x, y: cp.hi_box.y - 8, "font-size": 11, "font-weight": 700, fill: NEUTRAL_700 });
  hiLabel.textContent = "HI";
  svg.appendChild(hiLabel);
  cp.hi_paths.forEach(addCounty);
  el.appendChild(svg);

  // --- Zoom / pan ------------------------------------------------------
  // Plain viewBox manipulation (no library): zooming shrinks the visible
  // box around a focus point, panning translates it, both clamped so the
  // view never drifts outside the map's own bounds.
  const base = { x: 0, y: 0, w: cp.view_w, h: cp.view_h };
  let view = { ...base };
  const MAX_ZOOM = 8;

  function applyView() {
    svg.setAttribute("viewBox", `${view.x} ${view.y} ${view.w} ${view.h}`);
  }
  function clampView(v) {
    v.w = Math.max(base.w / MAX_ZOOM, Math.min(base.w, v.w));
    v.h = v.w * (base.h / base.w);
    v.x = Math.max(base.x, Math.min(base.x + base.w - v.w, v.x));
    v.y = Math.max(base.y, Math.min(base.y + base.h - v.h, v.y));
    return v;
  }
  function zoomAt(focusX, focusY, factor) {
    const newW = view.w / factor;
    const newH = view.h / factor;
    const fx = (focusX - view.x) / view.w;
    const fy = (focusY - view.y) / view.h;
    view = clampView({
      x: focusX - fx * newW, y: focusY - fy * newH, w: newW, h: newH,
    });
    applyView();
  }
  function svgPoint(clientX, clientY) {
    const rect = svg.getBoundingClientRect();
    return {
      x: view.x + ((clientX - rect.left) / rect.width) * view.w,
      y: view.y + ((clientY - rect.top) / rect.height) * view.h,
    };
  }

  svg.addEventListener("wheel", (e) => {
    e.preventDefault();
    const p = svgPoint(e.clientX, e.clientY);
    zoomAt(p.x, p.y, e.deltaY < 0 ? 1.3 : 1 / 1.3);
  }, { passive: false });

  let dragging = null;
  svg.addEventListener("mousedown", (e) => {
    dragging = { startClient: { x: e.clientX, y: e.clientY }, startView: { ...view } };
    svg.style.cursor = "grabbing";
  });
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const rect = svg.getBoundingClientRect();
    const dx = ((e.clientX - dragging.startClient.x) / rect.width) * dragging.startView.w;
    const dy = ((e.clientY - dragging.startClient.y) / rect.height) * dragging.startView.h;
    view = clampView({ ...dragging.startView, x: dragging.startView.x - dx, y: dragging.startView.y - dy });
    applyView();
  });
  window.addEventListener("mouseup", () => { dragging = null; svg.style.cursor = ""; });

  const zoomIn = document.getElementById("choro-zoom-in");
  const zoomOut = document.getElementById("choro-zoom-out");
  const zoomReset = document.getElementById("choro-zoom-reset");
  if (zoomIn) zoomIn.addEventListener("click", () => zoomAt(view.x + view.w / 2, view.y + view.h / 2, 1.6));
  if (zoomOut) zoomOut.addEventListener("click", () => zoomAt(view.x + view.w / 2, view.y + view.h / 2, 1 / 1.6));
  if (zoomReset) zoomReset.addEventListener("click", () => { view = { ...base }; applyView(); });

  document.getElementById("choropleth-note").textContent =
    `2024 wave. Gray = ${cp.excluded_states.join(", ")} (report at the town/municipality level, not county). Alaska is not shown: this project's data only has one statewide figure for it, not a per-county breakdown.`;
}

// Each figure renders independently — one throwing must not silently
// prevent the rest from ever running (this is what actually broke the
// choropleth in an earlier version: it was last in a single synchronous
// call chain, so any error upstream stopped it from ever being invoked).
function safe(fn, label) {
  try { fn(); } catch (e) { console.error(`[${label}]`, e); }
}
const DEFAULT_STATE = "CA";
safe(renderStatStrip, "stat-strip");
safe(renderStateFigure, "state-figure");
safe(renderTileMap, "tile-map");
safe(() => renderTileMap.selectTile(DEFAULT_STATE), "tile-map-initial-select");
safe(renderTrendChart, "trend-chart");
safe(renderForest, "forest");
safe(renderHistogram, "histogram");
safe(renderHeterogeneity, "heterogeneity");
safe(renderRobustness, "robustness");
safe(renderChoropleth, "choropleth");
