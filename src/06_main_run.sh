#!/usr/bin/env bash
# Main judge runs under the $10 plan (see LOG.md). One process per gateway host so rate limits don't collide.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=lib:src
R="python3 src/06_run_judges.py"
( $R --judge gpt-5 --prompt P1 --set clear --n 500 && $R --judge gpt-5 --prompt P3 --set clear --n 250 && python3 src/04b_title_baseline.py && $R --judge gpt-5 --prompt P2 --set clear --n 250 ) > judges/run_openai.log 2>&1 &
( $R --judge haiku-4.5 --prompt P1 --set clear --n 500 && $R --judge haiku-4.5 --prompt P3 --set clear --n 250 ) > judges/run_claude.log 2>&1 &
( $R --judge gemini-2.5-flash --prompt P1 --set clear --n 500 && $R --judge gemini-2.5-flash --prompt P3 --set clear --n 500 && $R --judge gemini-2.5-flash --prompt P1 --set close --n 200 ) > judges/run_gemini.log 2>&1 &
wait
python3 -c "from judge_client import total_spend; print(f'TOTAL SPEND \${total_spend():.4f}')"
