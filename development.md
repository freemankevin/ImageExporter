# 开发指南

## 目录结构说明

- `data/`：数据目录
  - `versions/`：存放版本信息文件
  - `images/`：存放导出的镜像文件
- `logs/`：日志文件目录
- `src/`：源代码目录
  - `config/`：配置相关代码
  - `services/`：核心服务代码
  - `utils/`：工具函数
- `tests/`：测试代码目录

## 开发环境设置

1. 创建虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 安装开发依赖：
   ```bash
   pip install -r requirements-dev.txt
   ```

## 目录说明

- `data/versions/`：存放历史版本文件，格式为 `latest-YYYYMMDD.txt`
- `data/images/`：存放导出的镜像文件，按日期和架构分类
- `logs/`：存放运行日志，格式为 `image_exporter_YYYYMMDD.log`

## 开发工具

### 清理工具 (clean.py)

项目根目录提供了清理工具，用于清理各类临时文件和缓存：

```bash
# 显示帮助信息
python clean.py

# 清理所有内容（保留历史版本文件）
python clean.py -a

# 清理特定内容
python clean.py -c    # 清理 Python 缓存
python clean.py -s    # 清理状态文件
python clean.py -o    # 清理输出目录
python clean.py -v    # 清理今天的版本文件
python clean.py -l    # 清理日志文件

# 组合清理多个内容
python clean.py -c -s -l  # 清理缓存、状态和日志
```

注意事项：
- 版本文件清理只会删除今天的文件，保留历史文件用于版本比较
- 日志清理会自动处理文件占用问题
- 建议在开始新的操作前执行清理

## 测试

运行所有测试：
```bash
pytest
```

运行特定测试：
```bash
pytest tests/test_version_utils.py
```

## 代码风格

项目使用 PEP 8 代码风格指南。建议使用 flake8 进行代码检查：
```bash
flake8 .
```

## 提交规范

提交信息格式：
```
<type>: <description>

[optional body]
```

类型（type）：
- feat: 新功能
- fix: 修复
- docs: 文档更新
- style: 代码风格
- refactor: 重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

## 项目结构

```
ImageExporter/
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── docker_hub.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_fetch.py
│   │   ├── image_pull.py
│   │   └── image_update.py
│   └── utils/
│       ├── __init__.py
│       ├── docker_utils.py
│       ├── file_utils.py
│       ├── logger.py
│       ├── paths.py
│       └── version_utils.py
├── config/
│   ├── __init__.py
│   └── config.py
├── tests/
│   └── ...
├── data/
│   ├── versions/     # 版本文件目录
│   └── output/       # 输出目录
├── logs/             # 日志目录
├── clean.py          # 清理工具
├── main.py
├── requirements.txt
└── requirements-dev.txt
```

## 开发流程

1. 创建新分支
2. 开发前执行清理 `python clean.py -a`
3. 进行开发和测试
4. 运行代码风格检查
5. 提交代码（遵循提交规范）
6. 创建合并请求

## 调试建议

1. 使用 clean.py 工具清理环境
2. 检查日志文件获取详细信息
3. 使用 pytest 的 -v 参数获取详细测试信息
4. 使用 Python 调试器 (pdb) 进行断点调试