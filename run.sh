#!/usr/bin/env bash
# Linux 启动脚本：使用项目 .venv 运行 Pi Agent FastAPI
#
# 用法:
#   bash run.sh              # 生产模式（0.0.0.0:8000, 2 workers）
#   bash run.sh --dev        # 开发模式（127.0.0.1:8000, --reload）
#   HOST=0.0.0.0 PORT=9000 WORKERS=4 bash run.sh
#
# 首次部署请先:
#   cp .env.example .env && vim .env
#   python3.12 -m venv .venv
#   .venv/bin/pip install -U pip
#   .venv/bin/pip install -e ".[dev,ml,top5]"
#   .venv/bin/playwright install chromium
#   .venv/bin/playwright install-deps chromium

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VENV_PYTHON="${ROOT}/.venv/bin/python"
VENV_UVICORN="${ROOT}/.venv/bin/uvicorn"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-2}"
DEV_MODE=false

for arg in "$@"; do
  case "$arg" in
    --dev) DEV_MODE=true ;;
    -h|--help)
      sed -n '2,16p' "$0"
      exit 0
      ;;
    *)
      echo "未知参数: $arg（可用 --dev / --help）" >&2
      exit 1
      ;;
  esac
done

if [[ ! -x "$VENV_UVICORN" ]]; then
  echo "错误: 未找到 ${VENV_UVICORN}" >&2
  echo "请先创建虚拟环境并安装依赖:" >&2
  echo "  python3.12 -m venv .venv" >&2
  echo "  .venv/bin/pip install -e \".[dev,ml,top5]\"" >&2
  exit 1
fi

if [[ ! -f "${ROOT}/.env" ]]; then
  echo "警告: 未找到 .env，将使用环境变量或默认值（建议 cp .env.example .env）" >&2
fi

mkdir -p "${ROOT}/.data" "${ROOT}/output/gemini-images" 2>/dev/null || true

echo ">>> 工作目录: ${ROOT}"
echo ">>> Python:   $("$VENV_PYTHON" --version)"
echo ">>> 监听:     ${HOST}:${PORT}"

if [[ "$DEV_MODE" == true ]]; then
  echo ">>> 模式:     开发 (--reload)"
  exec "$VENV_UVICORN" app.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --reload
else
  echo ">>> 模式:     生产 (workers=${WORKERS})"
  exec "$VENV_UVICORN" app.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --workers "${WORKERS}"
fi
