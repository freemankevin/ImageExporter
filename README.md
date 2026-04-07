# Docker Image Exporter

Docker镜像离线导出工具，支持 AMD64/ARM64 双架构。

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

py main.py            # 正常模式
py main.py -D         # 调试模式
py main.py --clean    # 清理缓存
py main.py --clean-data # 清理旧数据
```

## 支持的镜像

- Elasticsearch
- Nginx
- Redis
- RabbitMQ
- MinIO
- Nacos
- GeoServer
- PostgreSQL-PostGIS

## 配置

编辑 `config.yaml` 配置组件和参数。