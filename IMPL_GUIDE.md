# HFSP 机器故障模拟 — 实现指南

## 一、项目现状（已完成）

| 模块 | 文件 | 状态 |
|------|------|------|
| HFSP 环境建模/解码 | `src/hfsp_environment.py` | ✅ |
| PSO + IG 求解算法 | `src/niching_pso.py` + `src/iterated_greedy.py` | ✅ |
| 多智能体协同求解 | `src/multimodal_hfsp_solver.py` | ✅ |
| 多模态档案库 | `src/multimodal_hfsp_solver.py` | ✅ |
| 结果分析 | `src/solver_analysis.py` | ✅ |
| Web 后端（求解接口） | `src/web_app.py` | ✅ |
| 登录认证 | `src/auth.py` + `src/database.py` | ✅ |
| 人员管理 API | `src/web_app.py` | ✅ |
| 前端页面（5个视图） | `web/index.html` + `web/app.js` | ✅ |
| 动态甘特图回放 | `web/app.js` | ✅ |
| **机器故障模拟重调度** | 3个文件都要改 | ❌ 待实现 |

---

## 二、机器编号说明

HFSP 里机器用 **(stage_id, machine_id)** 定位，machine_id 在每个阶段从 0 重新编：

```
machines_per_stage = [2, 3, 2, 3]

Stage 0（stage_id=0）: M0, M1       → 甘特图: S1-M1, S1-M2
Stage 1（stage_id=1）: M0, M1, M2  → 甘特图: S2-M1, S2-M2, S2-M3
Stage 2（stage_id=2）: M0, M1       → 甘特图: S3-M1, S3-M2
Stage 3（stage_id=3）: M0, M1, M2  → 甘特图: S4-M1, S4-M2, S4-M3
```

**故障原理**：把故障机器在所有工件上的加工时间改为 999999，调度器永远不会选它。

---

## 三、需要改的三个文件

### 3.1 `src/web_app.py` — 加接口

在 `class SolveRequest` 之后加两个 Model：

```python
class FaultPayload(BaseModel):
    stage_id: int = Field(ge=0)
    machine_id: int = Field(ge=0)

class RescheduleRequest(BaseModel):
    instance: dict[str, Any]
    fault: FaultPayload
    config: SolverConfigPayload = Field(default_factory=SolverConfigPayload)
    mode: str = Field(default="basic_pso_ig")
```

在 `POST /api/solve` 之后加接口：

```python
@app.post("/api/reschedule")
def reschedule(request: RescheduleRequest) -> dict[str, Any]:
    try:
        from hfsp_environment import HFSPEnvironment
        env = HFSPEnvironment.from_dict(request.instance)
        stage_id = request.fault.stage_id
        machine_id = request.fault.machine_id
        if stage_id >= env.n_stages:
            raise ValueError(f"stage_id {stage_id} 超出范围")
        if machine_id >= env.machines_per_stage[stage_id]:
            raise ValueError(f"machine_id {machine_id} 超出范围")
        if env.machines_per_stage[stage_id] <= 1:
            raise ValueError(f"Stage {stage_id} 只有 1 台机器，无法模拟故障")
        _BIG = 999999
        new_pt = [
            [
                [_BIG if (s == stage_id and m == machine_id)
                 else env.processing_times[j][s][m]
                 for m in range(env.machines_per_stage[s])]
                for s in range(env.n_stages)
            ]
            for j in range(env.n_jobs)
        ]
        payload = dict(request.instance)
        payload["processing_times"] = new_pt
        payload["name"] = f"{request.instance.get('name','instance')}_fault_S{stage_id+1}M{machine_id+1}"
        config = SolverConfig(**request.config.model_dump())
        result = solve_instance(payload, config=config, mode=request.mode)
        result["fault"] = {"stage_id": stage_id, "machine_id": machine_id}
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"重调度失败: {exc}") from exc
```

---

### 3.2 `web/index.html` — 加面板

在动态甘特图页（`data-view-page="schedule"`）的 `realtime-panel` 里，  
找到 Job Status 那个 `<article>` 结束标签 `</article>` 后，紧接着加：

```html
<article class="realtime-card resizable-card">
  <p class="eyebrow">Fault Simulation</p>
  <div class="fault-sim-panel">
    <div class="control-group">
      <label for="faultStageSelect">故障阶段</label>
      <select id="faultStageSelect"><option value="">-- 选择阶段 --</option></select>
    </div>
    <div class="control-group">
      <label for="faultMachineSelect">故障机器</label>
      <select id="faultMachineSelect" disabled><option value="">-- 先选阶段 --</option></select>
    </div>
    <button id="faultSimBtn" class="primary-btn"
            style="width:100%;margin-top:8px;" disabled>
      模拟故障并重调度
    </button>
    <div id="faultSimResult" style="margin-top:8px;"></div>
  </div>
</article>
```

---

### 3.3 `web/app.js` — 加逻辑（4处改动）

**改动1**：在 `els` 对象的 `archiveContainer` 行后加：
```javascript
faultStageSelect: document.getElementById("faultStageSelect"),
faultMachineSelect: document.getElementById("faultMachineSelect"),
faultSimBtn: document.getElementById("faultSimBtn"),
faultSimResult: document.getElementById("faultSimResult"),
```

