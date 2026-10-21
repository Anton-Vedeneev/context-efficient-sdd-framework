#!/usr/bin/env python3
"""Record one observed agent turn into .local/metrics/turns.yaml.

An incoming message opens a row. The stop hook fills token counts.
Missing numbers stay null. Prompt text is never written.
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone


def repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def metrics_dir():
    return os.environ.get(
        "METRICS_DIR", os.path.join(repo_root(), ".local", "metrics")
    )


def state_path():
    return os.environ.get(
        "PROJECT_STATE", os.path.join(repo_root(), ".local", "project-state.yaml")
    )


def active_task(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("active_task:"):
                value = line.split(":", 1)[1].strip().strip('"')
                if value in ("", "null", "~"):
                    return None
                return value
    return None


def whole_number(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def text_or_none(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def yaml_value(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped + '"'


def load_turns(path):
    if not os.path.isfile(path):
        return []
    entries = []
    current = None
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if line.startswith("  - "):
                if current:
                    entries.append(current)
                current = {}
                rest = line[4:]
                if ":" in rest:
                    key, value = rest.split(":", 1)
                    current[key.strip()] = parse_scalar(value.strip())
            elif current is not None and line.startswith("    ") and ":" in line:
                key, value = line.strip().split(":", 1)
                current[key.strip()] = parse_scalar(value.strip())
        if current:
            entries.append(current)
    return entries


def parse_scalar(text):
    if text in ("null", "~", ""):
        return None
    if text in ("true", "false"):
        return text == "true"
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
        return int(text)
    return text


def dump_turns(path, entries):
    lines = ["schema_version: 1", "entries:"]
    if not entries:
        lines.append("  []")
    for entry in entries:
        first = True
        for key in (
            "task",
            "recorded_at",
            "conversation_id",
            "generation_id",
            "model",
            "status",
            "loop_count",
            "input_tokens",
            "output_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
            "duration_ms",
        ):
            rendered = "  - " if first else "    "
            lines.append(rendered + key + ": " + yaml_value(entry.get(key)))
            first = False
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    os.replace(temporary, path)


def starts_path():
    return os.path.join(metrics_dir(), "turn-starts.json")


def load_starts():
    path = starts_path()
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def save_starts(data):
    path = starts_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    os.replace(temporary, path)


def now_stamp():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def remember_start(payload):
    key = text_or_none(payload.get("generation_id")) or text_or_none(
        payload.get("conversation_id")
    )
    if not key:
        return
    starts = load_starts()
    starts[key] = now_stamp()
    save_starts(starts)


def take_duration(payload):
    key = text_or_none(payload.get("generation_id")) or text_or_none(
        payload.get("conversation_id")
    )
    if not key:
        return None
    starts = load_starts()
    started = starts.pop(key, None)
    save_starts(starts)
    if not started:
        return None
    try:
        began = datetime.fromisoformat(started)
        elapsed = datetime.now(timezone.utc).astimezone() - began
    except ValueError:
        return None
    return max(0, int(elapsed.total_seconds() * 1000))


def blank_turn(payload, status):
    return {
        "task": active_task(state_path()),
        "recorded_at": now_stamp(),
        "conversation_id": text_or_none(payload.get("conversation_id")),
        "generation_id": text_or_none(payload.get("generation_id")),
        "model": text_or_none(payload.get("model")),
        "status": status,
        "loop_count": whole_number(payload.get("loop_count")),
        "input_tokens": None,
        "output_tokens": None,
        "cache_read_tokens": None,
        "cache_write_tokens": None,
        "duration_ms": None,
    }


def open_turn(payload):
    remember_start(payload)
    path = os.path.join(metrics_dir(), "turns.yaml")
    entries = load_turns(path)
    generation = text_or_none(payload.get("generation_id"))
    if generation and any(item.get("generation_id") == generation for item in entries):
        return
    entries.append(blank_turn(payload, "started"))
    dump_turns(path, entries)


def fill_turn(entry, payload):
    status = text_or_none(payload.get("status"))
    if status:
        entry["status"] = status
    model = text_or_none(payload.get("model"))
    if model:
        entry["model"] = model
    loop_count = whole_number(payload.get("loop_count"))
    if loop_count is not None:
        entry["loop_count"] = loop_count
    for key in (
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
    ):
        value = whole_number(payload.get(key))
        if value is not None:
            entry[key] = value
    entry["duration_ms"] = take_duration(payload)


def record_stop(payload):
    generation = text_or_none(payload.get("generation_id"))
    path = os.path.join(metrics_dir(), "turns.yaml")
    entries = load_turns(path)
    target = None
    if generation:
        for item in reversed(entries):
            if item.get("generation_id") == generation and item.get("status") == "started":
                target = item
                break
        if target is None and any(item.get("generation_id") == generation for item in entries):
            return
    elif entries:
        for item in reversed(entries):
            if item.get("status") == "started":
                target = item
                break
    if target is None:
        target = blank_turn(payload, text_or_none(payload.get("status")))
        entries.append(target)
    fill_turn(target, payload)
    dump_turns(path, entries)


def handle(payload):
    event = text_or_none(payload.get("hook_event_name")) or ""
    if "prompt" in payload or event == "beforeSubmitPrompt":
        open_turn(payload)
        return {"continue": True}
    if event in ("stop", "Stop") or "status" in payload or "input_tokens" in payload:
        record_stop(payload)
    return {}


def summarize():
    entries = load_turns(os.path.join(metrics_dir(), "turns.yaml"))
    task = active_task(state_path())
    rows = [item for item in entries if item.get("task") == task]
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "duration_ms": 0,
    }
    missing = {key: 0 for key in totals}
    for row in rows:
        for key in totals:
            value = row.get(key)
            if isinstance(value, int):
                totals[key] += value
            else:
                missing[key] += 1
    print("task: " + (task or "null"))
    print("turns: " + str(len(rows)))
    for key in totals:
        if not rows or missing[key] == len(rows):
            print(key + ": null")
        elif missing[key]:
            print(key + ": " + str(totals[key]) + " (" + str(missing[key]) + " null)")
        else:
            print(key + ": " + str(totals[key]))
    print("subagent_tokens: null")


def self_test():
    with tempfile.TemporaryDirectory() as directory:
        os.environ["METRICS_DIR"] = os.path.join(directory, "metrics")
        os.environ["PROJECT_STATE"] = os.path.join(directory, "project-state.yaml")
        with open(os.environ["PROJECT_STATE"], "w", encoding="utf-8") as stream:
            stream.write('active_task: example-task\n')
        leaked = handle(
            {
                "hook_event_name": "beforeSubmitPrompt",
                "generation_id": "gen-1",
                "prompt": "secret prompt text",
            }
        )
        assert leaked == {"continue": True}
        opened = load_turns(os.path.join(metrics_dir(), "turns.yaml"))
        assert len(opened) == 1
        assert opened[0]["status"] == "started"
        assert opened[0]["input_tokens"] is None
        assert opened[0]["task"] == "example-task"
        blob = open(os.path.join(metrics_dir(), "turns.yaml"), encoding="utf-8").read()
        assert "secret prompt text" not in blob
        with open(starts_path(), encoding="utf-8") as stream:
            assert "secret prompt text" not in stream.read()
        handle(
            {
                "hook_event_name": "stop",
                "conversation_id": "conv-1",
                "generation_id": "gen-1",
                "model": "example-model",
                "status": "completed",
                "loop_count": 0,
                "input_tokens": 10,
                "output_tokens": 2,
                "cache_read_tokens": 3,
                "cache_write_tokens": 1,
            }
        )
        handle(
            {
                "hook_event_name": "stop",
                "generation_id": "gen-1",
                "input_tokens": 99,
            }
        )
        handle(
            {
                "hook_event_name": "beforeSubmitPrompt",
                "generation_id": "gen-3",
                "prompt": "another secret",
            }
        )
        handle(
            {
                "hook_event_name": "stop",
                "generation_id": "gen-2",
                "status": "completed",
            }
        )
        entries = load_turns(os.path.join(metrics_dir(), "turns.yaml"))
        blob = open(os.path.join(metrics_dir(), "turns.yaml"), encoding="utf-8").read()
        assert "secret prompt text" not in blob
        assert "another secret" not in blob
        assert len(entries) == 3
        assert entries[0]["input_tokens"] == 10
        assert entries[0]["status"] == "completed"
        assert entries[0]["task"] == "example-task"
        assert isinstance(entries[0]["duration_ms"], int)
        assert entries[1]["status"] == "started"
        assert entries[1]["generation_id"] == "gen-3"
        assert entries[1]["input_tokens"] is None
        assert entries[2]["input_tokens"] is None
        assert entries[2]["duration_ms"] is None
    print("[ok] record-turn")


def main():
    if "--self-test" in sys.argv:
        self_test()
        return
    if "--summary" in sys.argv:
        summarize()
        return
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    if not isinstance(payload, dict):
        payload = {}
    sys.stdout.write(json.dumps(handle(payload)))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        if "--self-test" in sys.argv or "--summary" in sys.argv:
            raise
        sys.stdout.write("{}")
        sys.exit(0)
