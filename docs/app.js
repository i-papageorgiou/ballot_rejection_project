// app.js — fetches the static JSON data files (written by src/07_figures.py
// and src/06_estimate.R) and renders every chart on the page. No build
// step; Plotly is loaded via CDN in index.html.

const PLOTLY_CONFIG = { responsive: true, displaylogo: false };
const isDark = () => window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
const textColor = () => (isDark() ? "#eaeaea" : "#1a1a1a");
const gridColor = () => (isDark() ? "#33363c" : "#e0e0e0");

function baseLayout(extra) {
  return Object.assign({
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { color: textColor() },
    margin: { t: 30, r: 20, b: 50, l: 60 },
    xaxis: { gridcolor: gridColor(), zerolinecolor: gridColor() },
    yaxis: { gridcolor: gridColor(), zerolinecolor: gridColor() },
  }, extra);
}

async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return res.json();
}

function fmtPct(x) { return (x * 100).toFixed(3) + "%"; }
function fmtP(p) { return p < 0.001 ? "<0.001" : p.toFixed(4); }

// --- Headline + coefficient comparison ------------------------------------
async function renderModelComparison() {
  const data = await fetchJSON("data/model_comparison.json");
  document.getElementById("headline-text").textContent = data.headline;

  const models = data.models;
  const y = models.map(m => m.model);
  const x = models.map(m => m.estimate);
  const errPlus = models.map(m => m.ci_hi - m.estimate);
  const errMinus = models.map(m => m.estimate - m.ci_lo);

  const traces = [{
    type: "scatter", mode: "markers",
    x, y,
    error_x: { type: "data", array: errPlus, arrayminus: errMinus, color: "#2b5797" },
    marker: { size: 12, color: "#2b5797" },
    name: "Point estimate (analytic 95% CI)",
  }];

  // Add TWFE's bootstrap CI as a second, offset marker for comparison.
  const twfe = models.find(m => m.model === "TWFE");
  if (twfe && twfe.bootstrap_ci) {
    traces.push({
      type: "scatter", mode: "markers",
      x: [twfe.estimate], y: ["TWFE (wild-cluster bootstrap)"],
      error_x: {
        type: "data",
        array: [twfe.bootstrap_ci[1] - twfe.estimate],
        arrayminus: [twfe.estimate - twfe.bootstrap_ci[0]],
        color: "#a33",
      },
      marker: { size: 12, color: "#a33", symbol: "diamond" },
      name: "TWFE, bootstrap CI",
    });
  }

  Plotly.newPlot("chart-coefficients", traces, baseLayout({
    xaxis: { title: "Effect on rejection rate", gridcolor: gridColor(), zeroline: true, zerolinewidth: 2, zerolinecolor: "#999" },
    yaxis: { automargin: true },
    showlegend: false,
  }), PLOTLY_CONFIG);
}

// --- Event study -----------------------------------------------------------
async function renderEventStudy() {
  const data = await fetchJSON("data/event_study.json");
  const ev = data.events;

  const trace = {
    type: "scatter", mode: "lines+markers",
    x: ev.map(e => e.event_time),
    y: ev.map(e => e.estimate),
    marker: { color: ev.map(e => (e.significant ? "#d94848" : "#2b5797")), size: 10 },
    line: { color: "#2b5797" },
    error_y: {
      type: "data",
      symmetric: false,
      array: ev.map(e => e.band_hi - e.estimate),
      arrayminus: ev.map(e => e.estimate - e.band_lo),
      color: "#999",
    },
    name: "ATT by event time",
  };

  Plotly.newPlot("chart-eventstudy", [trace], baseLayout({
    xaxis: { title: "Years relative to adoption", gridcolor: gridColor(), zeroline: true },
    yaxis: { title: "Effect on rejection rate", zeroline: true, zerolinewidth: 2, zerolinecolor: "#999" },
  }), PLOTLY_CONFIG);

  const box = document.getElementById("pretrend-caveat");
  const pt = data.pretrend_diagnosis;
  if (pt) {
    const states = (pt.driving_cell && pt.driving_cell.states) ? pt.driving_cell.states.join(", ") : "";
    box.innerHTML = `<strong>Pre-trend, diagnosed (red point above, event-time ${pt.flagged_event_time}):</strong> ` +
      `Traces to one group-time cell (states: ${escapeHtml(states)}). ${escapeHtml(pt.explanation || "")}`;
  } else {
    box.textContent = "No pre-trend diagnosis available in this data.";
  }
}

