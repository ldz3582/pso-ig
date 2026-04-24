const state = {
  benchmarks: [],
  resultBundle: null,
  result: null,
  scheduleResult: null,
  currentInstance: null,
  activeMode: null,
  selectedArchiveSolutionIndex: null,
  currentView: "workspace",
  ui: {
    ganttRefreshFrame: null,
    layoutFrame: null,
  },
  playback: {
    isPlaying: false,
    currentTime: 0,
    maxTime: 0,
    speed: 1,
    frameId: null,
    lastStamp: null,
  },
};

const splitLayoutRules = {
  workspace: { minLeft: 480, minRight: 300 },
  solver: { minLeft: 420, minRight: 300 },
  insights: { minLeft: 420, minRight: 300 },
};

const palette = [
  ["#0f7bff", "#14c8ff"],
  ["#ff7a59", "#ffb36b"],
  ["#31d38b", "#6de4b6"],
  ["#8b7dff", "#5fa5ff"],
  ["#ff5f57", "#ff8d7b"],
  ["#18b8a8", "#46d7c7"],
  ["#f7a400", "#ffd36b"],
  ["#4466ff", "#8bb2ff"],
];

const viewMeta = {
  workspace: {
    eyebrow: "Workspace",
    title: "算例工作台",
    description: "导入 benchmark、生成模板或直接编辑 JSON，先把输入数据准备好。",
  },
  solver: {
    eyebrow: "Solver",
    title: "求解中心",
    description: "配置 PSO、IG 和多智能体参数，发起求解并切换不同模式结果。",
  },
  insights: {
    eyebrow: "Insights",
    title: "结果分析",
    description: "查看瓶颈阶段、机器利用率、等待时间和多解档案的统计结果。",
  },
  schedule: {
    eyebrow: "Schedule",
    title: "动态甘特图",
    description: "用时间轴回放调度过程，观察机器和工件状态的实时变化。",
  },
};

const localizedViewMeta = {
  workspace: {
    eyebrow: "Workspace",
    title: "算例工作台",
    description: "导入 benchmark、生成模板或直接编辑 JSON，先把输入数据准备完整。",
  },
  solver: {
    eyebrow: "Solver",
    title: "求解中心",
    description: "配置 PSO、IG 和多智能体参数，发起求解并切换不同模式结果。",
  },
  insights: {
    eyebrow: "Insights",
    title: "结果分析",
    description: "查看瓶颈阶段、设备利用率、等待时间和多解档案的统计结果。",
  },
  schedule: {
    eyebrow: "Schedule",
    title: "动态甘特图",
    description: "用时间轴回放调度过程，观察机器和工件状态的实时变化。",
  },
};

viewMeta.simulation = {
  eyebrow: "Simulation",
  title: "仿真演示",
  description: "以车间工位、等待队列和完工流转对求解结果进行仿真回放。",
};

localizedViewMeta.simulation = {
  eyebrow: "Simulation",
  title: "仿真演示",
  description: "以车间工位、等待队列和完工流转对求解结果进行仿真回放。",
};

const els = {
  viewTabs: document.querySelectorAll("[data-view]"),
  viewPages: document.querySelectorAll("[data-view-page]"),
  pageEyebrow: document.getElementById("pageEyebrow"),
  pageTitle: document.getElementById("pageTitle"),
  pageDescription: document.getElementById("pageDescription"),
  commandMetrics: document.getElementById("commandMetrics"),
  goWorkspaceBtn: document.getElementById("goWorkspaceBtn"),
  goSolverBtn: document.getElementById("goSolverBtn"),
  goInsightsBtn: document.getElementById("goInsightsBtn"),
  goScheduleBtn: document.getElementById("goScheduleBtn"),
  toastRack: document.getElementById("toastRack"),
  benchmarkSelect: document.getElementById("benchmarkSelect"),
  loadBenchmarkBtn: document.getElementById("loadBenchmarkBtn"),
  loadFirstBenchmarkBtn: document.getElementById("loadFirstBenchmarkBtn"),
  importFile: document.getElementById("importFile"),
  instanceEditor: document.getElementById("instanceEditor"),
  instanceName: document.getElementById("instanceName"),
  nJobs: document.getElementById("nJobs"),
  nStages: document.getElementById("nStages"),
  machinesPerStage: document.getElementById("machinesPerStage"),
  generateTemplateBtn: document.getElementById("generateTemplateBtn"),
  generateTemplateHeroBtn: document.getElementById("generateTemplateHeroBtn"),
  formatJsonBtn: document.getElementById("formatJsonBtn"),
  instancePreview: document.getElementById("instancePreview"),
  instanceValidity: document.getElementById("instanceValidity"),
  solveBtn: document.getElementById("solveBtn"),
  solverMode: document.getElementById("solverMode"),
  runStatus: document.getElementById("runStatus"),
  lastElapsed: document.getElementById("lastElapsed"),
  lastArchiveSize: document.getElementById("lastArchiveSize"),
  summaryCards: document.getElementById("summaryCards"),
  modeResultSwitcher: document.getElementById("modeResultSwitcher"),
  analysisBoard: document.getElementById("analysisBoard"),
  headlineBadge: document.getElementById("headlineBadge"),
  ganttContainer: document.getElementById("ganttContainer"),
  ganttMeta: document.getElementById("ganttMeta"),
  stageFilter: document.getElementById("stageFilter"),
  zoomRange: document.getElementById("zoomRange"),
  playbackSpeed: document.getElementById("playbackSpeed"),
  playPauseBtn: document.getElementById("playPauseBtn"),
  resetPlaybackBtn: document.getElementById("resetPlaybackBtn"),
  timeSlider: document.getElementById("timeSlider"),
  currentTimeLabel: document.getElementById("currentTimeLabel"),
  currentEventLabel: document.getElementById("currentEventLabel"),
  realtimeSummary: document.getElementById("realtimeSummary"),
  machineStatusList: document.getElementById("machineStatusList"),
  jobStatusList: document.getElementById("jobStatusList"),
  ganttLegend: document.getElementById("ganttLegend"),
  simulationSummary: document.getElementById("simulationSummary"),
  simulationScene: document.getElementById("simulationScene"),
  archiveContainer: document.getElementById("archiveContainer"),
  populationSize: document.getElementById("populationSize"),
  maxGenerations: document.getElementById("maxGenerations"),
  igIterations: document.getElementById("igIterations"),
  kNeighbors: document.getElementById("kNeighbors"),
  mutationProbability: document.getElementById("mutationProbability"),
  destructionRatio: document.getElementById("destructionRatio"),
  seedValue: document.getElementById("seedValue"),
  stagnationThreshold: document.getElementById("stagnationThreshold"),
};

els.goSimulationBtn = document.getElementById("goSimulationBtn");

function showToast(message, tone = "info", title = "Notice") {
  if (!els.toastRack) return;
  const toast = document.createElement("article");
  toast.className = `toast ${tone}`;
  toast.innerHTML = `<strong class="toast-title">${title}</strong><p>${message}</p>`;
  els.toastRack.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.add("show");
  });
  window.setTimeout(() => {
    toast.classList.remove("show");
    window.setTimeout(() => {
      toast.remove();
    }, 260);
  }, 2600);
}

function setSplitLayoutSizes(layout, key, left, right) {
  layout.style.setProperty(`--${key}-left`, `${left}px`);
  layout.style.setProperty(`--${key}-right`, `${right}px`);
}

function loadStoredSplitLayouts() {
  document.querySelectorAll(".split-layout").forEach((layout) => {
    const key = layout.dataset.layoutKey;
    if (!key) return;
    try {
      const raw = window.localStorage.getItem(`hfsp-split-${key}`);
      if (!raw) return;
      const sizes = JSON.parse(raw);
      if (!Number.isFinite(sizes.left) || !Number.isFinite(sizes.right)) return;
      setSplitLayoutSizes(layout, key, sizes.left, sizes.right);
    } catch {
      // Ignore invalid persisted state.
    }
  });
}

