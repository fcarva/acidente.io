#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Preparando dados de acidentes..."
python3 src/01_data_prep.py

echo "[2/4] Calculando modelo insumo-produto e indicadores principais..."
python3 src/02_io_model.py

echo "[3/4] Executando extração hipotética (HEM)..."
python3 src/03_hem_analysis.py

echo "[4/4] Gerando visualização em quadrantes..."
python3 src/04_viz.py

echo "Pipeline concluído com sucesso."
