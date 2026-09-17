// app.js — fetches the static JSON data files (written by src/06_estimate.R
// and src/07_figures.py) and renders every figure on the page. No build
// step, no framework: hand-rolled SVG for the numeric charts (matching the
// project's design mockup, output/Mockup-website/, gitignored — not
// published) and Plotly (via CDN) only for the county choropleth, where a
// real geographic map isn't practical to hand-roll.

const SVG_NS = "http://www.w3.org/2000/svg";

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return res.json();
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

const fmtPP = (x) => (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x * 100).toFixed(2);
const fmtP = (p) => (p < 0.001 ? "<0.001" : p.toFixed(4));
const fmtN = (n) => Number(n).toLocaleString();
const fmtPct1 = (x) => (x * 100).toFixed(2) + "%";

function el(tag, attrs, children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const k in attrs) node.setAttribute(k, attrs[k]);
  (children || []).forEach((c) => node.appendChild(c));
  return node;
}
function text(x, y, str, attrs) {
  const t = el("text", Object.assign({ x, y }, attrs));
  t.textContent = str;
  return t;
}

// --- Headline stat grid -----------------------------------------------------
async function renderStatGrid() {
  const data = await fetchJSON("data/model_comparison.json");
  const models = data.models;
  const cs = models.find((m) => m.model === "Callaway-Sant'Anna") || models[models.length - 1];
  const twfe = models.find((m) => m.model === "TWFE") || models[0];
  const sig = models.filter((m) => m.p < 0.05).length;

  let sigNote;
  if (sig === 0) sigNote = "Every 95% interval below includes zero.";
  else if (sig === models.length) sigNote = "All estimators reach significance.";
  else sigNote = `${sig} of ${models.length} intervals exclude zero.`;

  const tiles = [
    { value: String(models.length), label: "Independent estimators", note: models.map((m) => m.model).join(", ") + "." },
    { value: `${sig} / ${models.length}`, label: "Reach p < 0.05", note: sigNote },
    { value: fmtPP(cs.estimate), label: "Callaway–Sant'Anna estimate, pp", note: `95% CI ${fmtPP(cs.ci_lo)} to ${fmtPP(cs.ci_hi)} pp.` },
    { value: fmtN(twfe.n_obs), label: "Jurisdiction-years (TWFE sample)", note: `${twfe.n_states} states, six EAVS waves, 2014–2024.` },
  ];

  const grid = document.getElementById("stat-grid");
  grid.innerHTML = "";
  tiles.forEach((t) => {
    const div = document.createElement("div");
    div.className = "stat-tile";
    div.innerHTML = `<div class="value">${escapeHtml(t.value)}</div><div class="label">${escapeHtml(t.label)}</div><div class="note">${escapeHtml(t.note)}</div>`;
    grid.appendChild(div);
  });

  return data;
}