function initSplitters() {
  const splitters = document.querySelectorAll(".splitter[data-splitter-key]");
  splitters.forEach((splitter) => {
    splitter.addEventListener("dblclick", () => {
      const key = splitter.dataset.splitterKey;
      const layout = splitter.closest(".split-layout");
      if (!key || !layout) return;
      layout.style.removeProperty(`--${key}-left`);
      layout.style.removeProperty(`--${key}-right`);
      try {
        window.localStorage.removeItem(`hfsp-split-${key}`);
      } catch {
        // Ignore storage reset failures.
      }
      scheduleLayoutMetricsUpdate();
      if (state.scheduleResult && state.currentView === "schedule") {
        refreshScheduleViewport(true);
      }
    });

    splitter.addEventListener("pointerdown", (event) => {
      if (window.innerWidth <= 1280) return;
      const key = splitter.dataset.splitterKey;
      const layout = splitter.closest(".split-layout");
      if (!key || !layout) return;

      const rules = splitLayoutRules[key] || { minLeft: 360, minRight: 260 };
      const rect = layout.getBoundingClientRect();
      const handleWidth = splitter.getBoundingClientRect().width || 12;
      const leftPane = layout.firstElementChild;
      const rightPane = layout.lastElementChild;
      const startLeft = leftPane?.getBoundingClientRect().width || rect.width * 0.6;
      const startX = event.clientX;

      splitter.classList.add("is-active");
      document.body.classList.add("is-resizing");
      splitter.setPointerCapture(event.pointerId);

      const onMove = (moveEvent) => {
        const delta = moveEvent.clientX - startX;
        const total = rect.width - handleWidth;
        const minLeft = rules.minLeft;
        const minRight = rules.minRight;
        const nextLeft = Math.max(minLeft, Math.min(total - minRight, startLeft + delta));
        const nextRight = Math.max(minRight, total - nextLeft);
        setSplitLayoutSizes(layout, key, nextLeft, nextRight);
        scheduleLayoutMetricsUpdate();
      };

      const onUp = () => {
        splitter.classList.remove("is-active");
        document.body.classList.remove("is-resizing");
        splitter.removeEventListener("pointermove", onMove);
        splitter.removeEventListener("pointerup", onUp);
        splitter.removeEventListener("pointercancel", onUp);
        const left = leftPane?.getBoundingClientRect().width;
        const right = rightPane?.getBoundingClientRect().width;
        if (Number.isFinite(left) && Number.isFinite(right)) {
          try {
            window.localStorage.setItem(`hfsp-split-${key}`, JSON.stringify({ left, right }));
          } catch {
            // Ignore storage write failures.
          }
        }
      };

      splitter.addEventListener("pointermove", onMove);
      splitter.addEventListener("pointerup", onUp);
      splitter.addEventListener("pointercancel", onUp);
    });
  });
}

function getCommandMetrics() {
  const metrics = [];
  if (state.currentInstance) {
    metrics.push(`<span class="metric-chip"><strong>${state.currentInstance.name || "custom"}</strong><span>当前实例</span></span>`);
    metrics.push(
      `<span class="metric-chip"><strong>${state.currentInstance.n_jobs} jobs</strong><span>${state.currentInstance.n_stages} stages</span></span>`
    );
  } else {
    metrics.push(`<span class="metric-chip"><strong>未载入</strong><span>等待实例</span></span>`);
  }

  if (state.result) {
    metrics.push(`<span class="metric-chip"><strong>${formatNumber(state.result.best_makespan)}</strong><span>Best Makespan</span></span>`);
    metrics.push(`<span class="metric-chip"><strong>${state.result.solver_label}</strong><span>当前结果</span></span>`);
  } else {
    metrics.push(`<span class="metric-chip"><strong>${els.solverMode?.value || "compare"}</strong><span>求解模式</span></span>`);
  }
  return metrics.join("");
}

function buildLocalizedCommandMetrics() {
  const metrics = [];
  if (state.currentInstance) {
    metrics.push(`<span class="metric-chip"><strong>${state.currentInstance.name || "custom"}</strong><span>当前实例</span></span>`);
    metrics.push(
      `<span class="metric-chip"><strong>${state.currentInstance.n_jobs} jobs</strong><span>${state.currentInstance.n_stages} stages</span></span>`
    );
  } else {
    metrics.push(`<span class="metric-chip"><strong>未载入</strong><span>等待实例</span></span>`);
  }

  if (state.result) {
    metrics.push(`<span class="metric-chip"><strong>${formatNumber(state.result.best_makespan)}</strong><span>Best Makespan</span></span>`);
    metrics.push(`<span class="metric-chip"><strong>${state.result.solver_label}</strong><span>当前结果</span></span>`);
  } else {
    metrics.push(`<span class="metric-chip"><strong>${els.solverMode?.value || "compare"}</strong><span>求解模式</span></span>`);
  }
  return metrics.join("");
}

function updateCommandDeck() {
  const meta = localizedViewMeta[state.currentView] || localizedViewMeta.workspace;
  els.pageEyebrow.textContent = meta.eyebrow;
  els.pageTitle.textContent = meta.title;
  els.pageDescription.textContent = meta.description;
  els.commandMetrics.innerHTML = buildLocalizedCommandMetrics();

  [
    ["workspace", els.goWorkspaceBtn],
    ["solver", els.goSolverBtn],
    ["insights", els.goInsightsBtn],
    ["schedule", els.goScheduleBtn],
    ["simulation", els.goSimulationBtn],
  ].forEach(([key, button]) => {
    button.classList.toggle("active", key === state.currentView);
  });
  scheduleLayoutMetricsUpdate();
}

function updateLayoutMetrics() {
  const chromeSelectors = [".layout-hub", ".playback-hub"];
  const occupied = chromeSelectors.reduce((sum, selector) => {
    const node = document.querySelector(selector);
    if (!node) return sum;
    return sum + node.getBoundingClientRect().height;
  }, 0);
  const style = window.getComputedStyle(document.body);
  const gap = Number.parseFloat(style.rowGap || style.gap || "0") || 0;
  const paddingTop = Number.parseFloat(style.paddingTop || "0") || 0;
  const paddingBottom = Number.parseFloat(style.paddingBottom || "0") || 0;
  const viewportHeight = window.innerHeight;
  const available = Math.max(420, viewportHeight - occupied - gap * 3 - paddingTop - paddingBottom);
  document.documentElement.style.setProperty("--app-content-height", `${available}px`);
}

function scheduleLayoutMetricsUpdate() {
  if (state.ui.layoutFrame) cancelAnimationFrame(state.ui.layoutFrame);
  state.ui.layoutFrame = requestAnimationFrame(() => {
    state.ui.layoutFrame = null;
    updateLayoutMetrics();
  });
}

function refreshScheduleViewport(autoFit = false) {
  if (!state.scheduleResult) return;
  if (state.ui.ganttRefreshFrame) cancelAnimationFrame(state.ui.ganttRefreshFrame);
  state.ui.ganttRefreshFrame = requestAnimationFrame(() => {
    state.ui.ganttRefreshFrame = null;
    renderGantt(state.scheduleResult, autoFit);
    applyPlaybackTime(state.playback.currentTime, true);
  });
}

function syncPlayheadViewport(behavior = "smooth") {
  if (state.currentView !== "schedule") return;
  const shell = els.ganttContainer;
  const playhead = document.getElementById("playhead");
  if (!shell || !playhead) return;

  const shellRect = shell.getBoundingClientRect();
  const playheadRect = playhead.getBoundingClientRect();
  const currentLeft = shell.scrollLeft;
  const playheadCenter = playheadRect.left - shellRect.left + currentLeft;
  const targetLeft = Math.max(0, playheadCenter - shell.clientWidth * 0.45);
  const delta = Math.abs(targetLeft - currentLeft);
  if (delta < 12) return;
  shell.classList.add("is-following");
  clearTimeout(syncPlayheadViewport.followTimer);
  syncPlayheadViewport.followTimer = setTimeout(() => {
    shell.classList.remove("is-following");
  }, behavior === "smooth" ? 260 : 120);
  shell.scrollTo({ left: targetLeft, behavior });
}

function openArchiveSolution(result, index, targetView) {
  state.selectedArchiveSolutionIndex = index;
  renderArchive(result);
  const scheduleResult = getDisplayedScheduleResult(result);
  renderGantt(scheduleResult, true);
  preparePlayback(scheduleResult);
  setView(targetView);
  showToast(`Loaded solution ${index + 1} ${targetView}`, "success", "Archive");
}