// --- Rejection-rate distribution by state ----------------------------------
let STATE_DIST = null;
function renderStateDist(year) {
  const rows = STATE_DIST.rows.filter(r => r.year === year).sort((a, b) => b.median - a.median);
  const trace = {
    type: "bar",
    x: rows.map(r => r.state),
    y: rows.map(r => r.median),
    marker: { color: "#2b5797" },
    error_y: {
      type: "data",
      symmetric: false,
      array: rows.map(r => r.p75 - r.median),
      arrayminus: rows.map(r => r.median - r.p25),
      color: "#999", thickness: 1,
    },
    text: rows.map(r => `n=${r.n}`),
    hovertemplate: "%{x}: %{y:.3%} (%{text})<extra></extra>",
  };
  Plotly.newPlot("chart-statedist", [trace], baseLayout({
    xaxis: { title: "State (sorted by median rejection rate)", tickangle: -90, gridcolor: gridColor() },
    yaxis: { title: "Median rejection rate", tickformat: ".2%" },
  }), PLOTLY_CONFIG);
}

async function renderStateDistSection() {
  STATE_DIST = await fetchJSON("data/state_distribution.json");
  const sel = document.getElementById("wave-select");
  STATE_DIST.waves.forEach(w => {
    const opt = document.createElement("option");
    opt.value = w; opt.textContent = w;
    sel.appendChild(opt);
  });
  sel.value = STATE_DIST.waves[STATE_DIST.waves.length - 1];
  sel.addEventListener("change", () => renderStateDist(Number(sel.value)));
  renderStateDist(Number(sel.value));
}

// --- County choropleth -------------------------------------------------------
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
      "<p style='color:var(--muted)'>County boundary data failed to load (no network access?) — the underlying values are still in docs/data/county_choropleth.json.</p>";
    return;
  }

  const trace = {
    type: "choropleth",
    geojson,
    locations: data.counties.map(c => c.fips),
    z: data.counties.map(c => c.rejection_rate),
    text: data.counties.map(c => `${c.name}, ${c.state}: ${fmtPct(c.rejection_rate)}`),
    hoverinfo: "text",
    colorscale: "Reds",
    marker: { line: { width: 0.2, color: "#888" } },
    colorbar: { title: "Rejection rate", tickformat: ".1%" },
  };

  Plotly.newPlot("chart-choropleth", [trace], baseLayout({
    geo: {
      scope: "usa",
      bgcolor: "rgba(0,0,0,0)",
      lakecolor: isDark() ? "#16181c" : "#fafafa",
      landcolor: isDark() ? "#2a2d33" : "#eeeeee",
    },
  }), PLOTLY_CONFIG);
}

// --- Heterogeneity table -----------------------------------------------------
async function renderHeterogeneity() {
  const data = await fetchJSON("data/heterogeneity.json");
  const tbody = document.querySelector("#table-heterogeneity tbody");
  const rows = [
    { model: "TWFE", subsample: "interaction (full sample)", ...data.twfe_interaction },
    ...data.subsamples,
  ];
  rows.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.model}</td><td>${r.subsample}</td><td>${fmtPct(r.estimate)}</td><td>${fmtPct(r.se)}</td><td>${fmtP(r.p)}</td><td>${r.n_obs.toLocaleString()}</td><td>${r.n_states}</td>`;
    tbody.appendChild(tr);
  });
  document.getElementById("heterogeneity-caveat").innerHTML =
    `<strong>Diagnosed, not resolved:</strong> ${escapeHtml(data.diagnosis)}`;
}

// --- Robustness table --------------------------------------------------------
async function renderRobustness() {
  const data = await fetchJSON("data/robustness.json");
  const tbody = document.querySelector("#table-robustness tbody");
  data.rows.forEach(r => {
    const tr = document.createElement("tr");
    if (r.unstable) tr.className = "unstable";
    const seDisplay = r.unstable ? `${r.se.toFixed(2)} **` : fmtPct(r.se);
    tr.innerHTML = `<td>${r.model}</td><td>${r.variant}</td><td>${fmtPct(r.estimate)}</td><td>${seDisplay}</td><td>${fmtP(r.p)}</td><td>${r.n_obs.toLocaleString()}</td><td>${r.n_states}</td>`;
    tbody.appendChild(tr);
  });
  document.getElementById("robustness-note").textContent =
    (data.unstable_note ? "** " + data.unstable_note + " " : "") + (data.summary || "");
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

// --- Boot --------------------------------------------------------------------
Promise.all([
  renderModelComparison(),
  renderEventStudy(),
  renderStateDistSection(),
  renderChoropleth(),
  renderHeterogeneity(),
  renderRobustness(),
]).catch(err => {
  console.error(err);
  document.querySelector(".wrap").insertAdjacentHTML(
    "afterbegin",
    `<div class="caveat-box"><strong>Something failed to load:</strong> ${escapeHtml(err.message)}. Check the browser console for detail.</div>`
  );
});
