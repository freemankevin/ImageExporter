# AGENTS.md — ImageExporter 项目指南

> 本文件面向 AI 编码助手。阅读本文件前，默认你对本项目一无所知。

---

## 项目概述

**ImageExporter**（容器镜像离线导出工具）是一个用于从 GHCR（GitHub Container Registry）拉取容器镜像并导出为离线压缩包（`.tar.gz`）的 Python CLI 工具。支持 AMD64 / ARM64 双架构，兼容 Docker 和 Podman 运行时。

- **版本**：`2.0.0`
- **主入口**：`main.py`
- **启动脚本**：`run.sh`（Git Bash 环境）
- **配置文件**：`config.yaml`
- **依赖声明**：`requirements.txt`
- **Python 版本**：3.12+

### 核心能力

1. 通过 GitHub Packages API 查询 GHCR 镜像标签列表，按正则过滤获取最新版本。
2. 与本地历史版本记录（`data/versions/latest-*.json`）对比，识别需要更新的镜像。
3. 使用多线程并发拉取镜像（`docker/podman pull`）并导出为 gzip 压缩的 tar 包。
4. 支持断点续传：任务状态保存在 `logs/task_state_*.json`，中断后下次运行自动跳过已完成的任务。
5. 失败任务支持指数退避重试，也可通过 `--retry-failed` 单独重试。
6. 生成 JSON/HTML 双格式报告，并为失败镜像生成可手动执行的 Bash 脚本。

### 支持的镜像组件

配置中预定义了 9 个组件：Elasticsearch、MinIO、Nacos、Nginx、RabbitMQ、Redis、GeoServer、PostgreSQL-PostGIS、PostgreSQL-Backup。全部通过 `freemankevin/*` 命名空间从 GHCR 拉取。

---

## 技术栈与依赖

| 类别 | 技术/库 |
|------|---------|
| 语言 | Python 3.12+ |
| 容器运行时 | Docker 或 Podman（自动检测，优先 Podman）|
| HTTP 请求 | `requests` + `urllib3`（带重试策略）|
| 容器客户端 | `docker`（Python SDK）|
| 配置解析 | `pyyaml` |
| 终端输出 | `rich`（进度条、日志着色）|
| 环境变量 | `python-dotenv`（读取 `.env`）|

### 完整依赖（requirements.txt）

```
requests>=2.31.0,<3.0.0
beautifulsoup4>=4.12.3,<5.0.0
urllib3>=2.2.2,<3.0.0
pyyaml>=6.0.1,<7.0.0
docker>=7.0.0,<8.0.0
rich>=13.0.0,<14.0.0
```

> 注意：`beautifulsoup4` 目前项目中未实际使用，但保留在依赖中。

---

## 项目结构

```
ImageExporter/
├── main.py                     # CLI 入口，参数解析与主流程调度
├── run.sh                      # Bash 启动脚本（Git Bash）
├── config.yaml                 # 组件、镜像路径、并发、超时等配置
├── requirements.txt            # Python 依赖
├── .env                        # 敏感凭证：GHCR_TOKEN / PAT_TOKEN
├── .gitignore                  # 忽略 __pycache__、data/、logs/、.env 等
├── README.md                   # 面向用户的快速入门
├── app/
│   ├── __init__.py             # 包初始化，定义 __version__ = "2.0.0"
│   ├── cli/
│   │   └── commands.py         # 清理命令：cache、data、all
│   ├── core/
│   │   ├── config.py           # 单例配置管理器（Config）、目录常量、镜像路径拼接
│   │   ├── logging.py          # 日志设置：文件 + Rich 控制台；QuietRichHandler 抑制进度条时的日志
│   │   └── shutdown.py         # 全局 threading.Event 用于优雅停止
│   ├── models/
│   │   ├── image.py            # ImageResult 数据模型
│   │   └── task.py             # TaskState：已完成/失败任务的 JSON 持久化
│   ├── services/
│   │   ├── exporter.py         # ImageExporter：主控类，串联版本检查、任务调度、报告生成
│   │   ├── docker_manager.py   # DockerManager：pull、export、digest 查询；优先 Podman
│   │   ├── docker_api.py       # ContainerRegistryAPI：通过 GitHub API 查询 GHCR 标签
│   │   └── version_manager.py  # VersionManager：历史版本文件读写、latest/update 列表保存
│   └── utils/
│       ├── helpers.py          # version_key、get_major_version、generate_manual_commands
│       ├── display.py          # 终端横幅、分隔线、字符串宽度处理
│       └── report_generator.py # generate_html_report：内联 CSS 的 HTML 报告生成
├── data/
│   ├── images/                 # 导出的 .tar.gz 镜像文件（按日期/架构分目录）
│   └── versions/               # 版本记录：latest-*.json、update-*.txt
└── logs/
    ├── exporter_YYYYMMDD.log   # 每日运行日志
    ├── task_state_*.json       # 任务断点状态
    ├── report_*.json / *.html  # 执行报告
    └── manual_commands_*.sh    # 失败镜像的手动执行脚本
```