function setView(viewKey) {
  state.currentView = viewKey;
  document.body.classList.remove("is-view-switching");
  void document.body.offsetWidth;
  document.body.classList.add("is-view-switching");
  window.clearTimeout(setView.transitionTimer);
  setView.transitionTimer = window.setTimeout(() => {
    document.body.classList.remove("is-view-switching");
  }, 460);
  document.body.dataset.activeView = viewKey;
  els.viewTabs.forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewKey);
  });
  els.viewPages.forEach((page) => {
    page.classList.toggle("active", page.dataset.viewPage === viewKey);
  });
  if (viewKey === "schedule" && state.scheduleResult) {
    refreshScheduleViewport(true);
  }
  if (viewKey === "simulation" && state.scheduleResult) {
    applyPlaybackTime(state.playback.currentTime, true);
  }
  updateCommandDeck();
  scheduleLayoutMetricsUpdate();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function formatNumber(value, digits = 0) {
  return Number(value).toLocaleString("zh-CN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function setValidity(type, text) {
  els.instanceValidity.textContent = text;
  els.instanceValidity.className = `status-pill ${type}`;
}

function setRunStatus(text) {
  els.runStatus.textContent = text;
}

function syncBuilderFields(instance) {
  els.instanceName.value = instance.name || "custom_hfsp_case";
  els.nJobs.value = instance.n_jobs;
  els.nStages.value = instance.n_stages;
  els.machinesPerStage.value = (instance.machines_per_stage || []).join(",");
}

function setEditorContent(instance) {
  state.currentInstance = instance;
  els.instanceEditor.value = JSON.stringify(instance, null, 2);
  syncBuilderFields(instance);
  renderInstancePreview(instance);
  updateCommandDeck();
}

function createTemplateInstance() {
  const name = els.instanceName.value.trim() || "custom_hfsp_case";
  const nJobs = Number.parseInt(els.nJobs.value, 10);
  const nStages = Number.parseInt(els.nStages.value, 10);
  const machinesPerStage = els.machinesPerStage.value
    .split(",")
    .map((item) => Number.parseInt(item.trim(), 10))
    .filter((item) => Number.isFinite(item) && item > 0);

  if (!Number.isFinite(nJobs) || nJobs < 1 || !Number.isFinite(nStages) || nStages < 1) {
    throw new Error("工件数和阶段数必须是正整数");
  }
  if (machinesPerStage.length !== nStages) {
    throw new Error("machines_per_stage 的数量必须与阶段数一致");
  }

  const processing_times = Array.from({ length: nJobs }, (_, jobId) =>
    Array.from({ length: nStages }, (_, stageId) =>
      Array.from({ length: machinesPerStage[stageId] }, (_, machineId) => {
        const baseline = 7 + ((jobId * 5 + stageId * 7 + machineId * 3) % 13);
        return baseline + stageId * 2;
      })
    )
  );

  return {
    name,
    n_jobs: nJobs,
    n_stages: nStages,
    machines_per_stage: machinesPerStage,
    processing_times,
  };
}

function validateInstance(instance) {
  if (!instance || typeof instance !== "object") {
    throw new Error("算例必须是对象");
  }
  const { name, n_jobs, n_stages, machines_per_stage, processing_times } = instance;
  if (!name) throw new Error("算例缺少 name");
  if (!Number.isInteger(n_jobs) || n_jobs < 1) throw new Error("n_jobs 必须是正整数");
  if (!Number.isInteger(n_stages) || n_stages < 1) throw new Error("n_stages 必须是正整数");
  const machinesPerStage = machines_per_stage;
  if (!Array.isArray(machinesPerStage) || machinesPerStage.length !== n_stages) {
    throw new Error("machines_per_stage 必须是与 n_stages 等长的数组");
  }
  if (!Array.isArray(processing_times) || processing_times.length !== n_jobs) {
    throw new Error("processing_times 必须是与 n_jobs 等长的三维数组");
  }
  processing_times.forEach((job, jobIdx) => {
    if (!Array.isArray(job) || job.length !== n_stages) {
      throw new Error(`工件 ${jobIdx} 的阶段数量不正确`);
    }
    job.forEach((stageTimes, stageIdx) => {
      if (!Array.isArray(stageTimes) || stageTimes.length !== machinesPerStage[stageIdx]) {
        throw new Error(`工件 ${jobIdx} 在阶段 ${stageIdx + 1} 的机器数量不正确`);
      }
      stageTimes.forEach((time) => {
        if (!Number.isFinite(time) || time <= 0) {
          throw new Error("加工时间必须是正数");
        }
      });
    });
  });
}

function parseEditorInstance() {
  const raw = els.instanceEditor.value.trim();
  if (!raw) throw new Error("请先输入或导入算例 JSON");
  const instance = JSON.parse(raw);
  validateInstance(instance);
  return instance;
}

function renderInstancePreview(instance) {
  const totalMachines = instance.machines_per_stage.reduce((sum, item) => sum + item, 0);
  const previewItems = [
    `名称 ${instance.name}`,
    `工件 ${instance.n_jobs}`,
    `阶段 ${instance.n_stages}`,
    `机器 ${totalMachines}`,
    `机器分布 ${instance.machines_per_stage.join(" / ")}`,
  ];
  els.instancePreview.innerHTML = previewItems.map((item) => `<span class="preview-chip">${item}</span>`).join("");
  setValidity("success", "结构合法");
}

function renderErrorState(message) {
  setValidity("error", "结构错误");
  els.instancePreview.innerHTML = `<span class="preview-chip">${message}</span>`;
}

async function fetchBenchmarks() {
  const response = await fetch("/api/benchmarks");
  const payload = await response.json();
  state.benchmarks = payload.benchmarks || [];
  els.benchmarkSelect.innerHTML = state.benchmarks
    .map(
      (item) =>
        `<option value="${item.file_name}">${item.name} · ${item.n_jobs} jobs / ${item.n_stages} stages</option>`
    )
    .join("");
}

async function loadBenchmark(fileName) {
  const response = await fetch(`/api/benchmarks/${encodeURIComponent(fileName)}`);
  if (!response.ok) throw new Error("无法加载 benchmark");
  const instance = await response.json();
  setEditorContent(instance);
}

function collectConfig() {
  return {
    population_size: Number.parseInt(els.populationSize.value, 10),
    max_generations: Number.parseInt(els.maxGenerations.value, 10),
    ig_max_iterations: Number.parseInt(els.igIterations.value, 10),
    k_neighbors: Number.parseInt(els.kNeighbors.value, 10),
    mutation_probability: Number.parseFloat(els.mutationProbability.value),
    destruction_ratio: Number.parseFloat(els.destructionRatio.value),
    stagnation_threshold: Number.parseInt(els.stagnationThreshold.value, 10),
    seed: els.seedValue.value === "" ? null : Number.parseInt(els.seedValue.value, 10),
  };
}

function getModeResults(bundle) {
  if (!bundle) return {};
  if (bundle.mode_results) return bundle.mode_results;
  const key = bundle.solver_key || "basic_pso_ig";
  return { [key]: bundle };
}

function getDisplayedResult() {
  const results = getModeResults(state.resultBundle);
  return results[state.activeMode] || state.resultBundle;
}

function getDisplayedScheduleResult(baseResult = state.result) {
  if (!baseResult) return null;
  const archiveIndex = state.selectedArchiveSolutionIndex;
  if (archiveIndex == null) return baseResult;

  const selected = baseResult.archive?.[archiveIndex];
  if (!selected) return baseResult;

  return {
    ...baseResult,
    best_makespan: selected.makespan,
    best_solution: {
      permutation: selected.permutation,
      makespan: selected.makespan,
      machine_assignments: selected.machine_assignments || [],
      completion_times: selected.completion_times || [],
      operations: selected.operations || [],
    },
  };
}

function renderModeSwitcher(bundle) {
  const results = getModeResults(bundle);
  const keys = Object.keys(results);
  if (keys.length <= 1) {
    els.modeResultSwitcher.innerHTML = "";
    return;
  }

  const comparison = bundle.comparison || {};
  els.modeResultSwitcher.innerHTML = `
    <div class="mode-switcher-head">
      <span>Result Views</span>
      <small>Winner: ${comparison.winner_label || results[state.activeMode]?.solver_label || ""}</small>
    </div>
    <div class="mode-switcher-buttons">
      ${keys
        .map((key) => {
          const result = results[key];
          const activeClass = key === state.activeMode ? "active" : "";
          return `<button class="mode-switch-btn ${activeClass}" data-mode-key="${key}">${result.solver_label} · ${formatNumber(result.best_makespan)}</button>`;
        })
        .join("")}
    </div>
  `;

  els.modeResultSwitcher.querySelectorAll("[data-mode-key]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeMode = button.dataset.modeKey;
      state.selectedArchiveSolutionIndex = null;
      renderModeSwitcher(state.resultBundle);
      renderCurrentMode();
    });
  });
}

function createSummaryCard(label, value, note) {
  const template = document.getElementById("summaryCardTemplate");
  const node = template.content.firstElementChild.cloneNode(true);
  node.querySelector(".summary-label").textContent = label;
  node.querySelector(".summary-value").textContent = value;
  node.querySelector(".summary-note").textContent = note;
  return node;
}

