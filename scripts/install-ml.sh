#!/usr/bin/env bash
# ML 扩展安装脚本（解决 pkuseg 等包的构建问题）
set -euo pipefail

cd "$(dirname "$0")/.."

echo ">>> 安装基础 + dev + ml + top5 依赖..."
pip install -e ".[dev,ml,top5]"

echo ">>> 完成（pkuseg 不支持 Python 3.12+，请使用 jieba 分词）"
