from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from multimodal_hfsp_solver import SolverConfig, solve_instance
from database import init_db, get_db
from auth import login as auth_login, verify_token, logout as auth_logout


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
WEB_DIR = PROJECT_ROOT / "web"


class SolverConfigPayload(BaseModel):
    population_size: int = Field(default=40, ge=4, le=300)
    max_generations: int = Field(default=60, ge=1, le=1000)
    w_max: float = Field(default=0.9, ge=0.0, le=2.0)
    w_min: float = Field(default=0.4, ge=0.0, le=2.0)
    c1: float = Field(default=1.5, ge=0.0, le=5.0)
    c2: float = Field(default=1.5, ge=0.0, le=5.0)
    k_neighbors: int = Field(default=3, ge=1, le=20)
    stagnation_threshold: int = Field(default=10, ge=1, le=100)
    mutation_probability: float = Field(default=0.12, ge=0.0, le=1.0)
    niche_distance_threshold: int = Field(default=3, ge=1, le=100)
    destruction_ratio: float = Field(default=0.3, ge=0.05, le=0.9)
    ig_max_iterations: int = Field(default=20, ge=1, le=500)
    cooling_rate: float = Field(default=0.95, ge=0.5, le=0.999)
    makespan_tolerance: float = Field(default=0.01, ge=0.0, le=1.0)
    permutation_distance_threshold: int = Field(default=3, ge=1, le=100)
    machine_assignment_threshold: int = Field(default=1, ge=0, le=100)
    seed: int | None = 20260326


class SolveRequest(BaseModel):
    instance: dict[str, Any]
    config: SolverConfigPayload = Field(default_factory=SolverConfigPayload)
    mode: str = Field(default="compare")


app = FastAPI(title="HFSP Visual Studio", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

# 初始化数据库
init_db()


# ---------------------------------------------------------------------------
# 认证依赖
# ---------------------------------------------------------------------------

def get_current_user(request: Request) -> dict[str, Any]:
    """从 Authorization: Bearer <token> 头部获取当前用户信息。"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供有效的认证令牌")
    token = auth_header[7:]
    user = verify_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    return user


def _benchmark_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/benchmarks")
def list_benchmarks() -> dict[str, Any]:
    benchmarks = []
    for path in sorted(BENCHMARKS_DIR.glob("*.json")):
        payload = _benchmark_payload(path)
        benchmarks.append(
            {
                "file_name": path.name,
                "name": payload.get("name", path.stem),
                "n_jobs": payload.get("n_jobs"),
                "n_stages": payload.get("n_stages"),
                "machines_per_stage": payload.get("machines_per_stage"),
            }
        )
    return {"benchmarks": benchmarks}


@app.get("/api/benchmarks/{file_name}")
def get_benchmark(file_name: str) -> dict[str, Any]:
    path = BENCHMARKS_DIR / file_name
    if not path.exists() or path.suffix.lower() != ".json":
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return _benchmark_payload(path)


@app.post("/api/solve")
def solve(request: SolveRequest) -> dict[str, Any]:
    try:
        config = SolverConfig(**request.config.model_dump())
        return solve_instance(request.instance, config=config, mode=request.mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"求解失败: {exc}") from exc


@app.get("/login", include_in_schema=False)
def login_page() -> FileResponse:
    return FileResponse(WEB_DIR / "login.html")


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


# ---------------------------------------------------------------------------
# 认证 API
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def api_login(request: LoginRequest) -> dict[str, Any]:
    """用户登录，返回 token 和用户信息。"""
    token = auth_login(request.username, request.password)
    if token is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    user = verify_token(token)
    return {"token": token, "user": user}


@app.post("/api/auth/logout")
def api_logout(request: Request) -> dict[str, str]:
    """用户退出，清除 token。"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        auth_logout(token)
    return {"message": "已退出"}


@app.get("/api/auth/me")
def api_me(request: Request) -> dict[str, Any]:
    """获取当前登录用户信息。"""
    user = get_current_user(request)
    return user


# ---------------------------------------------------------------------------
# 人员管理 API
# ---------------------------------------------------------------------------

class StaffCreate(BaseModel):
    staff_id: str
    name: str
    department: str = ""
    phone: str = ""
    position: str = ""
    device_ids: list[str] = []


class StaffUpdate(BaseModel):
    name: str | None = None
    department: str | None = None
    phone: str | None = None
    position: str | None = None
    device_ids: list[str] | None = None
    status: str | None = None


@app.get("/api/staff")
def api_list_staff(request: Request) -> dict[str, Any]:
    """获取所有人员列表。"""
    get_current_user(request)
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM staff ORDER BY id").fetchall()
        staff_list = []
        for row in rows:
            item = dict(row)
            try:
                item["device_ids"] = json.loads(item["device_ids"])
            except (ValueError, TypeError):
                item["device_ids"] = []
            staff_list.append(item)
        return {"staff": staff_list}
    finally:
        conn.close()


@app.get("/api/staff/{staff_id}")
def api_get_staff(staff_id: str, request: Request) -> dict[str, Any]:
    """获取单个人员详情。"""
    get_current_user(request)
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM staff WHERE staff_id = ?", (staff_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="人员不存在")
        item = dict(row)
        try:
            item["device_ids"] = json.loads(item["device_ids"])
        except (ValueError, TypeError):
            item["device_ids"] = []
        return item
    finally:
        conn.close()


@app.post("/api/staff")
def api_create_staff(body: StaffCreate, request: Request) -> dict[str, str]:
    """新增人员。"""
    get_current_user(request)
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO staff (staff_id, name, department, phone, position, device_ids) VALUES (?, ?, ?, ?, ?, ?)",
            (body.staff_id, body.name, body.department, body.phone, body.position, json.dumps(body.device_ids)),
        )
        conn.commit()
        return {"message": "人员创建成功"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"创建失败: {exc}") from exc
    finally:
        conn.close()


@app.put("/api/staff/{staff_id}")
def api_update_staff(staff_id: str, body: StaffUpdate, request: Request) -> dict[str, str]:
    """更新人员信息。"""
    get_current_user(request)
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM staff WHERE staff_id = ?", (staff_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="人员不存在")

        updates: list[str] = []
        params: list[Any] = []

        if body.name is not None:
            updates.append("name = ?")
            params.append(body.name)
        if body.department is not None:
            updates.append("department = ?")
            params.append(body.department)
        if body.phone is not None:
            updates.append("phone = ?")
            params.append(body.phone)
        if body.position is not None:
            updates.append("position = ?")
            params.append(body.position)
        if body.device_ids is not None:
            updates.append("device_ids = ?")
            params.append(json.dumps(body.device_ids))
        if body.status is not None:
            updates.append("status = ?")
            params.append(body.status)

        if not updates:
            return {"message": "没有需要更新的字段"}

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(staff_id)

        conn.execute(
            f"UPDATE staff SET {', '.join(updates)} WHERE staff_id = ?",
            params,
        )
        conn.commit()
        return {"message": "人员更新成功"}
    finally:
        conn.close()


@app.delete("/api/staff/{staff_id}")
def api_delete_staff(staff_id: str, request: Request) -> dict[str, str]:
    """删除人员。"""
    get_current_user(request)
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM staff WHERE staff_id = ?", (staff_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="人员不存在")
        return {"message": "人员删除成功"}
    finally:
        conn.close()


if __name__ == "__main__":
    host = os.getenv("HFSP_HOST", "127.0.0.1")
    port = int(os.getenv("HFSP_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, reload=False)