function renderSummary(result) {
  const { analytics, best_makespan, elapsed_seconds, archive, instance } = result;
  els.summaryCards.innerHTML = "";
  const cards = [
    createSummaryCard("最佳 Makespan", formatNumber(best_makespan), instance.name),
    createSummaryCard(
      "相对 NEH 改善",
      `${analytics.comparison.improvement_vs_neh}%`,
      `NEH = ${formatNumber(analytics.comparison.neh_makespan)}`
    ),
    createSummaryCard(
      "相对 SPT 改善",
      `${analytics.comparison.improvement_vs_spt}%`,
      `SPT = ${formatNumber(analytics.comparison.spt_makespan)}`
    ),
    createSummaryCard("多解档案", formatNumber(archive.length), `耗时 ${elapsed_seconds}s`),
  ];

  if (state.resultBundle?.comparison) {
    const current = result.solver_key;
    const opponent = current === "multi_agent" ? "basic_pso_ig" : "multi_agent";
    const currentScore = state.resultBundle.comparison[current]?.best_makespan;
    const opponentScore = state.resultBundle.comparison[opponent]?.best_makespan;
    if (currentScore != null && opponentScore != null) {
      cards.push(
        createSummaryCard(
          "模式对比",
          `${formatNumber(opponentScore - currentScore)}`,
          `${result.solver_label} 相对另一模式的 makespan 差值`
        )
      );
    }
  }

  cards.forEach((card) => els.summaryCards.appendChild(card));

  els.lastElapsed.textContent = `${elapsed_seconds}s`;
  els.lastArchiveSize.textContent = formatNumber(archive.length);
  els.headlineBadge.textContent = `${result.solver_label} · ${result.best_solution.permutation.join(" → ")}`;
}

function renderAnalysis(result) {
  const analytics = result.analytics;
  const bottleneck = analytics.bottleneck_stage;
  const stageRows = analytics.stage_stats
    .map(
      (stage) => `
        <div class="utilization-row">
          <strong>${stage.label}</strong>
          <div class="bar-track"><div class="bar-fill" style="width:${stage.utilization * 100}%"></div></div>
          <span>${formatNumber(stage.utilization * 100, 1)}%</span>
        </div>
      `
    )
    .join("");

  const machineRows = analytics.machine_stats
    .slice()
    .sort((a, b) => b.utilization - a.utilization)
    .slice(0, 8)
    .map(
      (machine) => `
        <div class="machine-pill">
          <strong>${machine.label}</strong>
          <small>利用率 ${formatNumber(machine.utilization * 100, 1)}%</small>
          <small>Busy ${formatNumber(machine.busy_time)} / Idle ${formatNumber(machine.idle_time)}</small>
        </div>
      `
    )
    .join("");

  const jobRows = analytics.job_stats
    .slice()
    .sort((a, b) => b.waiting_time - a.waiting_time)
    .slice(0, 6)
    .map(
      (job) => `
        <div class="job-row">
          <strong>Job ${job.job_id}</strong>
          <div class="bar-track"><div class="bar-fill" style="width:${(job.waiting_time / Math.max(1, result.best_makespan)) * 100}%"></div></div>
          <span class="job-meta">等待 ${formatNumber(job.waiting_time)}</span>
        </div>
      `
    )
    .join("");

  els.analysisBoard.className = "analysis-board";
  els.analysisBoard.innerHTML = `
    <div class="analysis-column">
      <article class="analysis-block">
        <p class="eyebrow">Bottleneck</p>
        <h3>${bottleneck ? bottleneck.label : "暂无"}</h3>
        <div class="metric-list">
          <div class="metric-row">
            <div class="metric-item">
              <span>瓶颈利用率</span>
              <strong>${bottleneck ? formatNumber(bottleneck.utilization * 100, 1) : 0}%</strong>
            </div>
            <div class="metric-item">
              <span>档案跨度</span>
              <strong>${formatNumber(analytics.archive_stats.spread)}</strong>
            </div>
            <div class="metric-item">
              <span>平均档案值</span>
              <strong>${formatNumber(analytics.archive_stats.average_makespan, 1)}</strong>
            </div>
          </div>
        </div>
      </article>
      <article class="analysis-block">
        <p class="eyebrow">Stage Load</p>
        <div class="utilization-list">${stageRows}</div>
      </article>
    </div>
    <div class="analysis-column">
      <article class="analysis-block">
        <p class="eyebrow">Machine Heat</p>
        <div class="machine-pills">${machineRows}</div>
      </article>
      <article class="analysis-block">
        <p class="eyebrow">Job Waiting</p>
        <div class="job-list">${jobRows}</div>
      </article>
    </div>
  `;
}

function renderArchive(result) {
  const archive = result.archive || [];
  if (!archive.length) {
    els.archiveContainer.className = "archive-grid empty-state";
    els.archiveContainer.textContent = "档案库尚未生成。";
    return;
  }

  els.archiveContainer.className = "archive-grid";
  els.archiveContainer.innerHTML = archive
    .slice(0, 12)
    .map((solution, index) => {
      const permutationPreview = solution.permutation.slice(0, 6).join(" → ");
      return `
        <article class="archive-item">
          <p>Solution ${index + 1}</p>
          <strong>${formatNumber(solution.makespan)}</strong>
          <span class="archive-meta">排列前缀 ${permutationPreview}${solution.permutation.length > 6 ? " ..." : ""}</span>
          <div class="archive-chips">
            <span class="archive-chip">Jobs ${solution.permutation.length}</span>
            <span class="archive-chip">Stages ${solution.machine_assignments[0]?.length || 0}</span>
          </div>
        </article>
      `;
    })
    .join("");
}

function stopPlayback() {
  state.playback.isPlaying = false;
  state.playback.lastStamp = null;
  if (state.playback.frameId) {
    cancelAnimationFrame(state.playback.frameId);
    state.playback.frameId = null;
  }
  els.playPauseBtn.textContent = "播放";
}

function startPlayback() {
  if (!state.scheduleResult) return;
  if (state.playback.currentTime >= state.playback.maxTime) {
    state.playback.currentTime = 0;
  }
  state.playback.isPlaying = true;
  state.playback.lastStamp = null;
  els.playPauseBtn.textContent = "暂停";
  state.playback.frameId = requestAnimationFrame(tickPlayback);
}

function tickPlayback(timestamp) {
  if (!state.playback.isPlaying || !state.scheduleResult) return;
  if (state.playback.lastStamp == null) state.playback.lastStamp = timestamp;
  const delta = (timestamp - state.playback.lastStamp) / 1000;
  state.playback.lastStamp = timestamp;
  state.playback.currentTime += delta * state.playback.speed;
  if (state.playback.currentTime >= state.playback.maxTime) {
    state.playback.currentTime = state.playback.maxTime;
    applyPlaybackTime(state.playback.currentTime, false);
    stopPlayback();
    return;
  }
  applyPlaybackTime(state.playback.currentTime, false);
  state.playback.frameId = requestAnimationFrame(tickPlayback);
}

function togglePlayback() {
  if (!state.scheduleResult) return;
  if (state.playback.isPlaying) stopPlayback();
  else startPlayback();
}

function refreshStageFilter(result) {
  const selected = els.stageFilter.value;
  const options = ['<option value="all">全部阶段</option>']
    .concat(
      result.instance.machines_per_stage.map(
        (_, index) => `<option value="${index}">Stage ${index + 1}</option>`
      )
    )
    .join("");
  els.stageFilter.innerHTML = options;
  if ([...els.stageFilter.options].some((option) => option.value === selected)) {
    els.stageFilter.value = selected;
  }
}

function computeRealtimeState(result, currentTime) {
  const operations = result.best_solution.operations || [];
  const machineStates = [];
  const activeOperations = [];
  const stageFilter = els.stageFilter.value;

  result.instance.machines_per_stage.forEach((machineCount, stageId) => {
    if (stageFilter !== "all" && Number.parseInt(stageFilter, 10) !== stageId) return;
    for (let machineId = 0; machineId < machineCount; machineId += 1) {
      const laneOperations = operations
        .filter((operation) => operation.stage_id === stageId && operation.machine_id === machineId)
        .sort((left, right) => left.start_time - right.start_time);
      const active = laneOperations.find(
        (operation) => currentTime >= operation.start_time && currentTime < operation.end_time
      );
      const next = laneOperations.find((operation) => currentTime < operation.start_time);
      if (active) activeOperations.push(active);
      machineStates.push({
        label: `S${stageId + 1}-M${machineId + 1}`,
        state: active ? "busy" : next ? "waiting" : "idle",
        active,
        next,
      });
    }
  });

  const jobStates = Array.from({ length: result.instance.n_jobs }, (_, jobId) => {
    const jobOperations = operations
      .filter((operation) => operation.job_id === jobId)
      .sort((left, right) => left.stage_id - right.stage_id);
    const active = jobOperations.find(
      (operation) => currentTime >= operation.start_time && currentTime < operation.end_time
    );
    const completedCount = jobOperations.filter((operation) => currentTime >= operation.end_time).length;
    const next = jobOperations.find((operation) => currentTime < operation.start_time);
    let stateLabel = "waiting";
    if (completedCount === jobOperations.length) stateLabel = "done";
    else if (active) stateLabel = "processing";
    else if (completedCount === 0) stateLabel = "not-started";
    return {
      jobId,
      state: stateLabel,
      active,
      next,
      completedCount,
      totalStages: jobOperations.length,
    };
  });

  return {
    machineStates,
    jobStates,
    activeOperations,
    summary: {
      busyMachines: machineStates.filter((item) => item.state === "busy").length,
      idleMachines: machineStates.filter((item) => item.state === "idle").length,
      completedJobs: jobStates.filter((item) => item.state === "done").length,
      processingJobs: jobStates.filter((item) => item.state === "processing").length,
    },
  };
}

