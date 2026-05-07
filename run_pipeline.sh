#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

echo "[1/4] Preparando dados de acidentes..."
"$PYTHON_BIN" src/01_data_prep.py

echo "[2/4] Calculando modelo insumo-produto e indicadores principais..."
"$PYTHON_BIN" src/02_io_model.py

echo "[3/4] Executando extração hipotética (HEM)..."
"$PYTHON_BIN" src/03_hem_analysis.py

echo "[4/4] Gerando visualização em quadrantes..."
"$PYTHON_BIN" src/04_viz.py

echo "Pipeline concluído com sucesso."
