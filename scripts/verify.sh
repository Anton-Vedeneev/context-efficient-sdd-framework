#!/usr/bin/env bash
set -euo pipefail

echo "[verify] Context-Efficient SDD verification entry point"
echo "[verify] Replace placeholder checks with project-specific commands."

failed=0

echo
echo "==> git diff --check"
if git diff --check; then
  echo "[ok] git diff --check"
else
  echo "[fail] git diff --check"
  failed=1
fi

if [[ "$failed" -ne 0 ]]; then
  echo "[verify] FAILED"
  exit 1
fi

echo "[verify] PASSED"