---

## 配置说明（config.yaml）

```yaml
docker:
  timeout: 300           # 拉取/导出超时（秒）
  max_retries: 3         # 单任务最大重试次数
  retry_delay: 2         # 重试间隔基数（秒）

concurrency:
  max_workers: 10        # 线程池并发数
  max_global_retries: 10 # 全局批次重试上限
  retry_backoff_factor: 2 # 指数退避系数

validation:
  min_file_size: 1048576 # 最小有效文件大小（字节），默认 1MB

mirror:
  enabled: true
  ghcr_registry: "ghcr.io/"

components:
  <component_name>:
    name: <显示名称>
    image: <GHCR 路径，如 freemankevin/library/elasticsearch>
    tag_pattern: <正则表达式过滤标签>
    exclude_pattern: <可选，排除正则>
    latest_version: null # 运行时填充
    version_type: single | multiple  # single=仅取最新；multiple=按主版本各取最新
```

> **重要**：`image` 字段不包含 `ghcr.io/` 前缀，实际拉取时由 `get_mirrored_image()` 自动拼接。

---

## 运行方式

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基础运行

```bash
# 正常模式
py main.py

# 调试模式（输出 DEBUG 级别日志）
py main.py -D

# 仅拉取，不导出离线包
py main.py --no-export

# 指定架构
py main.py --arch amd64
py main.py --arch arm64
py main.py --arch all   # 默认
```

### 清理与重置

```bash
py main.py --clean        # 清理 __pycache__ 和 .pyc
py main.py --clean-data   # 清理 data/ 和 logs/ 目录
py main.py --clean-all    # 全面清理（以上全部）
py main.py --reset        # 清理当天的记录并重新执行
```

### 失败重试

```bash
py main.py --retry-failed # 跳过版本检查，仅重试之前失败的镜像
```

### Git Bash 快捷启动

```bash
./run.sh -D
```

---

## 代码风格与约定

### 文件头