function colorForStage(stageId) {
  return palette[stageId % palette.length];
}

function renderGanttLegend(result) {
  const stageLegend = document.getElementById("ganttStageLegend");
  if (!els.ganttLegend || !stageLegend || !result?.instance?.machines_per_stage) return;
  const stageItems = result.instance.machines_per_stage
    .map((_, stageId) => {
      const [startColor, endColor] = colorForStage(stageId);
      return `
        <span class="legend-item">
          <span class="legend-swatch" style="background:linear-gradient(135deg, ${startColor}, ${endColor})"></span>
          Stage ${stageId + 1}
        </span>
      `;
    })
    .join("");
  stageLegend.innerHTML = `<span class="legend-title">阶段颜色</span>${stageItems}`;
}

function getAdaptiveZoom(result) {
  const stageFilter = els.stageFilter.value;
  const filteredStageId = stageFilter === "all" ? null : Number.parseInt(stageFilter, 10);
  const laneLabelWidth = 92;
  const hostWidth =
    els.ganttContainer.clientWidth ||
    els.ganttContainer.parentElement?.clientWidth ||
    window.innerWidth - 160 ||
    1200;
  const timelineWidth = Math.max(520, hostWidth - laneLabelWidth - 28);
  const makespan = Math.max(1, result.best_solution.makespan);
  const fitZoom = Math.floor(timelineWidth / makespan);
  const laneCount = result.instance.machines_per_stage.reduce((count, machines, stageId) => {
    if (filteredStageId !== null && filteredStageId !== stageId) return count;
    return count + machines;
  }, 0);
  const densityPenalty = laneCount > 10 ? 2 : laneCount > 6 ? 1 : 0;
  return Math.max(4, Math.min(16, fitZoom - densityPenalty));
}

function renderRealtimePanels(result, realtime) {
  const summary = realtime.summary;
  const primaryOperation = realtime.activeOperations[0];
  els.currentTimeLabel.textContent = `t = ${formatNumber(state.playback.currentTime, 1)}`;
  els.currentEventLabel.textContent = primaryOperation
    ? `Job ${primaryOperation.job_id} @ S${primaryOperation.stage_id + 1}-M${primaryOperation.machine_id + 1}`
    : summary.completedJobs === result.instance.n_jobs
      ? "全部工件已完成"
      : "当前无加工，系统等待下一任务";

  els.realtimeSummary.className = "realtime-summary";
  els.realtimeSummary.innerHTML = `
    <div class="realtime-metric"><span>忙碌机器</span><strong>${summary.busyMachines}</strong></div>
    <div class="realtime-metric"><span>空闲机器</span><strong>${summary.idleMachines}</strong></div>
    <div class="realtime-metric"><span>加工中工件</span><strong>${summary.processingJobs}</strong></div>
    <div class="realtime-metric"><span>已完工工件</span><strong>${summary.completedJobs}</strong></div>
  `;

  els.machineStatusList.className = "status-list";
  els.machineStatusList.innerHTML = realtime.machineStates
    .map((machine) => {
      const detail = machine.active
        ? `Job ${machine.active.job_id} · ${machine.active.start_time}-${machine.active.end_time}`
        : machine.next
          ? `下一任务 Job ${machine.next.job_id} @ ${machine.next.start_time}`
          : "无剩余任务";
      const labels = { busy: "运行中", waiting: "待机", idle: "空闲" };
      return `
        <div class="state-card ${machine.state}">
          <div class="state-card-head">
            <strong>${machine.label}</strong>
            <span class="state-badge ${machine.state}">${labels[machine.state]}</span>
          </div>
          <p>${detail}</p>
        </div>
      `;
    })
    .join("");

  els.jobStatusList.className = "status-list";
  els.jobStatusList.innerHTML = realtime.jobStates
    .slice()
    .sort((left, right) => {
      const order = { processing: 0, waiting: 1, "not-started": 2, done: 3 };
      return order[left.state] - order[right.state] || left.jobId - right.jobId;
    })
    .slice(0, 10)
    .map((job) => {
      const labels = {
        processing: "加工中",
        waiting: "等待下一阶段",
        "not-started": "未开始",
        done: "已完成",
      };
      const detail = job.active
        ? `当前在 S${job.active.stage_id + 1}-M${job.active.machine_id + 1}`
        : job.next
          ? `下一阶段 S${job.next.stage_id + 1} @ ${job.next.start_time}`
          : `完成 ${job.completedCount}/${job.totalStages}`;
      return `
        <div class="state-card ${job.state}">
          <div class="state-card-head">
            <strong>Job ${job.jobId}</strong>
            <span class="state-badge ${job.state}">${labels[job.state]}</span>
          </div>
          <p>${detail}</p>
        </div>
      `;
    })
    .join("");
}

function renderSimulationScene(result, realtime, currentTime) {
  const operations = result.best_solution.operations || [];
  if (!operations.length) {
    els.simulationSummary.textContent = "等待调度数据";
    els.simulationScene.className = "simulation-scene empty-state";
    els.simulationScene.textContent = "求解后将在这里展示工件在各阶段与机器间流转的仿真动画。";
    return;
  }

  const stageFilter = els.stageFilter.value;
  const filteredStageId = stageFilter === "all" ? null : Number.parseInt(stageFilter, 10);
  const visibleStageIds = result.instance.machines_per_stage
    .map((_, stageId) => stageId)
    .filter((stageId) => filteredStageId == null || filteredStageId === stageId);
  const queueJobsByStage = new Map();

  realtime.jobStates.forEach((job) => {
    if (!job.next || job.active) return;
    const stageId = job.next.stage_id;
    if (filteredStageId != null && filteredStageId !== stageId) return;
    const list = queueJobsByStage.get(stageId) || [];
    list.push(job);
    queueJobsByStage.set(stageId, list);
  });

  const stageCards = visibleStageIds.map((stageId) => {
    const stageOperations = operations.filter((operation) => operation.stage_id === stageId);
    const queueJobs = (queueJobsByStage.get(stageId) || [])
      .sort((left, right) => {
        const leftStart = left.next?.start_time ?? Number.MAX_SAFE_INTEGER;
        const rightStart = right.next?.start_time ?? Number.MAX_SAFE_INTEGER;
        return leftStart - rightStart || left.jobId - right.jobId;
      })
      .slice(0, 8);
    const activeCount = stageOperations.filter(
      (operation) => currentTime >= operation.start_time && currentTime < operation.end_time
    ).length;

    const machinesMarkup = Array.from(
      { length: result.instance.machines_per_stage[stageId] },
      (_, machineId) => {
        const laneOperations = stageOperations
          .filter((operation) => operation.machine_id === machineId)
          .sort((left, right) => left.start_time - right.start_time);
        const active = laneOperations.find(
          (operation) => currentTime >= operation.start_time && currentTime < operation.end_time
        );
        const next = laneOperations.find((operation) => currentTime < operation.start_time);
        const stateClass = active ? "active" : next ? "waiting" : "idle";
        const [startColor, endColor] = colorForStage(stageId);
        const progress = active
          ? ((currentTime - active.start_time) / Math.max(1, active.processing_time)) * 100
          : 0;
        const content = active
          ? `
              <div class="simulation-job-chip" style="background:linear-gradient(135deg, ${startColor}, ${endColor})">
                <span>Job ${active.job_id}</span>
                <small>${active.start_time} - ${active.end_time}</small>
              </div>
            `
          : `<span class="simulation-idle">${next ? `Next Job ${next.job_id} @ ${next.start_time}` : "Idle"}</span>`;
        return `
          <div class="simulation-machine ${stateClass}">
            <div class="simulation-machine-head">
              <strong>M${machineId + 1}</strong>
              <span class="simulation-state-dot"></span>
            </div>
            <div class="simulation-track">
              ${content}
              <div class="simulation-progress">
                <div class="simulation-progress-fill" style="width:${Math.max(0, Math.min(100, progress))}%; background:linear-gradient(90deg, ${startColor}, ${endColor})"></div>
              </div>
            </div>
          </div>
        `;
      }
    ).join("");

    const queueMarkup = queueJobs.length
      ? queueJobs
        .map((job) => `<span class="queue-chip highlight">J${job.jobId} · ${job.next.start_time}</span>`)
        .join("")
      : `<span class="queue-chip">No queue</span>`;

    return `
      <article class="simulation-stage">
        <div class="simulation-stage-head">
          <strong>Stage ${stageId + 1}</strong>
          <span>${activeCount}/${result.instance.machines_per_stage[stageId]} busy</span>
        </div>
        <div class="simulation-machines">${machinesMarkup}</div>
        <div class="simulation-queue">
          <span class="simulation-queue-label">Waiting queue</span>
          <div class="simulation-queue-chips">${queueMarkup}</div>
        </div>
      </article>
    `;
  }).join("");

  const completedMarkup = realtime.jobStates
    .filter((job) => job.state === "done")
    .slice(0, 20)
    .map((job) => `<span class="queue-chip">J${job.jobId}</span>`)
    .join("") || `<span class="queue-chip">No completed jobs yet</span>`;

  els.simulationSummary.textContent =
    `${realtime.summary.processingJobs} processing · ${realtime.summary.completedJobs} completed · ${realtime.summary.busyMachines} busy machines`;
  els.simulationScene.className = "simulation-scene";
  els.simulationScene.innerHTML = `
    ${stageCards}
    <div class="simulation-complete-lane">
      <span class="simulation-queue-label">Completed</span>
      ${completedMarkup}
    </div>
  `;
}

