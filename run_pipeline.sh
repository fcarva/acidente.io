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

echo "[1/8] Preparando dados de acidentes..."
"$PYTHON_BIN" src/01_data_prep.py

echo "[2/8] Calculando modelo insumo-produto e indicadores principais..."
"$PYTHON_BIN" src/02_io_model.py

echo "[3/8] Executando extração hipotética (HEM)..."
"$PYTHON_BIN" src/03_hem_analysis.py

echo "[4/8] Gerando visualização em quadrantes..."
"$PYTHON_BIN" src/04_viz.py

echo "[5/8] Análise de sensibilidade Monte Carlo..."
"$PYTHON_BIN" src/05_sensibilidade.py

echo "[6/8] Modelo fechado (Type II)..."
"$PYTHON_BIN" src/06_modelo_fechado.py

echo "[7/8] Campo de influência (Sonis-Hewings)..."
"$PYTHON_BIN" src/07_campo_influencia.py

echo "[8/8] Decomposição da pegada por componente de demanda final..."
"$PYTHON_BIN" src/08_decomposicao_demanda.py

echo "Pipeline concluído com sucesso."
