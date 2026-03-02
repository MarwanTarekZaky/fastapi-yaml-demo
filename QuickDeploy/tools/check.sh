#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> YAML Lint ..."
yamllint "$ROOT/config" || { echo "YAML lint failed"; exit 1; }

echo "==> Schema & rules validation ..."
python "$ROOT/tools/validate.py" || { echo "Validation failed"; exit 1; }

echo "All checks passed ✅"