function renderGantt(result, autoFit = false) {
  const operations = result.best_solution.operations || [];
  renderGanttLegend(result);
  if (!operations.length) {
    els.ganttContainer.className = "gantt-shell empty-state";
    els.ganttContainer.textContent = "没有可展示的调度操作。";
    return;
  }

  refreshStageFilter(result);
  const stageFilter = els.stageFilter.value;
  const filteredStageId = stageFilter === "all" ? null : Number.parseInt(stageFilter, 10);
  if (autoFit) {
    els.zoomRange.value = String(getAdaptiveZoom(result));
  }
  const unit = Number.parseInt(els.zoomRange.value, 10);
  const makespan = result.best_solution.makespan;
  const chartWidth = Math.max(680, makespan * unit + 28);
  const tickStep = Math.max(1, Math.ceil(makespan / 10));

  const lanes = [];
  result.instance.machines_per_stage.forEach((machineCount, stageId) => {
    if (filteredStageId !== null && filteredStageId !== stageId) return;
    for (let machineId = 0; machineId < machineCount; machineId += 1) {
      lanes.push({ stageId, machineId, label: `S${stageId + 1}-M${machineId + 1}` });
    }
  });

  const headerTicks = Array.from({ length: Math.floor(makespan / tickStep) + 1 }, (_, index) => {
    const time = index * tickStep;
    return `<div class="gantt-tick" style="left:${time * unit}px"><span>${time}</span></div>`;
  }).join("");

  const rows = lanes
    .map((lane) => {
      const laneOperations = operations
        .filter((operation) => operation.stage_id === lane.stageId && operation.machine_id === lane.machineId)
        .sort((left, right) => left.start_time - right.start_time);
      const bars = laneOperations
        .map((operation) => {
          const [startColor, endColor] = colorForStage(operation.stage_id);
          return `
            <div
              class="gantt-bar"
              data-start="${operation.start_time}"
              data-end="${operation.end_time}"
              style="
                left:${operation.start_time * unit}px;
                width:${Math.max(4, operation.processing_time * unit)}px;
                background:linear-gradient(135deg, ${startColor}, ${endColor});
              "
              title="Job ${operation.job_id} | Stage ${operation.stage_id + 1} | Machine ${operation.machine_id + 1} | ${operation.start_time}-${operation.end_time}"
            >
              <span>J${operation.job_id}</span>
              <small>${operation.start_time} → ${operation.end_time}</small>
            </div>
          `;
        })
        .join("");
      return `
        <div class="gantt-row">
          <div class="gantt-row-label">${lane.label}</div>
          <div class="gantt-track" style="width:${chartWidth}px">${bars}</div>
        </div>
      `;
    })
    .join("");

  els.ganttContainer.className = "gantt-shell";
  els.ganttContainer.innerHTML = `
    <div class="gantt-chart" style="width:${chartWidth + 92}px">
      <div class="gantt-header">
        <div class="gantt-header-label">Machine</div>
        <div class="gantt-timeline" style="width:${chartWidth}px">
          ${headerTicks}
          <div id="playhead" class="playhead" style="left:0px"></div>
        </div>
      </div>
      ${rows}
    </div>
  `;

  els.ganttMeta.textContent = `Makespan ${makespan} · ${stageFilter === "all" ? "全部阶段" : `Stage ${filteredStageId + 1}`} · 缩放 ${unit}px / 时间单位`;
}

function applyPlaybackTime(nextTime, syncSlider = true) {
  if (!state.scheduleResult) return;
  const clamped = Math.max(0, Math.min(nextTime, state.playback.maxTime));
  state.playback.currentTime = clamped;
  if (syncSlider) els.timeSlider.value = String(clamped);
  const stageFilter = els.stageFilter.value;
  const filteredStageId = stageFilter === "all" ? null : Number.parseInt(stageFilter, 10);
  const unit = Number.parseInt(els.zoomRange.value, 10);
  const scheduleLabel = state.selectedArchiveSolutionIndex == null
    ? "Best solution"
    : `Archive solution ${state.selectedArchiveSolutionIndex + 1}`;
  els.ganttMeta.textContent = `${scheduleLabel} 路 Makespan ${state.scheduleResult.best_solution.makespan} 路 ${stageFilter === "all" ? "鍏ㄩ儴闃舵" : `Stage ${filteredStageId + 1}`} 路 缂╂斁 ${unit}px / 鏃堕棿鍗曚綅`;

  const playhead = document.getElementById("playhead");
  if (playhead) playhead.style.left = `${clamped * unit}px`;
  if (state.playback.isPlaying || state.currentView === "schedule") {
    syncPlayheadViewport(state.playback.isPlaying ? "smooth" : "auto");
  }

  document.querySelectorAll(".gantt-bar").forEach((bar) => {
    const start = Number.parseFloat(bar.dataset.start);
    const end = Number.parseFloat(bar.dataset.end);
    bar.classList.remove("is-completed", "is-active", "is-upcoming");
    if (clamped >= end) bar.classList.add("is-completed");
    else if (clamped >= start && clamped < end) bar.classList.add("is-active");
    else bar.classList.add("is-upcoming");
  });

  const realtime = computeRealtimeState(state.scheduleResult, clamped);
  renderRealtimePanels(state.scheduleResult, realtime);
  renderSimulationScene(state.scheduleResult, realtime, clamped);
}

function resetPlayback(forcedTime = 0) {
  stopPlayback();
  applyPlaybackTime(forcedTime, true);
}

function preparePlayback(result) {
  stopPlayback();
  state.scheduleResult = result;
  state.playback.currentTime = 0;
  state.playback.maxTime = result.best_solution.makespan;
  state.playback.speed = Number.parseFloat(els.playbackSpeed.value);
  els.timeSlider.max = String(result.best_solution.makespan);
  els.timeSlider.value = "0";
  els.playPauseBtn.disabled = false;
  els.resetPlaybackBtn.disabled = false;
  applyPlaybackTime(0, true);
}

function renderCurrentMode() {
  const displayed = getDisplayedResult();
  if (!displayed) return;
  state.result = displayed;
  renderSummary(displayed);
  renderAnalysis(displayed);
  renderArchive(displayed);
  const scheduleResult = getDisplayedScheduleResult(displayed);
  renderGantt(scheduleResult, true);
  preparePlayback(scheduleResult);
  updateCommandDeck();
}

function renderResult(resultBundle) {
  state.resultBundle = resultBundle;
  state.selectedArchiveSolutionIndex = null;
  const results = getModeResults(resultBundle);
  state.activeMode = state.activeMode && results[state.activeMode]
    ? state.activeMode
    : (resultBundle.solver_key || Object.keys(results)[0]);
  renderModeSwitcher(resultBundle);
  renderCurrentMode();
}

