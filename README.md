# Docker 镜像自动更新工具

用于自动检查、下载和导出 Docker 镜像的最新版本。

## 目录结构

```
ImageExporter/
├── data/
│   ├── versions/     # 版本文件目录
│   └── output/       # 输出目录
├── logs/             # 日志目录
├── src/              # 源代码
├── config/           # 配置文件
├── tests/            # 测试文件
├── clean.py          # 清理工具
├── main.py          # 主程序
└── requirements.txt  # 依赖清单
```

## 输出说明

程序会在 `output` 目录下创建以日期命名的文件夹，并按架构分类存储导出的镜像文件：

```
output/
  └── 20241202/
      ├── AMD64/
      │   └── elasticsearch_8.16.0_amd64_20241202.tar.gz
      └── ARM64/
          └── elasticsearch_8.16.0_arm64_20241202.tar.gz
```

## 日志说明

日志文件存储在 `logs` 目录下，按日期命名：
```
logs/
  └── image_exporter_20241202.log
```

## 开发指南

详细的开发说明请参考 [开发文档](development.md)。

## 常见问题

1. 如何修改并发下载数？
   - 在 `config.yaml` 中设置 `concurrent_downloads` 参数

2. 如何添加新的镜像支持？
   - 在 `config.py` 的 `DEFAULT_COMPONENTS` 中添加新的组件配置

3. 如何清理临时文件？
   - 使用 `clean.py` 工具，例如：`python clean.py -a`

4. 版本文件在哪里？
   - 在 `data/versions` 目录下，按日期命名

## 贡献指南

1. Fork 本仓库
2. 创建您的特性分支
3. 提交您的更改
4. 推送到您的分支
5. 创建新的 Pull Request

## License

[Apache License 2.0](LICENSE)