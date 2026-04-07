#!/bin/bash
# Docker镜像离线导出工具启动脚本 (Git Bash 环境)
cd "$(dirname "$0")"
py main.py "$@"