## ImageExporter

[English](README_EN.md) | 简体中文

**ImageExporter** 是一个高效的工具，专为离线安装部署场景设计。它能够自动检查、下载并导出 Docker 镜像的最新版本，为中间件和服务环境的镜像管理提供了便捷的一键式解决方案。
通过该工具，您可以快速获取最新的中间件镜像版本，并将其制作为离线可用的镜像文件，以便在无网络环境下实现高效部署。

### 目录结构

```
ImageExporter/
├── data/
│   ├── versions/     # 版本信息文件
│   └── images/       # 导出的镜像文件
├── logs/             # 日志文件
├── src/              # 源代码
└── tests/            # 测试代码
```

### 使用说明

1. 将历史版本文件放入 `data/versions` 目录（可选）
2. 运行程序：`python main.py`
3. 导出的镜像文件将保存在 `data/images/日期/架构/` 目录下

### 开发说明

1. 克隆仓库：`git clone <repository_url>`
2. 安装依赖：`pip install -r requirements.txt`
3. 运行测试：`python -m pytest tests/`

### 清理工具

使用 `clean.py` 进行清理：
```bash
python clean.py -a    # 清理所有内容
python clean.py -c    # 只清理缓存
python clean.py -v    # 清理今天的版本文件
```

### 依赖要求

- Python 3.8+
- Docker
- 详细依赖见 requirements.txt

### 许可证

[MIT License](LICENSE)