async function solveCurrentInstance() {
  const instance = parseEditorInstance();
  setEditorContent(instance);
  setRunStatus("求解中");
  els.solveBtn.disabled = true;
  els.solveBtn.textContent = "求解中...";
  stopPlayback();

  try {
    const response = await fetch("/api/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        instance,
        config: collectConfig(),
        mode: els.solverMode.value,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "求解失败");
    renderResult(payload);
    setView("insights");
    showToast(`Best makespan: ${formatNumber(payload.best_makespan)}`, "success", "Solved");
    setRunStatus("已完成");
  } catch (error) {
    setRunStatus("失败");
    showToast(error.message, "error", "Solve Failed");
  } finally {
    els.solveBtn.disabled = false;
    els.solveBtn.textContent = "开始求解";
  }
}

function bindEvents() {
  els.viewTabs.forEach((button) => {
    button.addEventListener("click", () => {
      setView(button.dataset.view);
    });
  });

  [
    ["workspace", els.goWorkspaceBtn],
    ["solver", els.goSolverBtn],
    ["insights", els.goInsightsBtn],
    ["schedule", els.goScheduleBtn],
    ["simulation", els.goSimulationBtn],
  ].forEach(([viewKey, button]) => {
    button.addEventListener("click", () => {
      setView(viewKey);
    });
  });

  els.loadBenchmarkBtn.addEventListener("click", async () => {
    if (!els.benchmarkSelect.value) return;
    try {
      setView("workspace");
      await loadBenchmark(els.benchmarkSelect.value);
      showToast("Benchmark loaded", "success", "Instance Ready");
    } catch (error) {
      showToast(error.message, "error", "Load Failed");
    }
  });

  els.loadFirstBenchmarkBtn.addEventListener("click", async () => {
    if (!state.benchmarks.length) return;
    els.benchmarkSelect.value = state.benchmarks[0].file_name;
    setView("workspace");
    await loadBenchmark(state.benchmarks[0].file_name);
    showToast("Sample instance loaded", "success", "Instance Ready");
  });

  [els.generateTemplateBtn, els.generateTemplateHeroBtn].forEach((button) => {
    button.addEventListener("click", () => {
      try {
        setView("workspace");
        setEditorContent(createTemplateInstance());
        showToast("Template instance generated", "success", "Template Ready");
      } catch (error) {
        showToast(error.message, "error", "Template Failed");
      }
    });
  });

  els.formatJsonBtn.addEventListener("click", () => {
    try {
      setEditorContent(parseEditorInstance());
      showToast("JSON formatted and validated", "success", "Format Complete");
    } catch (error) {
      showToast(error.message, "error", "Format Failed");
    }
  });

  els.instanceEditor.addEventListener("input", () => {
    try {
      const instance = JSON.parse(els.instanceEditor.value);
      validateInstance(instance);
      state.currentInstance = instance;
      syncBuilderFields(instance);
      renderInstancePreview(instance);
    } catch (error) {
      renderErrorState(error.message);
    }
  });

  els.importFile.addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    try {
      const instance = JSON.parse(text);
      validateInstance(instance);
      setView("workspace");
      setEditorContent(instance);
      showToast("JSON instance imported", "success", "Import Complete");
    } catch (error) {
      showToast(`Import failed: ${error.message}`, "error", "Import Failed");
    } finally {
      event.target.value = "";
    }
  });

  els.solveBtn.addEventListener("click", solveCurrentInstance);
  els.solverMode.addEventListener("change", () => {
    state.selectedArchiveSolutionIndex = null;
    updateCommandDeck();
  });
  els.stageFilter.addEventListener("change", () => {
    if (!state.scheduleResult) return;
    refreshScheduleViewport(true);
  });
  els.zoomRange.addEventListener("input", () => {
    if (!state.scheduleResult) return;
    refreshScheduleViewport(false);
  });
  els.playbackSpeed.addEventListener("change", () => {
    state.playback.speed = Number.parseFloat(els.playbackSpeed.value);
  });
  els.playPauseBtn.addEventListener("click", togglePlayback);
  els.resetPlaybackBtn.addEventListener("click", () => resetPlayback(0));
  els.timeSlider.addEventListener("input", () => {
    stopPlayback();
    applyPlaybackTime(Number.parseFloat(els.timeSlider.value), false);
  });
  window.addEventListener("resize", () => {
    scheduleLayoutMetricsUpdate();
    if (!state.scheduleResult) return;
    refreshScheduleViewport(true);
  });
  document.addEventListener("keydown", (event) => {
    const tagName = event.target?.tagName;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(tagName)) return;
    const mapping = { "1": "workspace", "2": "solver", "3": "insights", "4": "schedule", "5": "simulation" };
    const nextView = mapping[event.key];
    if (!nextView) return;
    event.preventDefault();
    setView(nextView);
  });
}

function renderArchive(result) {
  const archive = result.archive || [];
  if (!archive.length) {
    els.archiveContainer.className = "archive-grid empty-state";
    els.archiveContainer.textContent = "Archive unavailable";
    return;
  }

  els.archiveContainer.className = "archive-grid";
  els.archiveContainer.innerHTML = archive
    .slice(0, 12)
    .map((solution, index) => {
      const permutationPreview = solution.permutation.slice(0, 6).join(" -> ");
      const activeClass = state.selectedArchiveSolutionIndex === index ? " active" : "";
      return `
        <article class="archive-item${activeClass}">
          <p>Solution ${index + 1}</p>
          <strong>${formatNumber(solution.makespan)}</strong>
          <span class="archive-meta">Permutation ${permutationPreview}${solution.permutation.length > 6 ? " ..." : ""}</span>
          <div class="archive-chips">
            <span class="archive-chip">Jobs ${solution.permutation.length}</span>
            <span class="archive-chip">Stages ${solution.machine_assignments[0]?.length || 0}</span>
          </div>
          <div class="archive-actions">
            <button type="button" class="archive-action-btn" data-archive-index="${index}" data-archive-target="schedule">
              ${state.selectedArchiveSolutionIndex === index ? "Current Gantt" : "View Gantt"}
            </button>
            <button type="button" class="archive-action-btn secondary" data-archive-index="${index}" data-archive-target="simulation">
              ${state.selectedArchiveSolutionIndex === index ? "Current Simulation" : "View Simulation"}
            </button>
          </div>
        </article>
      `;
    })
    .join("");

  els.archiveContainer.querySelectorAll("[data-archive-index]").forEach((button) => {
    button.addEventListener("click", () => {
      openArchiveSolution(
        result,
        Number.parseInt(button.dataset.archiveIndex, 10),
        button.dataset.archiveTarget || "schedule"
      );
    });
  });
}

async function init() {
  loadStoredSplitLayouts();
  initSplitters();
  bindEvents();
  setView(state.currentView);
  scheduleLayoutMetricsUpdate();
  els.playPauseBtn.disabled = true;
  els.resetPlaybackBtn.disabled = true;
  await fetchBenchmarks();
  try {
    if (state.benchmarks.length) {
      els.benchmarkSelect.value = state.benchmarks[0].file_name;
      await loadBenchmark(state.benchmarks[0].file_name);
    } else {
      setEditorContent(createTemplateInstance());
    }
  } catch (error) {
    renderErrorState(error.message);
  }
}

/* ── Staff Manager Module ── */