// --- Figure 1: coefficient comparison (forest plot + table) -----------------
function renderCoefficientsChart(models) {
  const rows = [];
  models.forEach((m) => rows.push({ name: m.model, est: m.estimate, lo: m.ci_lo, hi: m.ci_hi }));
  const twfe = models.find((m) => m.model === "TWFE");
  if (twfe && twfe.bootstrap_ci) {
    rows.push({ name: "TWFE (bootstrap CI)", est: twfe.estimate, lo: twfe.bootstrap_ci[0], hi: twfe.bootstrap_ci[1] });
  }

  const L = 260, R = 770, T = 20, B = 190;
  const allVals = rows.flatMap((r) => [r.lo, r.hi]).concat([0]);
  let dMin = Math.min(...allVals), dMax = Math.max(...allVals);
  const pad = (dMax - dMin) * 0.2 || 0.001;
  dMin -= pad; dMax += pad;
  const sx = (v) => L + ((v - dMin) / (dMax - dMin)) * (R - L);

  const svg = document.getElementById("chart-coefficients");
  svg.innerHTML = "";
  const accent = cssVar("--accent");
  const textCol = cssVar("--text");
  const neutral = cssVar("--neutral-300");

  svg.appendChild(el("line", { x1: sx(0), y1: T, x2: sx(0), y2: B, stroke: textCol, "stroke-width": 2 }));
  svg.appendChild(text(sx(0), 14, "no effect", { "text-anchor": "middle", "font-size": 12, fill: cssVar("--neutral-700") }));

  const rowH = (B - T) / (rows.length + 1);
  rows.forEach((r, i) => {
    const y = T + rowH * (i + 1);
    const line = el("line", { x1: sx(r.lo), y1: y, x2: sx(r.hi), y2: y, stroke: accent, "stroke-width": 2.5 });
    const dot = el("circle", { cx: sx(r.est), cy: y, r: 6, fill: textCol });
    const title = document.createElementNS(SVG_NS, "title");
    title.textContent = `${r.name}: ${fmtPP(r.est)} pp (95% CI ${fmtPP(r.lo)} to ${fmtPP(r.hi)} pp)`;
    dot.appendChild(title);
    svg.appendChild(line);
    svg.appendChild(dot);
    svg.appendChild(text(20, y + 5, r.name, { "font-size": 14, "font-weight": 700, fill: textCol }));
  });

  for (let i = 0; i <= 4; i++) {
    const v = dMin + (i / 4) * (dMax - dMin);
    const x = sx(v);
    svg.appendChild(text(x, 212, fmtPP(v), { "text-anchor": "middle", "font-size": 12, fill: cssVar("--neutral-700") }));
  }
  svg.appendChild(text(L, 228, "Percentage-point change in mail ballot rejection rate", { "font-size": 12, fill: cssVar("--neutral-700") }));
}

