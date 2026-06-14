#!/bin/bash
# Detached orchestrator: runs every e2e_*.py serially, captures status, uploads to S3.
# Designed to run via SSM RunCommand and survive the controlling shell exiting.
set -uo pipefail
# SSM RunCommand strips HOME — set it explicitly. Default to /root since SSM runs as root.
: "${HOME:=/root}"
ROOT=$HOME/agentcore-tests
cd "$ROOT"
source .venv/bin/activate

RUN_TS=$(date -u +%Y%m%dT%H%M%SZ)
export AGENTCORE_TESTS_RUN=$RUN_TS
export AGENTCORE_TESTS_ROOT=$ROOT
RUN_DIR=$ROOT/results/$RUN_TS
LOG_DIR=$ROOT/logs/$RUN_TS
mkdir -p "$RUN_DIR" "$LOG_DIR"
ORCH_LOG=$LOG_DIR/_orchestrator.log
exec > >(tee -a "$ORCH_LOG") 2>&1

echo "=== orchestrator start @ $RUN_TS ==="
echo "ROOT=$ROOT"
echo "PY=$(which python)"
echo "BOTO3=$(python -c 'import boto3; print(boto3.__version__)')"

TESTS=(
  "e2e_0_validate_codeblocks.py"
  "e2e_e_codeinterp.py"
  "e2e_d_identity_registry.py"
  "e2e_a_runtime.py"
)

for t in "${TESTS[@]}"; do
  echo
  echo "===== running $t ====="
  if [ -f "$ROOT/scripts/$t" ]; then
    python "$ROOT/scripts/$t"
    echo "[exit=$? for $t]"
  else
    echo "MISSING: $ROOT/scripts/$t"
  fi
done

echo
echo "=== finalize ==="
python "$ROOT/scripts/finalize.py"
echo "=== orchestrator done @ $(date -u +%FT%TZ) ==="