**改动2**：在 `renderCurrentMode` 函数之前加三个函数：
```javascript
function populateFaultSelectors() {
  const instance = state.currentInstance;
  if (!els.faultStageSelect || !instance?.machines_per_stage) return;
  els.faultStageSelect.innerHTML = '<option value="">-- 选择阶段 --</option>';
  instance.machines_per_stage.forEach((count, stageId) => {
    if (count >= 2) {
      const opt = document.createElement("option");
      opt.value = String(stageId);
      opt.textContent = `Stage ${stageId + 1}（${count} 台机器）`;
      els.faultStageSelect.appendChild(opt);
    }
  });
  els.faultMachineSelect.innerHTML = '<option value="">-- 先选阶段 --</option>';
  els.faultMachineSelect.disabled = true;
  els.faultSimBtn.disabled = true;
  if (els.faultSimResult) els.faultSimResult.innerHTML = "";
}

function updateFaultMachineSelect() {
  const stageId = Number.parseInt(els.faultStageSelect.value, 10);
  const instance = state.currentInstance;
  if (Number.isNaN(stageId) || !instance) {
    els.faultMachineSelect.innerHTML = '<option value="">-- 先选阶段 --</option>';
    els.faultMachineSelect.disabled = true;
    els.faultSimBtn.disabled = true;
    return;
  }
  const count = instance.machines_per_stage[stageId];
  els.faultMachineSelect.innerHTML = '<option value="">-- 选择机器 --</option>';
  for (let i = 0; i < count; i += 1) {
    const opt = document.createElement("option");
    opt.value = String(i);
    opt.textContent = `M${i + 1}（S${stageId + 1}-M${i + 1}）`;
    els.faultMachineSelect.appendChild(opt);
  }
  els.faultMachineSelect.disabled = false;
  els.faultSimBtn.disabled = true;
}

async function rescheduleFault() {
  if (!state.result || !state.currentInstance) {
    showToast("请先完成求解", "error", "Fault Simulation"); return;
  }
  const stageId = Number.parseInt(els.faultStageSelect.value, 10);
  const machineId = Number.parseInt(els.faultMachineSelect.value, 10);
  if (Number.isNaN(stageId) || Number.isNaN(machineId)) {
    showToast("请选择故障阶段和机器", "error", "Fault Simulation"); return;
  }
  const orig = state.result.best_makespan;
  els.faultSimBtn.disabled = true;
  els.faultSimBtn.textContent = "重调度中...";
  if (els.faultSimResult)
    els.faultSimResult.innerHTML = '<span class="status-pill neutral">求解中...</span>';
  try {
    const resp = await fetch("/api/reschedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        instance: state.currentInstance,
        fault: { stage_id: stageId, machine_id: machineId },
        config: collectConfig(),
        mode: "basic_pso_ig",
      }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "重调度失败");
    const next = data.best_makespan;
    const delta = next - orig;
    const pct = ((delta / orig) * 100).toFixed(1);
    if (els.faultSimResult) {
      els.faultSimResult.innerHTML = `
        <div style="margin-top:6px;padding:10px;background:var(--surface-2,#f5f5f7);
                    border-radius:10px;font-size:13px;line-height:1.9;">
          <div style="display:flex;justify-content:space-between;">
            <span>原始 Makespan</span><strong>${formatNumber(orig)}</strong></div>
          <div style="display:flex;justify-content:space-between;color:#ff5f57;">
            <span>重调度后</span><strong>${formatNumber(next)}</strong></div>
          <div style="display:flex;justify-content:space-between;opacity:.6;font-size:12px;">
            <span>影响</span><span>+${formatNumber(delta)}（+${pct}%）</span></div>
          <div style="opacity:.45;font-size:11px;margin-top:3px;">
            S${stageId+1}-M${machineId+1} 已标记故障</div>
        </div>`;
    }
    renderGantt(data, true);
    preparePlayback(data);
    showToast(`重调度完成 ${formatNumber(orig)} → ${formatNumber(next)}（+${pct}%）`, "success", "Fault Rescheduled");
  } catch (err) {
    if (els.faultSimResult)
      els.faultSimResult.innerHTML = `<span class="status-pill error">${err.message}</span>`;
    showToast(err.message, "error", "Reschedule Failed");
  } finally {
    els.faultSimBtn.disabled = false;
    els.faultSimBtn.textContent = "模拟故障并重调度";
  }
}
```

**改动3**：在 `renderCurrentMode` 的 `preparePlayback(scheduleResult);` 后加一行：
```javascript
populateFaultSelectors();
```

**改动4**：在 `bindEvents()` 里 `els.resetPlaybackBtn` 那行后加：
```javascript
if (els.faultStageSelect)
  els.faultStageSelect.addEventListener("change", updateFaultMachineSelect);
if (els.faultMachineSelect)
  els.faultMachineSelect.addEventListener("change", () => {
    if (els.faultSimBtn) els.faultSimBtn.disabled = els.faultMachineSelect.value === "";
  });
if (els.faultSimBtn)
  els.faultSimBtn.addEventListener("click", rescheduleFault);
```

---

## 四、演示步骤

1. 启动服务：`python src/web_app.py`，浏览器打开 `http://127.0.0.1:8000`
2. 加载 `benchmark_carlier_09.json`（4阶段，每阶段2~3台机器）
3. 进入"求解中心"，点击"开始求解"，等待完成
4. 进入"动态甘特图"页面
5. 右侧面板 **Fault Simulation**：选择阶段 → 选择机器 → 点击"模拟故障并重调度"
6. 甘特图自动更新，面板显示新旧 Makespan 对比

---

## 五、推荐测试 Benchmark

`benchmark_carlier_09.json`：
- 10 个工件，4 个阶段
- `machines_per_stage = [2, 3, 2, 3]`
- 所有阶段都有 ≥2 台机器，任意机器都可以模拟故障