function renderCoefficientsTable(data) {
  const tbody = document.querySelector("#table-coefficients tbody");
  tbody.innerHTML = "";
  const addRow = (name, est, se, lo, hi, p, nObs, nStates) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${escapeHtml(name)}</td><td>${fmtPP(est)}</td><td>${(se * 100).toFixed(2)}</td><td>[${fmtPP(lo)}, ${fmtPP(hi)}]</td><td>${fmtP(p)}</td><td>${fmtN(nObs)}</td><td>${nStates}</td>`;
    tbody.appendChild(tr);
  };
  data.models.forEach((m) => addRow(m.model, m.estimate, m.se, m.ci_lo, m.ci_hi, m.p, m.n_obs, m.n_states));
  const twfe = data.models.find((m) => m.model === "TWFE");
  if (twfe && twfe.bootstrap_ci) {
    addRow("TWFE (wild-cluster bootstrap)", twfe.estimate, NaN, twfe.bootstrap_ci[0], twfe.bootstrap_ci[1], twfe.bootstrap_p, twfe.n_obs, twfe.n_states);
    tbody.lastChild.children[2].textContent = "—";
  }
  document.getElementById("coefficients-caption").textContent =
    `Outcome: ${data.outcome}. TWFE clusters standard errors by state; its bootstrap row uses a wild-cluster bootstrap (999 replications) instead of the analytic CI.`;
}

// --- Figure 2: event study ----------------------------------------------------
function renderEventStudy(data) {
  const ev = data.events;
  const L = 58, R = 784, T = 30, B = 250;
  const xs = ev.map((e) => e.event_time);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const sx = (t) => L + ((t - xMin) / (xMax - xMin)) * (R - L);

  const yVals = ev.flatMap((e) => [e.band_lo, e.band_hi]).concat([0]);
  let yMin = Math.min(...yVals), yMax = Math.max(...yVals);
  const pad = (yMax - yMin) * 0.15 || 0.001;
  yMin -= pad; yMax += pad;
  const sy = (v) => T + (1 - (v - yMin) / (yMax - yMin)) * (B - T);

  const svg = document.getElementById("chart-eventstudy");
  svg.innerHTML = "";
  const textCol = cssVar("--text");
  const neutral700 = cssVar("--neutral-700");
  const neutral300 = cssVar("--neutral-300");
  const accent = cssVar("--accent");

  for (let i = 0; i <= 4; i++) {
    const v = yMin + (i / 4) * (yMax - yMin);
    const y = sy(v);
    svg.appendChild(el("line", { x1: L, y1: y, x2: R, y2: y, stroke: neutral300, "stroke-width": 1 }));
    svg.appendChild(text(L - 8, y + 4, fmtPP(v), { "text-anchor": "end", "font-size": 12, fill: neutral700 }));
  }
  svg.appendChild(el("line", { x1: L, y1: sy(0), x2: R, y2: sy(0), stroke: textCol, "stroke-width": 2 }));
  const zeroX = sx(0);
  if (xMin <= 0 && xMax >= 0) {
    svg.appendChild(el("line", { x1: zeroX, y1: T, x2: zeroX, y2: B, stroke: neutral700, "stroke-width": 2, "stroke-dasharray": "6 5" }));
    svg.appendChild(text(zeroX, T - 10, "adoption", { "text-anchor": "middle", "font-size": 12, fill: neutral700 }));
  }

  const readout = document.getElementById("es-readout");
  const colW = ev.length > 1 ? (sx(xs[1]) - sx(xs[0])) : 40;

  ev.forEach((e) => {
    const x = sx(e.event_time);
    const color = e.significant ? accent : neutral700;
    svg.appendChild(el("line", { x1: x, y1: sy(e.band_lo), x2: x, y2: sy(e.band_hi), stroke: color, "stroke-width": 2 }));
    const dot = el("circle", { cx: x, cy: sy(e.estimate), r: 4.5, fill: e.significant ? accent : textCol });
    dot.dataset.baseR = "4.5";
    svg.appendChild(dot);
    svg.appendChild(text(x, 270, (e.event_time > 0 ? "+" : "") + e.event_time, { "text-anchor": "middle", "font-size": 12, fill: neutral700 }));

    const hit = el("rect", { x: x - colW / 2, y: T, width: colW, height: B - T, fill: "transparent", style: "cursor:pointer" });
    hit.addEventListener("mouseenter", () => {
      dot.setAttribute("r", 7);
      readout.textContent = `Event ${e.event_time > 0 ? "+" + e.event_time : e.event_time} · ${fmtPP(e.estimate)} pp · SE ${(e.se * 100).toFixed(2)} · CI [${fmtPP(e.band_lo)}, ${fmtPP(e.band_hi)}] pp`;
    });
    hit.addEventListener("mouseleave", () => {
      dot.setAttribute("r", dot.dataset.baseR);
      readout.textContent = "Hover for exact values";
    });
    svg.appendChild(hit);
  });

  svg.appendChild(text(L, 290, "Elections relative to adoption · red = simultaneous 95% band excludes zero", { "font-size": 12, fill: neutral700 }));

  const box = document.getElementById("pretrend-caveat");
  const overall = `<strong>Overall ATT (event-study aggregation):</strong> ${fmtPP(data.overall.estimate)} pp (SE ${(data.overall.se * 100).toFixed(2)}).`;
  const pt = data.pretrend_diagnosis;
  if (pt) {
    const states = (pt.driving_cell && pt.driving_cell.states) ? pt.driving_cell.states.join(", ") : "";
    box.innerHTML = `${overall} <strong>Pre-trend, diagnosed (event-time ${pt.flagged_event_time}):</strong> traces to one group-time cell (states: ${escapeHtml(states)}). ${escapeHtml(pt.explanation || "")}`;
  } else {
    box.innerHTML = `${overall} No pre-treatment event-time's simultaneous confidence band excludes zero in this run — no pre-trend violation detected.`;
  }
}

// --- Figure 3: rejection-rate distribution by state --------------------------
let STATE_DIST = null;