每个 `.py` 文件必须包含以下文件头：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模块中文描述"""
```

### 命名规范

- 类名：`PascalCase`
- 函数/变量：`snake_case`
- 私有属性/方法：前缀 `_`
- 常量：`UPPER_CASE`

### 字符串与注释

- 项目内注释、文档字符串、日志输出、终端提示均使用**中文**。
- 不要使用英文注释替代现有中文注释风格。

### 路径处理

- 统一使用 `pathlib.Path`，禁止拼接字符串路径。
- 项目根目录常量定义在 `app/core/config.py` 的 `PROJECT_ROOT`。

### 日志与终端输出

- 日志通过 `app.core.logging.setup_logger()` 获取 `ImageExporter` 记录器。
- 终端用户可见的输出使用 `rich.console.Console` 或 `print()` 配合 `COLORS` / `ICONS` 字典。
- 进度条运行期间，通过 `QuietRichHandler.set_quiet(True)` 抑制日志打到控制台，但文件日志始终写入。

---

## 核心模块职责

### `app/services/exporter.py` — ImageExporter

主控类，生命周期如下：

1. `run()` → 打印横幅 → 列出组件 → 获取最新版本 → 对比历史版本 → 处理镜像 → 保存 SHA256 → 总结。
2. `get_latest_versions()` → 遍历组件，调用 `docker_api.get_versions()`。
3. `check_updates()` → 对比 `data/versions/latest-*.json` 中的历史版本与 SHA256，输出更新清单。
4. `process_images()` → 构建任务列表，跳过已完成的任务，使用 `ThreadPoolExecutor` 并发执行 `_process_single_image()`，失败任务按指数退避重试。
5. `_validate_images()` → 校验导出文件大小与命名，清理任务状态。
6. `_generate_summary_report()` → 输出 JSON + HTML 报告，以及 `manual_commands_*.sh`。

### `app/services/docker_manager.py` — DockerManager

- `detect_container_runtime()`：优先检测 `podman`，其次 `docker`。
- `pull_image()`：使用 `docker` Python SDK 的 `api.pull(..., platform=f"linux/{arch}")` 拉取镜像。
- `export_image()`：通过 `subprocess.Popen([runtime, "save", ...])` 管道输出到 `gzip.open(...)` 实现流式压缩导出。
- `get_image_digest()`：调用 `docker/podman inspect` 提取 `RepoDigests` 或 `Id` 的 sha256 值。

### `app/services/docker_api.py` — ContainerRegistryAPI

- 通过 GitHub Packages API (`api.github.com/users/{owner}/packages/container/{package}/versions`) 获取标签列表。
- 包名中的 `/` 需要替换为 `__`（已通过 `urllib.parse.quote` 处理）。
- 需要环境变量 `GHCR_TOKEN` 或 `PAT_TOKEN` 作为 `Authorization: Bearer`。
- 支持按 `tag_pattern`（包含正则）过滤，`exclude_pattern` 排除。

### `app/services/version_manager.py` — VersionManager

- `get_latest_history_file()`：查找 `data/versions/` 下最新的 `latest-*.json/.txt`（排除当前时间戳）。
- `load_history_versions()`：解析历史版本文件，返回 `{image_name: {major: {version, sha256}}}` 结构。
- `save_latest_versions()`：将本次运行结果写入 `latest-YYYYMMDD_HHMM.json`。

### `app/models/task.py` — TaskState

- 基于 JSON 文件的简单状态机，记录 `completed_tasks`（Set）和 `failed_tasks`（Dict）。
- 任务 ID 格式：`<full_image_name>:<version>:<arch>`，例如 `ghcr.io/freemankevin/library/nginx:1.27.0:amd64`。

---

## 断点续传与状态管理

- 每次运行会在 `logs/task_state_YYYYMMDD_HHMM.json` 创建新的状态文件。
- 如果任务被中断（Ctrl+C 或 SIGTERM），`ImageExporter._signal_handler()` 会将正在执行的任务标记为失败并保存状态，然后调用 `os._exit(0)` 立即退出。
- 下次运行时，状态文件中 `completed` 的任务会被跳过；`failed` 的任务可以通过 `--retry-failed` 重试。
- 如果所有任务最终成功，状态文件会被 `clear_state()` 删除。

---

## 安全与凭证

- **GitHub Token**：必须存放在项目根目录的 `.env` 文件中，变量名为 `GHCR_TOKEN` 或 `PAT_TOKEN`。`docker_api.py` 启动时通过 `python-dotenv` 加载。
- `.env` 已在 `.gitignore` 中忽略，**禁止将其提交到 Git**。
- Token 权限要求：至少具有 `read:packages` 权限以访问 GHCR 包版本 API。

---

## 测试策略

**当前项目没有自动化测试套件**（无 `pytest`、`unittest` 或 `tests/` 目录）。

验证改动的推荐方式：

1. **静态运行**：`py main.py --no-export` —— 仅查询版本和对比更新，不实际拉取镜像，可快速验证版本管理逻辑。
2. **单组件验证**：临时修改 `config.yaml`，只保留一个组件，运行 `py main.py -D` 观察完整流程。
3. **架构隔离**：`py main.py --arch amd64` 减少任务量，加速验证导出流程。
4. **失败重试验证**：手动制造一个失败任务（如断网后运行），再执行 `py main.py --retry-failed` 验证恢复逻辑。

---

## 常见修改场景

### 添加新镜像组件

1. 在 `config.yaml` 的 `components:` 下新增节点：
   ```yaml
   newapp:
     name: newapp
     image: freemankevin/namespace/newapp
     tag_pattern: "^[0-9]+\\.[0-9]+\\.[0-9]+$"
     latest_version: null
     version_type: single
   ```
2. 无需修改代码，主程序会读取配置并自动处理。

### 调整并发与重试

直接修改 `config.yaml` 中的 `concurrency` 和 `docker` 节，无需重启或重新打包。

### 修改报告样式

HTML 报告是内联 CSS 的纯字符串模板，位于 `app/utils/report_generator.py` 的 `generate_html_report()` 函数中。直接修改模板字符串即可。

### 升级依赖

修改 `requirements.txt` 中的版本约束后执行：

```bash
pip install -r requirements.txt
```

---

## 部署与运行环境

- **操作系统**：开发环境为 Windows（PowerShell / Git Bash），但代码兼容 Linux/macOS（通过 `os.name == 'nt'` 区分 `where`/`which`）。
- **容器运行时**：目标机器需要预装 Docker 或 Podman，且用户具有拉取镜像的权限。
- **网络**：需要访问 `api.github.com`（查询版本）和 `ghcr.io`（拉取镜像）。
- **存储**：导出镜像存放在 `data/images/YYYYMMDD/<arch>/`，注意磁盘空间。
