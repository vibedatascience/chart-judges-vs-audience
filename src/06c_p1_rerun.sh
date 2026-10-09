#!/usr/bin/env bash
# Pre-registered P1 rerun on all 2,000 clear pairs (see LOG.md 2026-10-09 PRE-REGISTRATION).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=lib:src
R="python3 src/06_run_judges.py"
( $R --judge gpt-5 --prompt P1 --set clear --n 2000 ) > judges/rerun_openai.log 2>&1 &
( $R --judge gemini-2.5-flash --prompt P1 --set clear --n 2000 ) > judges/rerun_gemini.log 2>&1 &
( $R --judge haiku-4.5 --prompt P1 --set clear --n 2000 && $R --judge sonnet-5.5 --prompt P1 --set clear --n 1000 ) > judges/rerun_claude.log 2>&1 &
( OMP_NUM_THREADS=6 python3 src/08a_image_features.py ) > judges/rerun_features.log 2>&1 &
wait
python3 -c "from judge_client import total_spend; print(f'TOTAL SPEND \${total_spend():.4f}')"