function renderStateDist(year) {
  const rows = STATE_DIST.rows.filter((r) => r.year === year).sort((a, b) => b.median - a.median);
  const L = 50, R = 780, T = 20, B = 340;
  const yMax = Math.max(...rows.map((r) => r.p75)) * 1.1 || 0.01;
  const sy = (v) => T + (1 - v / yMax) * (B - T);
  const barW = (R - L) / rows.length;

  const svg = document.getElementById("chart-statedist");
  svg.innerHTML = "";
  const accent = cssVar("--accent");
  const textCol = cssVar("--text");
  const neutral700 = cssVar("--neutral-700");
  const neutral300 = cssVar("--neutral-300");

  for (let i = 0; i <= 4; i++) {
    const v = (i / 4) * yMax;
    const y = sy(v);
    svg.appendChild(el("line", { x1: L, y1: y, x2: R, y2: y, stroke: neutral300, "stroke-width": 1 }));
    svg.appendChild(text(L - 8, y + 4, (v * 100).toFixed(1) + "%", { "text-anchor": "end", "font-size": 11, fill: neutral700 }));
  }

  const readout = document.getElementById("statedist-readout");
  rows.forEach((r, i) => {
    const x = L + i * barW + 1;
    const w = Math.max(barW - 2, 1);
    const y = sy(r.median);
    const barRect = el("rect", { x, y, width: w, height: B - y, fill: accent });
    const cx = x + w / 2;
    const errLine = el("line", { x1: cx, y1: sy(r.p75), x2: cx, y2: sy(r.p25), stroke: neutral700, "stroke-width": 1 });
    svg.appendChild(barRect);
    svg.appendChild(errLine);
    svg.appendChild(text(cx, B + 10, r.state, {
      "text-anchor": "end", "font-size": 10, fill: neutral700,
      transform: `rotate(-90 ${cx} ${B + 10})`,
    }));

    const hit = el("rect", { x, y: T, width: w, height: B - T, fill: "transparent", style: "cursor:pointer" });
    hit.addEventListener("mouseenter", () => {
      readout.textContent = `${r.state}, ${year} · median ${fmtPct1(r.median)} (IQR ${fmtPct1(r.p25)}–${fmtPct1(r.p75)}) · n=${r.n}`;
    });
    hit.addEventListener("mouseleave", () => { readout.textContent = "Hover a bar for exact values"; });
    svg.appendChild(hit);
  });

  svg.appendChild(el("line", { x1: L, y1: B, x2: R, y2: B, stroke: textCol, "stroke-width": 2 }));
}

async function renderStateDistSection() {
  STATE_DIST = await fetchJSON("data/state_distribution.json");
  const picker = document.getElementById("wave-picker");
  const latest = STATE_DIST.waves[STATE_DIST.waves.length - 1];
  STATE_DIST.waves.forEach((w) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = String(w);
    if (w === latest) btn.classList.add("active");
    btn.addEventListener("click", () => {
      picker.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      renderStateDist(w);
    });
    picker.appendChild(btn);
  });
  renderStateDist(latest);
}

// --- Figure 4: county choropleth ----------------------------------------------
async function renderChoropleth() {
  const data = await fetchJSON("data/county_choropleth.json");
  document.getElementById("choropleth-note").textContent =
    `Wave ${data.wave}. Gray = ${data.excluded_states.join(", ")} (${data.excluded_reason})`;

  const geoUrl = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json";
  let geojson;
  try {
    geojson = await fetchJSON(geoUrl);
  } catch (e) {
    document.getElementById("chart-choropleth").innerHTML =
      "<p style='padding:20px;color:var(--neutral-700)'>County boundary data failed to load (no network access?) — the underlying values are still in docs/data/county_choropleth.json.</p>";
    return;
  }

  const trace = {
    type: "choropleth",
    geojson,
    locations: data.counties.map((c) => c.fips),
    z: data.counties.map((c) => c.rejection_rate),
    text: data.counties.map((c) => `${c.name}, ${c.state}: ${fmtPct1(c.rejection_rate)}`),
    hoverinfo: "text",
    colorscale: "Reds",
    marker: { line: { width: 0.2, color: "#888" } },
    colorbar: { title: "Rejection rate", tickformat: ".1%" },
  };

  Plotly.newPlot("chart-choropleth", [trace], {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { color: cssVar("--text"), family: cssVar("--font-body") },
    margin: { t: 10, r: 10, b: 10, l: 10 },
    geo: {
      scope: "usa",
      bgcolor: "rgba(0,0,0,0)",
      lakecolor: cssVar("--bg"),
      landcolor: cssVar("--panel"),
    },
  }, { responsive: true, displaylogo: false });
}

