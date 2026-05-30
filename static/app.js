const state = {
  runs: [],
  selectedRunId: null,
};

const elements = {
  modelFilter: document.querySelector("#modelFilter"),
  statusFilter: document.querySelector("#statusFilter"),
  accuracyFilter: document.querySelector("#accuracyFilter"),
  refreshButton: document.querySelector("#refreshButton"),
  runRows: document.querySelector("#runRows"),
  totalRuns: document.querySelector("#totalRuns"),
  successfulRuns: document.querySelector("#successfulRuns"),
  avgAccuracy: document.querySelector("#avgAccuracy"),
  totalCost: document.querySelector("#totalCost"),
  detailTitle: document.querySelector("#detailTitle"),
  detailNotes: document.querySelector("#detailNotes"),
  metricBars: document.querySelector("#metricBars"),
  datasetDetail: document.querySelector("#datasetDetail"),
  eventList: document.querySelector("#eventList"),
  lineageList: document.querySelector("#lineageList"),
};

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatMoney(value) {
  return `$${Number(value).toFixed(2)}`;
}

function setMetricSummary(summary) {
  elements.totalRuns.textContent = summary.total_runs;
  elements.successfulRuns.textContent = summary.successful_runs;
  elements.avgAccuracy.textContent = formatPercent(summary.avg_accuracy);
  elements.totalCost.textContent = formatMoney(summary.total_cost_usd);
}

function populateModels(runs) {
  const current = elements.modelFilter.value;
  const models = [...new Set(runs.map((run) => run.model))].sort();
  elements.modelFilter.innerHTML = '<option value="">All models</option>';
  for (const model of models) {
    const option = document.createElement("option");
    option.value = model;
    option.textContent = model;
    elements.modelFilter.append(option);
  }
  elements.modelFilter.value = models.includes(current) ? current : "";
}

function renderRuns(runs) {
  elements.runRows.innerHTML = "";
  for (const run of runs) {
    const row = document.createElement("tr");
    row.className = run.run_id === state.selectedRunId ? "selected" : "";
    row.innerHTML = `
      <td><div class="runId">${run.run_id}</div><div>${run.task}</div></td>
      <td>${run.model}</td>
      <td>${run.dataset_id}:${run.dataset_version}</td>
      <td><span class="status ${run.status === "failed" ? "failed" : ""}">${run.status}</span></td>
      <td>${formatPercent(run.eval_accuracy)}</td>
      <td>${formatMoney(run.cost_usd)}</td>
    `;
    row.addEventListener("click", () => selectRun(run.run_id));
    elements.runRows.append(row);
  }
}

function bar(label, value) {
  const width = Math.max(0, Math.min(100, value * 100));
  const wrapper = document.createElement("div");
  wrapper.innerHTML = `
    <div class="barLabel"><span>${label}</span><span>${formatPercent(value)}</span></div>
    <div class="barTrack"><div class="barFill" style="width: ${width}%"></div></div>
  `;
  return wrapper;
}

function renderDetail(detail) {
  const { run, dataset, events, lineage } = detail;
  elements.detailTitle.textContent = run.run_id;
  elements.detailNotes.textContent = run.notes;
  elements.metricBars.innerHTML = "";
  elements.metricBars.append(
    bar("Accuracy", run.eval_accuracy),
    bar("Helpfulness", run.eval_helpfulness),
    bar("Harmlessness", run.eval_harmlessness),
  );

  elements.datasetDetail.innerHTML = "";
  const datasetRows = [
    ["Dataset", `${dataset.dataset_id}:${dataset.version}`],
    ["Rows", dataset.row_count.toLocaleString()],
    ["Source", dataset.source],
    ["SHA", dataset.content_sha],
    ["Parent", dataset.parent_dataset_id || "none"],
    ["Transform", dataset.transform],
    ["Risk", dataset.risk_level],
  ];
  for (const [term, description] of datasetRows) {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = term;
    dd.textContent = description;
    elements.datasetDetail.append(dt, dd);
  }

  elements.eventList.innerHTML = "";
  for (const event of events) {
    const li = document.createElement("li");
    const metric = event.metric_name ? ` (${event.metric_name}: ${event.metric_value})` : "";
    li.textContent = `${event.stage}: ${event.message}${metric}`;
    elements.eventList.append(li);
  }

  elements.lineageList.innerHTML = "";
  for (const edge of lineage) {
    const li = document.createElement("li");
    li.textContent = `${edge.upstream} -> ${edge.downstream} [${edge.relation}]: ${edge.evidence}`;
    elements.lineageList.append(li);
  }
}

async function selectRun(runId) {
  state.selectedRunId = runId;
  renderRuns(state.runs);
  const detail = await fetchJson(`/api/runs/${encodeURIComponent(runId)}`);
  renderDetail(detail);
}

function currentQuery() {
  const params = new URLSearchParams();
  if (elements.modelFilter.value) params.set("model", elements.modelFilter.value);
  if (elements.statusFilter.value) params.set("status", elements.statusFilter.value);
  if (elements.accuracyFilter.value) params.set("min_accuracy", elements.accuracyFilter.value);
  const query = params.toString();
  return query ? `?${query}` : "";
}

async function refresh() {
  const [runs, summary] = await Promise.all([
    fetchJson(`/api/runs${currentQuery()}`),
    fetchJson("/api/metrics/summary"),
  ]);
  state.runs = runs;
  populateModels(runs);
  setMetricSummary(summary);
  renderRuns(runs);
  if (runs.length > 0) {
    await selectRun(state.selectedRunId && runs.some((run) => run.run_id === state.selectedRunId) ? state.selectedRunId : runs[0].run_id);
  }
}

elements.refreshButton.addEventListener("click", refresh);
elements.modelFilter.addEventListener("change", refresh);
elements.statusFilter.addEventListener("change", refresh);
elements.accuracyFilter.addEventListener("change", refresh);

refresh().catch((error) => {
  elements.detailTitle.textContent = "Unable to load runs";
  elements.detailNotes.textContent = error.message;
});