const StaffManager = {
  staffList: [],
  selectedStaffId: null,

  init() {
    // Check login status
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    const userInfoArea = document.getElementById('userInfoArea');
    const currentUserLabel = document.getElementById('currentUserLabel');
    const logoutBtn = document.getElementById('logoutBtn');

    if (token && userInfoArea && currentUserLabel) {
      userInfoArea.style.display = 'flex';
      currentUserLabel.textContent = username || 'admin';
    } else {
      // Redirect to login if no token
      window.location.href = '/login';
      return;
    }

    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = '/login';
      });
    }

    // Bind add staff button
    const addStaffBtn = document.getElementById('addStaffBtn');
    if (addStaffBtn) {
      addStaffBtn.addEventListener('click', () => {
        StaffManager.selectedStaffId = null;
        StaffManager.renderStaffDetail(null);
      });
    }

    // Bind search
    const searchInput = document.getElementById('staffSearchInput');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        StaffManager.searchStaff(searchInput.value.trim());
      });
    }

    // Load staff data
    StaffManager.loadStaff();
  },

  getToken() {
    return localStorage.getItem('token') || '';
  },

  authHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + StaffManager.getToken(),
    };
  },

  async loadStaff() {
    try {
      const res = await fetch('/api/staff', { headers: StaffManager.authHeaders() });
      if (res.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
        return;
      }
      const data = await res.json();
      StaffManager.staffList = Array.isArray(data) ? data : (data.staff || data.data || []);
      StaffManager.renderStaffList(StaffManager.staffList);
      StaffManager.renderStaffStats(StaffManager.staffList);
    } catch (err) {
      showToast('加载人员列表失败: ' + err.message, 'error', 'Load Failed');
    }
  },

  renderStaffStats(list) {
    const bar = document.getElementById('staffStatsBar');
    if (!bar) return;
    const total = list.length;
    const active = list.filter(s => s.status === '在职').length;
    const deptMap = {};
    list.forEach(s => {
      const dept = s.department || '未分配';
      deptMap[dept] = (deptMap[dept] || 0) + 1;
    });
    const deptChips = Object.entries(deptMap)
      .map(([dept, count]) => `<span class="metric-chip"><strong>${count}</strong><span>${dept}</span></span>`)
      .join('');
    bar.innerHTML = `
      <span class="metric-chip"><strong>${total}</strong><span>总人数</span></span>
      <span class="metric-chip"><strong>${active}</strong><span>在职</span></span>
      ${deptChips}
    `;
  },

  renderStaffList(list) {
    const container = document.getElementById('staffListContainer');
    if (!container) return;
    if (!list.length) {
      container.innerHTML = '<div class="empty-state">暂无人员数据</div>';
      return;
    }
    container.innerHTML = list.map(s => {
      const isActive = s.status === '在职';
      const selectedClass = StaffManager.selectedStaffId === s.staff_id ? ' selected' : '';
      return `
        <article class="staff-card${selectedClass}" data-staff-id="${s.staff_id}">
          <div class="staff-card-head">
            <strong>${s.name || '-'}</strong>
            <span class="status-pill ${isActive ? 'success' : 'neutral'}">${s.status || '未知'}</span>
          </div>
          <div class="staff-card-meta">
            <span>工号 ${s.staff_id || '-'}</span>
            <span>${s.department || '-'}</span>
            <span>${s.position || '-'}</span>
          </div>
        </article>
      `;
    }).join('');

    container.querySelectorAll('.staff-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.dataset.staffId;
        StaffManager.selectedStaffId = id;
        const staff = StaffManager.staffList.find(s => String(s.staff_id) === String(id));
        StaffManager.renderStaffDetail(staff);
        StaffManager.renderStaffList(StaffManager.staffList);
      });
    });
  },

  searchStaff(keyword) {
    if (!keyword) {
      StaffManager.renderStaffList(StaffManager.staffList);
      return;
    }
    const kw = keyword.toLowerCase();
    const filtered = StaffManager.staffList.filter(s =>
      (s.name && s.name.toLowerCase().includes(kw)) ||
      (s.staff_id && String(s.staff_id).toLowerCase().includes(kw))
    );
    StaffManager.renderStaffList(filtered);
  },

  renderStaffDetail(staff) {
    const container = document.getElementById('staffDetailContent');
    const title = document.getElementById('staffDetailTitle');
    if (!container) return;

    const isNew = !staff;
    title.textContent = isNew ? '新增人员' : '编辑人员';

    container.innerHTML = `
      <form id="staffForm" class="staff-form">
        <div class="control-group">
          <label for="sf_staff_id">工号</label>
          <input id="sf_staff_id" type="text" value="${staff ? staff.staff_id || '' : ''}" ${isNew ? '' : 'readonly'} placeholder="自动生成或手动输入" />
        </div>
        <div class="control-group">
          <label for="sf_name">姓名</label>
          <input id="sf_name" type="text" value="${staff ? staff.name || '' : ''}" placeholder="请输入姓名" />
        </div>
        <div class="control-group">
          <label for="sf_department">部门</label>
          <input id="sf_department" type="text" value="${staff ? staff.department || '' : ''}" placeholder="请输入部门" />
        </div>
        <div class="control-group">
          <label for="sf_phone">手机号</label>
          <input id="sf_phone" type="text" value="${staff ? staff.phone || '' : ''}" placeholder="请输入手机号" />
        </div>
        <div class="control-group">
          <label for="sf_position">岗位</label>
          <input id="sf_position" type="text" value="${staff ? staff.position || '' : ''}" placeholder="请输入岗位" />
        </div>
        <div class="control-group">
          <label for="sf_device_ids">负责设备</label>
          <input id="sf_device_ids" type="text" value="${staff ? (Array.isArray(staff.device_ids) ? staff.device_ids.join(', ') : staff.device_ids || '') : ''}" placeholder="多个设备用逗号分隔" />
        </div>
        <div class="control-group">
          <label for="sf_status">状态</label>
          <select id="sf_status">
            <option value="在职" ${staff && staff.status === '在职' ? 'selected' : ''}>在职</option>
            <option value="离职" ${staff && staff.status === '离职' ? 'selected' : ''}>离职</option>
          </select>
        </div>
        <div class="staff-form-actions">
          <button type="submit" class="primary-btn">保存</button>
          ${!isNew ? '<button type="button" id="deleteStaffBtn" class="ghost-btn" style="color:var(--danger);">删除</button>' : ''}
        </div>
      </form>
    `;

    // Bind save
    const form = document.getElementById('staffForm');
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      StaffManager.saveStaff({
        staff_id: document.getElementById('sf_staff_id').value.trim(),
        name: document.getElementById('sf_name').value.trim(),
        department: document.getElementById('sf_department').value.trim(),
        phone: document.getElementById('sf_phone').value.trim(),
        position: document.getElementById('sf_position').value.trim(),
        device_ids: document.getElementById('sf_device_ids').value.split(',').map(s => s.trim()).filter(Boolean),
        status: document.getElementById('sf_status').value,
      });
    });

    // Bind delete
    const deleteBtn = document.getElementById('deleteStaffBtn');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', () => {
        if (staff) StaffManager.deleteStaff(staff.staff_id);
      });
    }
  },

  async saveStaff(data) {
    try {
      const isNew = !StaffManager.selectedStaffId;
      const url = isNew ? '/api/staff' : '/api/staff/' + encodeURIComponent(data.staff_id);
      const method = isNew ? 'POST' : 'PUT';
      const res = await fetch(url, {
        method: method,
        headers: StaffManager.authHeaders(),
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || '保存失败');
      }
      showToast(isNew ? '人员添加成功' : '人员信息已更新', 'success', 'Saved');
      StaffManager.selectedStaffId = data.staff_id;
      await StaffManager.loadStaff();
    } catch (err) {
      showToast('保存失败: ' + err.message, 'error', 'Save Failed');
    }
  },

  async deleteStaff(staffId) {
    if (!confirm('确定要删除该人员吗？')) return;
    try {
      const res = await fetch('/api/staff/' + encodeURIComponent(staffId), {
        method: 'DELETE',
        headers: StaffManager.authHeaders(),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || '删除失败');
      }
      showToast('人员已删除', 'success', 'Deleted');
      StaffManager.selectedStaffId = null;
      StaffManager.renderStaffDetail(null);
      await StaffManager.loadStaff();
    } catch (err) {
      showToast('删除失败: ' + err.message, 'error', 'Delete Failed');
    }
  },
};

// Add staff view metadata
viewMeta.staff = {
  eyebrow: "Staff",
  title: "人员管理",
  description: "管理系统人员信息，包括部门、岗位、设备分配和状态。",
};
localizedViewMeta.staff = {
  eyebrow: "Staff",
  title: "人员管理",
  description: "管理系统人员信息，包括部门、岗位、设备分配和状态。",
};

// Register staff elements and events
els.goStaffBtn = document.getElementById("goStaffBtn");

// Add staff to command deck update
const _origUpdateCommandDeck = updateCommandDeck;
updateCommandDeck = function () {
  _origUpdateCommandDeck();
  if (els.goStaffBtn) {
    els.goStaffBtn.classList.toggle("active", state.currentView === "staff");
  }
};

// Add staff to bindEvents
const _origBindEvents = bindEvents;
bindEvents = function () {
  _origBindEvents();
  if (els.goStaffBtn) {
    els.goStaffBtn.addEventListener("click", () => setView("staff"));
  }
};

// Add staff to keyboard shortcuts
document.addEventListener("keydown", (event) => {
  const tagName = event.target?.tagName;
  if (["INPUT", "TEXTAREA", "SELECT"].includes(tagName)) return;
  if (event.key === "6") {
    event.preventDefault();
    setView("staff");
  }
});

// Add staff layout rule
splitLayoutRules.staff = { minLeft: 360, minRight: 320 };

// Patch init to include StaffManager
const _origInit = init;
init = async function () {
  // Check login first
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = '/login';
    return;
  }
  await _origInit();
  StaffManager.init();
};

init();