// --- Heterogeneity table -------------------------------------------------------
async function renderHeterogeneity() {
  const data = await fetchJSON("data/heterogeneity.json");
  const label = (v) => ({
    "interaction: treated x log_ballots": "Interaction (full sample)",
    "subsample: large": "Tercile: large",
    "subsample: small": "Tercile: small",
    "nchs_urban": "NCHS: urban",
    "nchs_rural": "NCHS: rural",
  }[v] || v);

  const rows = [
    { model: "TWFE", ...data.twfe_interaction[0] },
    ...data.subsamples,
    ...(data.nchs_subsamples || []),
  ];
  const tbody = document.querySelector("#table-heterogeneity tbody");
  tbody.innerHTML = "";
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${escapeHtml(r.model)}</td><td>${escapeHtml(label(r.variant))}</td><td>${fmtPP(r.estimate)}</td><td>${(r.se * 100).toFixed(2)}</td><td>${fmtP(r.p)}</td><td>${fmtN(r.n_obs)}</td><td>${r.n_states}</td>`;
    tbody.appendChild(tr);
  });

  const note = document.getElementById("heterogeneity-note");
  note.classList.remove("loading");
  const agreement = (data.nchs_agreement_note || "").replace(/ \| /g, "<br>");
  note.innerHTML =
    (agreement ? `<p style="margin:0 0 14px;">${agreement}</p>` : "") +
    `<p style="margin:0; font-size:13px;">${escapeHtml(data.nchs_coverage_note || "")}</p>`;
}

// --- Robustness table -----------------------------------------------------------
async function renderRobustness() {
  const data = await fetchJSON("data/robustness.json");
  const label = (v) => ({
    drop_2020: "Drop 2020",
    drop_WI_MI: "Drop WI, MI",
    winsorize_p99: "Winsorize at p99",
    weight_by_ballots: "Weight by ballots",
    fractional_response: "Fractional-response GLM",
  }[v] || v);

  const tbody = document.querySelector("#table-robustness tbody");
  tbody.innerHTML = "";
  data.rows.forEach((r) => {
    const tr = document.createElement("tr");
    if (r.unstable) tr.className = "unstable";
    const seDisplay = r.unstable ? `${r.se.toFixed(2)} **` : (r.se * 100).toFixed(2);
    const pDisplay = r.unstable ? `${fmtP(r.p)} **` : fmtP(r.p);
    tr.innerHTML = `<td>${escapeHtml(r.model)}</td><td>${escapeHtml(label(r.variant))}</td><td>${fmtPP(r.estimate)}</td><td>${seDisplay}</td><td>${pDisplay}</td><td>${fmtN(r.n_obs)}</td><td>${r.n_states}</td>`;
    tbody.appendChild(tr);
  });
}

// --- Boot ------------------------------------------------------------------------
(async function boot() {
  try {
    const modelData = await renderStatGrid();
    renderCoefficientsChart(modelData.models);
    renderCoefficientsTable(modelData);

    const esData = await fetchJSON("data/event_study.json");
    renderEventStudy(esData);

    await Promise.all([
      renderStateDistSection(),
      renderChoropleth(),
      renderHeterogeneity(),
      renderRobustness(),
    ]);
  } catch (err) {
    console.error(err);
    document.querySelector(".wrap").insertAdjacentHTML(
      "afterbegin",
      `<div class="caveat-box"><strong>Something failed to load:</strong> ${escapeHtml(err.message)}. Check the browser console for detail.</div>`
    );
  }
})();
