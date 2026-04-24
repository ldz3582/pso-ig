# HFSP Docker 部署说明

## 1. 前置条件

需要本机已安装：

- Docker Desktop
- Docker Compose（Docker Desktop 已内置）

确认命令可用：

```bash
docker --version
docker compose version
```

## 2. 项目结构

Docker 相关文件：

- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- `.dockerignore`

容器启动后使用：

- `src/web_app.py` 作为 Web 服务入口
- `benchmarks/` 作为只读算例目录
- `output/`、`results/` 作为结果输出目录

## 3. 构建与启动

在项目根目录执行：

```bash
docker compose up --build -d
```

启动完成后访问：

- `http://127.0.0.1:8000`

健康检查接口：

- `http://127.0.0.1:8000/api/health`

## 4. 停止与删除

停止容器：

```bash
docker compose down
```

如果只想停止而不删除：

```bash
docker compose stop
```

## 5. 查看日志

实时查看日志：

```bash
docker compose logs -f
```

只看 Web 服务日志：

```bash
docker compose logs -f hfsp-web
```

## 6. 重新构建

代码或依赖有变更时：

```bash
docker compose up --build -d
```

如果要强制重新构建镜像：

```bash
docker compose build --no-cache
docker compose up -d
```

## 7. 数据目录说明

Compose 默认挂载：

- `./benchmarks:/app/benchmarks:ro`
- `./output:/app/output`
- `./results:/app/results`

含义：

- 本地新增 benchmark 后，容器内可直接读取
- 求解结果和图表会保存在宿主机当前项目目录
- 重启容器不会丢失输出结果

## 8. 常见问题

### 8.1 端口 8000 被占用

修改 `docker-compose.yml`：

```yaml
ports:
  - "8001:8000"
```

然后访问：

- `http://127.0.0.1:8001`

### 8.2 Docker Desktop 没启动

症状：

- `docker compose up` 报连接失败

处理：

- 先启动 Docker Desktop
- 再重新执行启动命令

### 8.3 镜像拉取或安装依赖慢

这是网络环境问题，不是项目问题。可稍后重试，或为 Docker 配置镜像源。

### 8.4 页面还是旧版本

浏览器执行一次强刷：

```text
Ctrl + F5
```

如果前端资源已更新，Compose 会重新挂载最新 `web/` 内容。

## 9. Windows 一键脚本

项目已附带：

- `start_hfsp_docker.bat`
- `stop_hfsp_docker.bat`

双击即可启动或停止 Docker 版服务。

## 10. 推荐命令汇总

启动：

```bash
docker compose up --build -d
```

查看日志：

```bash
docker compose logs -f hfsp-web
```

停止：

```bash
docker compose down
```
