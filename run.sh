#!/usr/bin/env bash
# Linux 启动脚本：使用当前 PATH 中的 Python 运行 Pi Agent FastAPI
#
# 用法:
#   bash run.sh              # 生产模式，自动使用系统 PATH 中的 python3 / python
#   bash run.sh --dev        # 开发模式（--reload）
#   HOST=0.0.0.0 PORT=9000 WORKERS=4 bash run.sh
#   PYTHON=python3.12 bash run.sh   # 可选：手动指定解释器
#
# 首次部署请先:
#   cp .env.example .env && vim .env
#   pip install -e ".[dev,ml,top5]"
#   playwright install chromium
#   playwright install-deps chromium

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
  elif command -v python >/dev/null 2>&1; then
    PYTHON=python
  else
    echo "错误: 未找到 python3 或 python，请先安装 Python 3.11+" >&2
    exit 1
  fi
fi
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-2}"
DEV_MODE=false

for arg in "$@"; do
  case "$arg" in
    --dev) DEV_MODE=true ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
    *)
      echo "未知参数: $arg（可用 --dev / --help）" >&2
      exit 1
      ;;
  esac
done

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "错误: 未找到 Python 解释器: ${PYTHON}" >&2
  exit 1
fi
if ! "$PYTHON" -c "import uvicorn" >/dev/null 2>&1; then
  echo "错误: 当前 Python 未安装 uvicorn" >&2
  echo "请先安装依赖: pip install -e \".[dev,ml,top5]\"" >&2
  exit 1
fi

if [[ ! -f "${ROOT}/.env" ]]; then
  echo "警告: 未找到 .env，将使用环境变量或默认值（建议 cp .env.example .env）" >&2
fi

mkdir -p "${ROOT}/.data" "${ROOT}/output/gemini-images" 2>/dev/null || true

echo ">>> 工作目录: ${ROOT}"
echo ">>> Python:   $("$PYTHON" --version) ($("$PYTHON" -c 'import sys; print(sys.executable)'))"
echo ">>> 监听:     ${HOST}:${PORT}"

if [[ "$DEV_MODE" == true ]]; then
  echo ">>> 模式:     开发 (--reload)"
  exec "$PYTHON" -m uvicorn app.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --reload
else
  echo ">>> 模式:     生产 (workers=${WORKERS})"
  exec "$PYTHON" -m uvicorn app.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --workers "${WORKERS}"
fi
