#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Erro: nenhum interpretador Python disponível (python3/python)." >&2
  exit 1
fi

if [ -f data/raw/aeat15tab/15Act19_01.xls ]; then
  echo "[0/4] Extraindo tabela 19.1 do AEAT-2015 (Espírito Santo)..."
  "$PYTHON_BIN" src/00_extract_aeat.py
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
