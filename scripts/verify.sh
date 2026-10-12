#!/usr/bin/env bash
set -euo pipefail

echo "[verify] Context-Efficient SDD verification entry point"

root="$(cd "$(dirname "$0")/.." && pwd)"
template_state="$root/.framework/project-state.yaml"
template_ledger="$root/.framework/metrics/ledger.yaml"
if [[ -f "$root/.local/project-state.yaml" ]]; then
  state="$root/.local/project-state.yaml"
  ledger="$root/.local/metrics/ledger.yaml"
else
  state="$template_state"
  ledger="$template_ledger"
fi

failed=0

echo
echo "==> git diff --check"
if git -C "$root" diff --check; then
  echo "[ok] git diff --check"
else
  echo "[fail] git diff --check"
  failed=1
fi

echo
echo "==> framework templates stay universal"
template_task="$(awk '
function strip(s) {
  gsub(/^[[:space:]]+|[[:space:]]+$/, "", s)
  gsub(/^"/, "", s)
  gsub(/"$/, "", s)
  return s
}
/^active_task:/ {
  sub(/^[^:]*:[[:space:]]*/, "", $0)
  print strip($0)
  exit
}
' "$template_state")"
if [[ ! -f "$template_state" || ! -f "$template_ledger" ]]; then
  echo "[fail] missing framework task templates"
  failed=1
elif [[ -n "$template_task" && "$template_task" != "null" && "$template_task" != "~" ]]; then
  echo "[fail] .framework/project-state.yaml contains project task $template_task; write it to .local/project-state.yaml"
  failed=1
elif awk '/^  - task:/ { found = 1 } END { exit found ? 0 : 1 }' "$template_ledger"; then
  echo "[fail] .framework/metrics/ledger.yaml contains a project task; write it to .local/metrics/ledger.yaml"
  failed=1
else
  echo "[ok] framework templates have no project task"
fi

echo
echo "==> metrics ledger"
if [[ ! -f "$state" ]]; then
  echo "[fail] missing $state"
  failed=1
elif [[ ! -f "$ledger" ]]; then
  echo "[fail] missing $ledger"
  failed=1
elif ! awk '
function strip(s) {
  gsub(/^[[:space:]]+|[[:space:]]+$/, "", s)
  gsub(/^"/, "", s)
  gsub(/"$/, "", s)
  return s
}
function field_value(line) {
  sub(/^[^:]*:[[:space:]]*/, "", line)
  return strip(line)
}
function required_missing(i, key) {
  return !((i SUBSEP key) in fields)
}
BEGIN { entries = 0 }
FILENAME == ARGV[1] && /^active_task:/ { active = field_value($0); next }
FILENAME == ARGV[1] && /^active_task_since:/ { since = field_value($0); next }
FILENAME == ARGV[2] && /^  - task:/ {
  entries++
  task[entries] = field_value($0)
  next
}
FILENAME == ARGV[2] && entries > 0 && /^    [a-z0-9_]+:/ {
  key = $0
  sub(/^    /, "", key)
  sub(/:.*/, "", key)
  fields[entries, key] = field_value($0)
  next
}
END {
  if (active == "" || active == "null" || active == "~") {
    print "[ok] metrics ledger skipped: active_task is not set"
    exit 0
  }
  if (since == "" || since == "null" || since == "~" || since !~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/) {
    print "[fail] active_task_since must be YYYY-MM-DD while active_task is set"
    exit 1
  }
  if (entries == 0) {
    print "[fail] ledger has no rows; active task " active " is newer than the ledger"
    exit 1
  }
  required[1] = "recorded_at"
  required[2] = "status"
  required[3] = "verification_passed"
  required[4] = "acceptance_criteria_covered"
  required[5] = "assumptions_invalidated"
  required[6] = "missing_requirements_after_implementation"
  required[7] = "context_escalated"
  for (i = 1; i <= entries; i++) {
    if (task[i] == "" || task[i] == "null") {
      print "[fail] ledger row " i " has an empty task"
      exit 1
    }
    for (r = 1; r <= 7; r++) {
      if (required_missing(i, required[r])) {
        print "[fail] ledger row " task[i] " is missing " required[r]
        exit 1
      }
    }
    recorded = fields[i, "recorded_at"]
    status = fields[i, "status"]
    verified = fields[i, "verification_passed"]
    escalated = fields[i, "context_escalated"]
    if (recorded !~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/) {
      print "[fail] ledger row " task[i] " recorded_at must be YYYY-MM-DD"
      exit 1
    }
    if (status != "in_progress" && status != "accepted") {
      print "[fail] ledger row " task[i] " status must be in_progress or accepted"
      exit 1
    }
    if (status == "accepted" && verified != "true" && verified != "false") {
      print "[fail] accepted ledger row " task[i] " needs verification_passed true or false"
      exit 1
    }
    if (status == "in_progress" && verified != "true" && verified != "false" && verified != "null") {
      print "[fail] ledger row " task[i] " verification_passed must be true, false, or null"
      exit 1
    }
    if (escalated != "true" && escalated != "false") {
      print "[fail] ledger row " task[i] " context_escalated must be true or false"
      exit 1
    }
    counts[1] = "acceptance_criteria_covered"
    counts[2] = "assumptions_invalidated"
    counts[3] = "missing_requirements_after_implementation"
    for (c = 1; c <= 3; c++) {
      number = fields[i, counts[c]]
      if (number != "null" && number !~ /^[0-9]+$/) {
        print "[fail] ledger row " task[i] " " counts[c] " must be an integer or null"
        exit 1
      }
    }
  }
  last = entries
  if (task[last] != active) {
    print "[fail] latest ledger row is " task[last] ", active task is " active
    exit 1
  }
  if (since > fields[last, "recorded_at"]) {
    print "[fail] active task " active " since " since " is newer than ledger row " fields[last, "recorded_at"]
    exit 1
  }
  print "[ok] metrics ledger " active " " fields[last, "status"] " " fields[last, "recorded_at"]
  exit 0
}
' "$state" "$ledger"; then
  failed=1
fi

if [[ "$failed" -ne 0 ]]; then
  echo "[verify] FAILED"
  exit 1
fi

echo "[verify] PASSED"
