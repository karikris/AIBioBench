
#!/usr/bin/env python3
import argparse
import csv
import json
import math
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import psutil
from jsonschema import Draft202012Validator

BASE = "http://127.0.0.1:11434/api"

DEFAULT_MODELS = [
    "qwen36-64:latest",
    "qwen36-256:latest",
    "phi4-mini-128:latest",
    "gemma4-26b-256:latest",
    "gemma4-26b-64:latest",
    "gemma4-31b-256:latest",
    "gemma4-31b-64:latest",
    "qwen3-coder-30b-256:latest",
    "qwen3-coder-30b-64:latest",
]

DEFAULT_OPTIONS = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
}

THINK = False
KEEP_ALIVE = "10m"
REQUEST_TIMEOUT_S = 7200
HEARTBEAT_INTERVAL_S = 15.0
SAMPLE_INTERVAL_S = 1.0

OUTPUT_TABLE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["columns", "rows"],
    "properties": {
        "columns": {
            "type": "array",
            "items": {"type": "string"},
        },
        "rows": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {
                    "type": ["string", "number", "integer", "boolean", "null"]
                },
            },
        },
    },
}

OUTPUT_TABLE_VALIDATOR = Draft202012Validator(OUTPUT_TABLE_SCHEMA)


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def ns_to_s(ns: Optional[int]) -> float:
    if ns in (None, 0):
        return 0.0
    return ns / 1_000_000_000.0


def bytes_to_gib(n: float) -> float:
    return safe_div(float(n), 1024 ** 3)


def bytes_to_mib(n: float) -> float:
    return safe_div(float(n), 1024 ** 2)


def extract_num_ctx(parameters_text: str) -> Optional[int]:
    if not parameters_text:
        return None
    m = re.search(r"num_ctx\s+(\d+)", parameters_text)
    return int(m.group(1)) if m else None


def canonicalize_scalar(value: Any) -> Any:
    if isinstance(value, str) and value.strip().upper() == "NULL":
        return None
    return value


def canonicalize_row(row: Iterable[Any]) -> Tuple[Any, ...]:
    return tuple(canonicalize_scalar(v) for v in row)


def parse_json_response(text: str) -> Tuple[Optional[dict], Optional[str]]:
    text = (text or "").strip()
    if not text:
        return None, "empty response text"
    try:
        return json.loads(text), None
    except Exception as e:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0)), None
            except Exception as e2:
                return None, f"invalid JSON after fallback extraction: {e2}"
        return None, f"invalid JSON: {e}"


def api_json(method: str, path: str, payload: Optional[dict] = None, timeout: int = REQUEST_TIMEOUT_S) -> dict:
    url = BASE + path
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def stop_model(model: str) -> None:
    subprocess.run(["ollama", "stop", model], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_all_loaded() -> None:
    try:
        ps = api_json("GET", "/ps")
        for m in ps.get("models", []):
            name = m.get("name") or m.get("model")
            if name:
                stop_model(name)
    except Exception:
        pass


def get_ps_model(model: str) -> Optional[dict]:
    ps = api_json("GET", "/ps")
    wanted = {model}
    bare = model[:-7] if model.endswith(":latest") else model
    wanted.add(bare)
    wanted.add(f"{bare}:latest")
    for m in ps.get("models", []):
        name = m.get("name") or m.get("model")
        if name in wanted:
            return m
    return None


def get_show(model: str) -> dict:
    return api_json("POST", "/show", {"model": model})


def normalize_nonstream(path: str, obj: dict, client_wall_s: float) -> dict:
    if path == "/generate":
        answer_text = obj.get("response", "") or ""
        thinking_text = obj.get("thinking", "") or ""
    else:
        message = obj.get("message", {}) or {}
        answer_text = message.get("content", "") or ""
        thinking_text = message.get("thinking", "") or ""

    server_total_s = ns_to_s(obj.get("total_duration"))
    server_load_s = ns_to_s(obj.get("load_duration"))
    server_prompt_eval_s = ns_to_s(obj.get("prompt_eval_duration"))
    server_eval_s = ns_to_s(obj.get("eval_duration"))

    return {
        "endpoint_used": path,
        "answer_text": answer_text,
        "thinking_text": thinking_text,
        "client_wall_s": client_wall_s,
        "server_total_s": server_total_s,
        "server_load_s": server_load_s,
        "server_prompt_eval_s": server_prompt_eval_s,
        "server_eval_s": server_eval_s,
        "server_prompt_eval_count": obj.get("prompt_eval_count", 0) or 0,
        "server_eval_count": obj.get("eval_count", 0) or 0,
        "server_overhead_s": client_wall_s - server_total_s,
        "server_unaccounted_s": server_total_s - server_load_s - server_prompt_eval_s - server_eval_s,
        "done_reason": obj.get("done_reason", ""),
        "final_obj": obj,
    }


class Heartbeat(threading.Thread):
    def __init__(self, model: str, case_id: str, endpoint_name: str, started_at: float):
        super().__init__(daemon=True)
        self.model = model
        self.case_id = case_id
        self.endpoint_name = endpoint_name
        self.started_at = started_at
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.wait(HEARTBEAT_INTERVAL_S):
            elapsed = time.perf_counter() - self.started_at
            msg = f"{self.model} {self.case_id} via {self.endpoint_name}: still running after {elapsed:.1f}s"
            try:
                ps = get_ps_model(self.model)
                if ps:
                    size_gib = bytes_to_gib(ps.get("size", 0) or 0)
                    vram_gib = bytes_to_gib(ps.get("size_vram", 0) or 0)
                    host_gib = max(0.0, size_gib - vram_gib)
                    ctx = ps.get("context_length")
                    msg += f" | ctx={ctx} loaded_gib={size_gib:.2f} vram_gib={vram_gib:.2f} host_gib_est={host_gib:.2f}"
            except Exception:
                pass
            log(msg)


def find_ollama_processes() -> List[psutil.Process]:
    matches: List[psutil.Process] = []
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            cmdline = " ".join(proc.info.get("cmdline") or []).lower()
            if name == "ollama" or "ollama serve" in cmdline or cmdline.endswith("/ollama"):
                matches.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return matches


def has_command(name: str) -> bool:
    return subprocess.run(
        ["bash", "-lc", f"command -v {name} >/dev/null 2>&1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


class ResourceSampler(threading.Thread):
    def __init__(self, interval_s: float = SAMPLE_INTERVAL_S):
        super().__init__(daemon=True)
        self.interval_s = interval_s
        self._stop_event = threading.Event()
        self.samples: List[Dict[str, Any]] = []
        self.has_nvidia_smi = has_command("nvidia-smi")
        self.gpu_names: List[str] = []
        self._prime()

    def _prime(self) -> None:
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass
        for proc in find_ollama_processes():
            try:
                proc.cpu_percent(interval=None)
            except Exception:
                pass

    def stop(self) -> None:
        self._stop_event.set()

    def _sample_gpu(self) -> Dict[str, Any]:
        if not self.has_nvidia_smi:
            return {}
        cmd = [
            "nvidia-smi",
            "--query-gpu=name,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu",
            "--format=csv,noheader,nounits",
        ]
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if cp.returncode != 0:
                return {}
            utils = []
            mem_used = []
            mem_total = []
            power = []
            temp = []
            names = []
            for line in cp.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 6:
                    continue
                names.append(parts[0])
                utils.append(float(parts[1]))
                mem_used.append(float(parts[2]))
                mem_total.append(float(parts[3]))
                power.append(float(parts[4]) if parts[4] not in ("[N/A]", "N/A") else math.nan)
                temp.append(float(parts[5]) if parts[5] not in ("[N/A]", "N/A") else math.nan)
            if names:
                self.gpu_names = names
            if not utils:
                return {}
            return {
                "gpu_util_avg_pct": sum(utils) / len(utils),
                "gpu_util_max_pct": max(utils),
                "gpu_mem_used_mib": sum(mem_used),
                "gpu_mem_total_mib": sum(mem_total),
                "gpu_mem_util_pct": 100.0 * safe_div(sum(mem_used), sum(mem_total)),
                "gpu_power_draw_w": None if all(math.isnan(x) for x in power) else sum(x for x in power if not math.isnan(x)),
                "gpu_temp_avg_c": None if all(math.isnan(x) for x in temp) else sum(x for x in temp if not math.isnan(x)) / len([x for x in temp if not math.isnan(x)]),
            }
        except Exception:
            return {}

    def run(self) -> None:
        while not self._stop_event.wait(self.interval_s):
            sample: Dict[str, Any] = {"ts": time.time()}
            try:
                sample["system_cpu_pct"] = psutil.cpu_percent(interval=None)
                sample["system_mem_pct"] = psutil.virtual_memory().percent
                try:
                    sample["system_load1"] = os.getloadavg()[0]
                except Exception:
                    sample["system_load1"] = None

                procs = find_ollama_processes()
                sample["ollama_proc_count"] = len(procs)
                sample["ollama_cpu_pct"] = 0.0
                sample["ollama_rss_mib"] = 0.0
                sample["ollama_threads"] = 0
                for proc in procs:
                    try:
                        sample["ollama_cpu_pct"] += proc.cpu_percent(interval=None)
                        sample["ollama_rss_mib"] += bytes_to_mib(proc.memory_info().rss)
                        sample["ollama_threads"] += proc.num_threads()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                sample.update(self._sample_gpu())
            except Exception:
                pass
            self.samples.append(sample)

    def aggregate(self) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {
            "resource_samples": len(self.samples),
            "sampler_interval_s": self.interval_s,
            "gpu_sampler_available": self.has_nvidia_smi,
            "gpu_names": ";".join(self.gpu_names) if self.gpu_names else "",
        }
        if not self.samples:
            return metrics

        def series(name: str) -> List[float]:
            out = []
            for s in self.samples:
                v = s.get(name)
                if isinstance(v, (int, float)) and not math.isnan(v):
                    out.append(float(v))
            return out

        for name, prefix in [
            ("system_cpu_pct", "system_cpu"),
            ("system_mem_pct", "system_mem"),
            ("system_load1", "system_load1"),
            ("ollama_cpu_pct", "ollama_cpu"),
            ("ollama_rss_mib", "ollama_rss_mib"),
            ("ollama_threads", "ollama_threads"),
            ("ollama_proc_count", "ollama_proc_count"),
            ("gpu_util_avg_pct", "gpu_util_pct"),
            ("gpu_mem_used_mib", "gpu_mem_used_mib"),
            ("gpu_mem_util_pct", "gpu_mem_util_pct"),
            ("gpu_power_draw_w", "gpu_power_w"),
            ("gpu_temp_avg_c", "gpu_temp_c"),
        ]:
            vals = series(name)
            if vals:
                metrics[f"{prefix}_avg"] = sum(vals) / len(vals)
                metrics[f"{prefix}_max"] = max(vals)
                metrics[f"{prefix}_min"] = min(vals)
        return metrics


def build_generate_payload(model: str, prompt: str, schema: dict, options: dict, keep_alive: str) -> dict:
    return {
        "model": model,
        "prompt": prompt,
        "system": "Return only valid JSON. No prose.",
        "format": schema,
        "stream": False,
        "think": THINK,
        "keep_alive": keep_alive,
        "options": options.copy(),
    }


def build_chat_payload(model: str, prompt: str, schema: dict, options: dict, keep_alive: str) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only valid JSON. No prose."},
            {"role": "user", "content": prompt},
        ],
        "format": schema,
        "stream": False,
        "think": THINK,
        "keep_alive": keep_alive,
        "options": options.copy(),
    }


def call_nonstream(path: str, payload: dict, model: str, case_id: str) -> dict:
    url = BASE + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    t0 = time.perf_counter()
    hb = Heartbeat(model=model, case_id=case_id, endpoint_name=path, started_at=t0)
    sampler = ResourceSampler()
    hb.start()
    sampler.start()
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
            body = resp.read().decode("utf-8")
        client_wall_s = time.perf_counter() - t0
        obj = json.loads(body)
        result = normalize_nonstream(path, obj, client_wall_s)
        result["resource_metrics"] = sampler.aggregate()
        return result
    finally:
        hb.stop()
        sampler.stop()
        hb.join(timeout=1)
        sampler.join(timeout=1)


def invoke_nonstream(path: str, model: str, prompt: str, schema: dict, case_id: str, options: dict, keep_alive: str) -> dict:
    if path == "/generate":
        payload = build_generate_payload(model, prompt, schema, options, keep_alive)
    else:
        payload = build_chat_payload(model, prompt, schema, options, keep_alive)
    return call_nonstream(path, payload, model, case_id)


def derive_memory_speed_metrics(row: dict) -> None:
    loaded = row.get("ps_loaded_gib", 0.0) or 0.0
    vram = row.get("ps_vram_gib", 0.0) or 0.0
    host = max(0.0, loaded - vram)

    row["ps_host_loaded_gib_est"] = host
    row["ps_vram_ratio"] = safe_div(vram, loaded)
    row["ps_host_ratio_est"] = safe_div(host, loaded)

    row["server_gen_tps_per_loaded_gib"] = safe_div(row.get("server_gen_tps", 0.0), loaded)
    row["server_gen_tps_per_vram_gib"] = safe_div(row.get("server_gen_tps", 0.0), vram)
    row["server_gen_tps_per_host_gib_est"] = safe_div(row.get("server_gen_tps", 0.0), host)
    row["server_load_s_per_loaded_gib"] = safe_div(row.get("server_load_s", 0.0), loaded)
    row["server_load_s_per_vram_gib"] = safe_div(row.get("server_load_s", 0.0), vram)

    if row["ps_vram_ratio"] >= 0.75:
        row["memory_speed_hint"] = "mostly_gpu_resident"
    elif row["ps_vram_ratio"] >= 0.45:
        row["memory_speed_hint"] = "mixed_gpu_host"
    else:
        row["memory_speed_hint"] = "mostly_host_offloaded"


def scalar_for_json(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value


def make_csv_text(table_name: str, table: dict) -> str:
    lines = [",".join(table["columns"])]
    for row in table["rows"]:
        parts = []
        for v in row:
            if v is None:
                parts.append("")
            else:
                parts.append(str(v))
        lines.append(",".join(parts))
    return "\n".join(lines)


def build_case_prompt(case: dict, dataset: dict, instruction_lookup: Dict[str, dict], answer_columns: List[str]) -> str:
    inst = instruction_lookup[case["standard_instructions_id"]]["text"].strip()
    table_blocks = []
    for table_name, table in dataset["tables"].items():
        table_blocks.append(f"{table_name}:\n{make_csv_text(table_name, table)}")

    output_columns_text = ", ".join(answer_columns)
    return (
        "/no_think\n"
        "You are benchmarking a local model on data analysis accuracy.\n\n"
        f"{inst}\n\n"
        "For this automated benchmark run, do NOT output SQL or Python code.\n"
        "Return ONLY the final result table as JSON matching the required schema.\n"
        "The JSON must be:\n"
        '{"columns": [...], "rows": [[...], ...]}\n'
        "Use JSON null for NULL values.\n"
        "Preserve exact column order and row order requested by the task.\n"
        "Do not include markdown. Do not include commentary.\n\n"
        f"Benchmark ID: {case['benchmark_id']}\n"
        f"Case ID: {case['case_id']}\n"
        f"Pass: {case['pass']}\n"
        f"Difficulty: {case['difficulty']}\n"
        f"Language: {case['language']}\n\n"
        f"Schema shape:\n{dataset['schema_text']}\n\n"
        "Shared dataset tables:\n\n"
        + "\n\n".join(table_blocks)
        + "\n\n"
        f"Task:\n{case['prompt']}\n\n"
        f"Return these columns in this exact order:\n{output_columns_text}\n"
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as e:
                raise ValueError(f"{path} line {idx}: invalid JSON: {e}") from e
    return rows


def validate_records(records: List[dict], schema: dict, path: Path) -> None:
    validator = Draft202012Validator(schema)
    errs = []
    for i, rec in enumerate(records, start=1):
        for err in validator.iter_errors(rec):
            errs.append(f"{path.name} line {i}: {'/'.join(map(str, err.absolute_path)) or '<root>'}: {err.message}")
    if errs:
        preview = "\n".join(errs[:20])
        raise ValueError(f"Schema validation failed for {path}.\n{preview}")


def validate_single_record(record: dict, schema: dict, label: str) -> None:
    validator = Draft202012Validator(schema)
    errs = sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path))
    if errs:
        lines = [f"{label}: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errs[:20]]
        raise ValueError("\n".join(lines))


def load_benchmark(manifest_path: Path, validate: bool = True) -> dict:
    base_dir = manifest_path.parent
    manifest = load_json(manifest_path)
    case_schema = load_json(base_dir / manifest["schemas"]["case"])
    gold_schema = load_json(base_dir / manifest["schemas"]["gold"])
    result_schema = load_json(base_dir / manifest["schemas"]["result"])
    dataset = load_json(base_dir / manifest["dataset_file"])
    instructions = load_json(base_dir / manifest["standard_instructions_file"])
    cases = load_jsonl(base_dir / manifest["cases_file"])
    gold = load_jsonl(base_dir / manifest["gold_file"])

    if validate:
        validate_records(cases, case_schema, base_dir / manifest["cases_file"])
        validate_records(gold, gold_schema, base_dir / manifest["gold_file"])

    instruction_lookup = {x["standard_instructions_id"]: x for x in instructions["instructions"]}
    gold_lookup = {x["case_id"]: x for x in gold}

    case_ids = {c["case_id"] for c in cases}
    gold_ids = set(gold_lookup)
    if case_ids != gold_ids:
        missing_gold = sorted(case_ids - gold_ids)
        missing_cases = sorted(gold_ids - case_ids)
        raise ValueError(f"Case/gold mismatch. missing_gold={missing_gold[:10]} missing_cases={missing_cases[:10]}")

    return {
        "manifest": manifest,
        "dataset": dataset,
        "instructions": instructions,
        "cases": cases,
        "gold": gold,
        "instruction_lookup": instruction_lookup,
        "gold_lookup": gold_lookup,
        "case_schema": case_schema,
        "gold_schema": gold_schema,
        "result_schema": result_schema,
        "base_dir": base_dir,
    }


def multiset_diff_counts(gold_rows: List[List[Any]], pred_rows: List[List[Any]]) -> Tuple[int, int]:
    gold_counter = Counter(canonicalize_row(r) for r in gold_rows)
    pred_counter = Counter(canonicalize_row(r) for r in pred_rows)
    missing = gold_counter - pred_counter
    extra = pred_counter - gold_counter
    return sum(missing.values()), sum(extra.values())


def score_exact_ordered_table(case: dict, gold: dict, pred_columns: List[str], pred_rows: List[List[Any]]) -> Dict[str, Any]:
    gold_columns = gold["columns"]
    gold_rows = gold["rows"]
    row_order_matters = case["scoring"].get("row_order_matters", True)
    column_order_matters = case["scoring"].get("column_order_matters", True)

    gold_columns_norm = [canonicalize_scalar(x) for x in gold_columns]
    pred_columns_norm = [canonicalize_scalar(x) for x in pred_columns]
    pred_rows_norm = [list(canonicalize_row(r)) for r in pred_rows]
    gold_rows_norm = [list(canonicalize_row(r)) for r in gold_rows]

    column_exact_match = pred_columns_norm == gold_columns_norm if column_order_matters else sorted(pred_columns_norm) == sorted(gold_columns_norm)
    row_exact_match = pred_rows_norm == gold_rows_norm if row_order_matters else Counter(map(tuple, pred_rows_norm)) == Counter(map(tuple, gold_rows_norm))
    exact_match = column_exact_match and row_exact_match

    max_rows = max(len(gold_rows_norm), len(pred_rows_norm))
    max_cols = max(len(gold_columns_norm), len(pred_columns_norm))
    aligned_total_cells = max_rows * max_cols
    aligned_cell_matches = 0
    sentinel = object()
    for i in range(max_rows):
        for j in range(max_cols):
            gv = sentinel
            pv = sentinel
            if i < len(gold_rows_norm) and j < len(gold_rows_norm[i]):
                gv = gold_rows_norm[i][j]
            if i < len(pred_rows_norm) and j < len(pred_rows_norm[i]):
                pv = pred_rows_norm[i][j]
            if gv == pv:
                aligned_cell_matches += 1

    row_position_matches = 0
    for i in range(min(len(gold_rows_norm), len(pred_rows_norm))):
        if pred_rows_norm[i] == gold_rows_norm[i]:
            row_position_matches += 1

    missing_rows_count, extra_rows_count = multiset_diff_counts(gold_rows_norm, pred_rows_norm)

    return {
        "score": float(case["scoring"].get("max_score", 1.0) if exact_match else 0.0),
        "max_score": float(case["scoring"].get("max_score", 1.0)),
        "exact_match": exact_match,
        "column_exact_match": column_exact_match,
        "row_exact_match": row_exact_match,
        "gold_column_count": len(gold_columns_norm),
        "pred_column_count": len(pred_columns_norm),
        "gold_row_count": len(gold_rows_norm),
        "pred_row_count": len(pred_rows_norm),
        "row_count_match": len(pred_rows_norm) == len(gold_rows_norm),
        "column_count_match": len(pred_columns_norm) == len(gold_columns_norm),
        "row_position_matches": row_position_matches,
        "row_position_accuracy": safe_div(row_position_matches, max(len(gold_rows_norm), len(pred_rows_norm))),
        "aligned_cell_matches": aligned_cell_matches,
        "aligned_total_cells": aligned_total_cells,
        "aligned_cell_accuracy": safe_div(aligned_cell_matches, aligned_total_cells),
        "missing_rows_count": missing_rows_count,
        "extra_rows_count": extra_rows_count,
    }


def run_case(
    model: str,
    case: dict,
    gold: dict,
    dataset: dict,
    instruction_lookup: Dict[str, dict],
    options: dict,
    keep_alive: str,
    cold_start: bool,
) -> dict:
    case_id = case["case_id"]
    answer_columns = gold["columns"]
    prompt = build_case_prompt(case, dataset, instruction_lookup, answer_columns)

    if cold_start:
        log(f"{model} {case_id}: cold start requested; stopping loaded copy first")
        stop_model(model)

    primary_path = "/generate"
    fallback_path = "/chat"
    fallback_used = False
    parse_error = ""
    output_validation_error = ""
    status = "ok"
    error = None

    prompt_chars = len(prompt)
    prompt_bytes = len(prompt.encode("utf-8"))

    try:
        log(f"{model} {case_id}: starting primary request via {primary_path}")
        primary = invoke_nonstream(primary_path, model, prompt, OUTPUT_TABLE_SCHEMA, case_id, options, keep_alive)
        parsed, parse_error = parse_json_response(primary["answer_text"])
        result = primary

        if parsed is not None:
            schema_errors = sorted(OUTPUT_TABLE_VALIDATOR.iter_errors(parsed), key=lambda e: list(e.absolute_path))
            if schema_errors:
                output_validation_error = "; ".join(
                    f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in schema_errors[:10]
                )
                parsed = None

        if parsed is None:
            log(f"{model} {case_id}: primary {primary_path} invalid; retrying via {fallback_path}")
            fallback = invoke_nonstream(fallback_path, model, prompt, OUTPUT_TABLE_SCHEMA, case_id + "_fallback_chat", options, keep_alive)
            fallback_parsed, fallback_err = parse_json_response(fallback["answer_text"])
            fallback_validation_error = ""
            if fallback_parsed is not None:
                schema_errors = sorted(OUTPUT_TABLE_VALIDATOR.iter_errors(fallback_parsed), key=lambda e: list(e.absolute_path))
                if schema_errors:
                    fallback_validation_error = "; ".join(
                        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in schema_errors[:10]
                    )
                    fallback_parsed = None

            if fallback_parsed is not None:
                parsed = fallback_parsed
                result = fallback
                parse_error = ""
                output_validation_error = ""
                fallback_used = True
            else:
                parse_bits = []
                if parse_error:
                    parse_bits.append(parse_error)
                if output_validation_error:
                    parse_bits.append(f"output_schema_error={output_validation_error}")
                if fallback_err:
                    parse_bits.append(f"fallback_chat_error={fallback_err}")
                if fallback_validation_error:
                    parse_bits.append(f"fallback_chat_schema_error={fallback_validation_error}")
                parse_error = " | ".join(parse_bits)

        if parsed is not None:
            pred_columns = parsed.get("columns", [])
            pred_rows = parsed.get("rows", [])
            scoring = score_exact_ordered_table(case, gold, pred_columns, pred_rows)
        else:
            pred_columns = []
            pred_rows = []
            scoring = score_exact_ordered_table(case, gold, pred_columns, pred_rows)
            scoring["score"] = 0.0

    except Exception as e:
        status = "error"
        error = f"{type(e).__name__}: {e}"
        result = {
            "endpoint_used": primary_path,
            "answer_text": "",
            "thinking_text": "",
            "client_wall_s": 0.0,
            "server_total_s": 0.0,
            "server_load_s": 0.0,
            "server_prompt_eval_s": 0.0,
            "server_eval_s": 0.0,
            "server_prompt_eval_count": 0,
            "server_eval_count": 0,
            "server_overhead_s": 0.0,
            "server_unaccounted_s": 0.0,
            "done_reason": "",
            "resource_metrics": {},
        }
        pred_columns = []
        pred_rows = []
        scoring = score_exact_ordered_table(case, gold, pred_columns, pred_rows)
        scoring["score"] = 0.0
        parse_error = error

    ps = get_ps_model(model) or {}
    ps_loaded_gib = bytes_to_gib(ps.get("size", 0) or 0)
    ps_vram_gib = bytes_to_gib(ps.get("size_vram", 0) or 0)

    row = {
        "benchmark_id": case["benchmark_id"],
        "dataset_id": case["dataset_id"],
        "case_id": case["case_id"],
        "pass": case["pass"],
        "query": case["query"],
        "difficulty": case["difficulty"],
        "language": case["language"],
        "model": model,
        "status": status,
        "cold_start": cold_start,
        "endpoint_used": result["endpoint_used"],
        "fallback_used": fallback_used,
        "valid_json": parsed is not None if status == "ok" else False,
        "score": scoring["score"],
        "max_score": scoring["max_score"],
        "exact_match": scoring["exact_match"],
        "column_exact_match": scoring["column_exact_match"],
        "row_exact_match": scoring["row_exact_match"],
        "row_count_match": scoring["row_count_match"],
        "column_count_match": scoring["column_count_match"],
        "gold_row_count": scoring["gold_row_count"],
        "pred_row_count": scoring["pred_row_count"],
        "gold_column_count": scoring["gold_column_count"],
        "pred_column_count": scoring["pred_column_count"],
        "row_position_matches": scoring["row_position_matches"],
        "row_position_accuracy": scoring["row_position_accuracy"],
        "aligned_cell_matches": scoring["aligned_cell_matches"],
        "aligned_total_cells": scoring["aligned_total_cells"],
        "aligned_cell_accuracy": scoring["aligned_cell_accuracy"],
        "missing_rows_count": scoring["missing_rows_count"],
        "extra_rows_count": scoring["extra_rows_count"],
        "client_wall_s": result["client_wall_s"],
        "server_total_s": result["server_total_s"],
        "server_load_s": result["server_load_s"],
        "server_prompt_eval_s": result["server_prompt_eval_s"],
        "server_eval_s": result["server_eval_s"],
        "server_prompt_eval_count": result["server_prompt_eval_count"],
        "server_eval_count": result["server_eval_count"],
        "server_prompt_tps": safe_div(result["server_prompt_eval_count"], result["server_prompt_eval_s"]),
        "server_gen_tps": safe_div(result["server_eval_count"], result["server_eval_s"]),
        "server_overhead_s": result["server_overhead_s"],
        "server_unaccounted_s": result["server_unaccounted_s"],
        "done_reason": result["done_reason"],
        "prompt_chars": prompt_chars,
        "prompt_bytes": prompt_bytes,
        "response_chars": len(result["answer_text"]),
        "response_bytes": len(result["answer_text"].encode("utf-8")),
        "thinking_chars": len(result["thinking_text"]),
        "prompt_lines": prompt.count("\n") + 1,
        "response_lines": result["answer_text"].count("\n") + 1 if result["answer_text"] else 0,
        "response_text": result["answer_text"],
        "thinking_text": result["thinking_text"],
        "parse_error": parse_error or "",
        "output_validation_error": output_validation_error or "",
        "error": error or "",
        "ps_context": ps.get("context_length"),
        "ps_loaded_gib": ps_loaded_gib,
        "ps_vram_gib": ps_vram_gib,
        "ps_expires_at": ps.get("expires_at", ""),
        "parsed_columns_json": json.dumps(pred_columns, ensure_ascii=False),
        "parsed_rows_json": json.dumps(pred_rows, ensure_ascii=False),
        "gold_columns_json": json.dumps(gold["columns"], ensure_ascii=False),
        "gold_rows_json": json.dumps(gold["rows"], ensure_ascii=False),
    }

    row.update(result.get("resource_metrics", {}))
    row["prompt_tokens_per_char"] = safe_div(row["server_prompt_eval_count"], row["prompt_chars"])
    row["response_tokens_per_char"] = safe_div(row["server_eval_count"], row["response_chars"])
    row["eval_to_prompt_token_ratio"] = safe_div(row["server_eval_count"], row["server_prompt_eval_count"])
    row["client_to_server_time_ratio"] = safe_div(row["client_wall_s"], row["server_total_s"])
    derive_memory_speed_metrics(row)

    log(
        f"{model} {case_id}: status={row['status']} valid_json={row['valid_json']} "
        f"score={row['score']:.1f}/{row['max_score']:.1f} exact={row['exact_match']} "
        f"endpoint={row['endpoint_used']} fallback={row['fallback_used']}"
    )
    log(
        f"{model} {case_id}: client_wall_s={row['client_wall_s']:.2f} server_total_s={row['server_total_s']:.2f} "
        f"load_s={row['server_load_s']:.2f} prompt_eval_s={row['server_prompt_eval_s']:.2f} eval_s={row['server_eval_s']:.2f}"
    )
    log(
        f"{model} {case_id}: prompt_tps={row['server_prompt_tps']:.2f} gen_tps={row['server_gen_tps']:.2f} "
        f"gpu_share={100 * row['ps_vram_ratio']:.0f}% host_share={100 * row['ps_host_ratio_est']:.0f}% "
        f"loaded_gib={row['ps_loaded_gib']:.2f} vram_gib={row['ps_vram_gib']:.2f}"
    )
    if row.get("resource_samples", 0):
        log(
            f"{model} {case_id}: sys_cpu_avg={row.get('system_cpu_avg', 0.0):.1f}% "
            f"ollama_cpu_avg={row.get('ollama_cpu_avg', 0.0):.1f}% "
            f"ollama_rss_avg_mib={row.get('ollama_rss_mib_avg', 0.0):.1f}"
        )

    if row["parse_error"]:
        response_sample = row["response_text"][:800].replace("\n", "\\n")
        log(f"{model} {case_id}: parse_error={row['parse_error']}")
        log(f"{model} {case_id}: raw_response_sample={response_sample!r}")

    return row


def make_run_result_record(benchmark_id: str, run_id: str, case_id: str, model_name: str, row: dict) -> dict:
    status = "ok" if row.get("exact_match") else ("error" if row.get("status") == "error" else "ok")
    rec = {
        "benchmark_id": benchmark_id,
        "run_id": run_id,
        "case_id": case_id,
        "model_name": model_name,
        "status": status,
        "answer_text": row.get("response_text") or None,
        "parsed_columns": json.loads(row.get("parsed_columns_json") or "null"),
        "parsed_rows": json.loads(row.get("parsed_rows_json") or "null"),
        "score": row.get("score"),
        "max_score": row.get("max_score"),
        "error": row.get("error") or row.get("parse_error") or None,
    }
    return rec


def aggregate_rows(rows: List[dict], group_keys: List[str]) -> List[dict]:
    groups: Dict[Tuple[Any, ...], List[dict]] = {}
    for row in rows:
        key = tuple(row.get(k) for k in group_keys)
        groups.setdefault(key, []).append(row)

    out = []
    for key, items in sorted(groups.items()):
        rec = {k: v for k, v in zip(group_keys, key)}
        rec["cases"] = len(items)
        rec["exact_matches"] = sum(1 for x in items if x.get("exact_match"))
        rec["valid_json_cases"] = sum(1 for x in items if x.get("valid_json"))
        rec["score"] = sum(float(x.get("score", 0.0) or 0.0) for x in items)
        rec["max_score"] = sum(float(x.get("max_score", 0.0) or 0.0) for x in items)
        rec["accuracy"] = safe_div(rec["score"], rec["max_score"])
        rec["exact_match_rate"] = safe_div(rec["exact_matches"], rec["cases"])
        rec["valid_json_rate"] = safe_div(rec["valid_json_cases"], rec["cases"])
        rec["client_wall_s_total"] = sum(float(x.get("client_wall_s", 0.0) or 0.0) for x in items)
        rec["server_total_s_total"] = sum(float(x.get("server_total_s", 0.0) or 0.0) for x in items)
        rec["server_eval_tokens_total"] = sum(int(x.get("server_eval_count", 0) or 0) for x in items)
        rec["server_prompt_tokens_total"] = sum(int(x.get("server_prompt_eval_count", 0) or 0) for x in items)
        rec["mean_gen_tps"] = safe_div(
            sum(float(x.get("server_gen_tps", 0.0) or 0.0) for x in items),
            len(items),
        )
        rec["mean_prompt_tps"] = safe_div(
            sum(float(x.get("server_prompt_tps", 0.0) or 0.0) for x in items),
            len(items),
        )
        rec["mean_ps_loaded_gib"] = safe_div(
            sum(float(x.get("ps_loaded_gib", 0.0) or 0.0) for x in items),
            len(items),
        )
        rec["mean_ps_vram_gib"] = safe_div(
            sum(float(x.get("ps_vram_gib", 0.0) or 0.0) for x in items),
            len(items),
        )
        rec["mean_system_cpu_avg"] = safe_div(
            sum(float(x.get("system_cpu_avg", 0.0) or 0.0) for x in items),
            len(items),
        )
        rec["mean_ollama_cpu_avg"] = safe_div(
            sum(float(x.get("ollama_cpu_avg", 0.0) or 0.0) for x in items),
            len(items),
        )
        rec["mean_gpu_util_pct_avg"] = safe_div(
            sum(float(x.get("gpu_util_pct_avg", 0.0) or 0.0) for x in items),
            len(items),
        )
        out.append(rec)
    return out


def print_summary_table(rows: List[dict]) -> None:
    cols = [
        ("model", 24),
        ("case_id", 14),
        ("ok", 3),
        ("score", 7),
        ("gen_tps", 9),
        ("gpu_share", 10),
        ("host_share", 11),
        ("loaded_gib", 11),
        ("vram_gib", 10),
        ("sys_cpu", 8),
        ("ollama_cpu", 11),
    ]
    header = " ".join(name.ljust(width) for name, width in cols)
    print("\n" + header)
    print("-" * len(header))
    for r in rows:
        vals = {
            "model": str(r["model"])[:24],
            "case_id": str(r["case_id"])[:14],
            "ok": "Y" if r.get("exact_match") else "N",
            "score": f"{r['score']:.1f}/{r['max_score']:.1f}",
            "gen_tps": f"{r['server_gen_tps']:.2f}",
            "gpu_share": f"{100 * r['ps_vram_ratio']:.0f}%",
            "host_share": f"{100 * r['ps_host_ratio_est']:.0f}%",
            "loaded_gib": f"{r['ps_loaded_gib']:.2f}",
            "vram_gib": f"{r['ps_vram_gib']:.2f}",
            "sys_cpu": f"{r.get('system_cpu_avg', 0.0):.1f}",
            "ollama_cpu": f"{r.get('ollama_cpu_avg', 0.0):.1f}",
        }
        print(" ".join(vals[name].ljust(width) for name, width in cols))


def print_model_summary(rows: List[dict]) -> None:
    agg = aggregate_rows(rows, ["model"])
    cols = [
        ("model", 24),
        ("cases", 6),
        ("exact", 6),
        ("acc", 7),
        ("json", 7),
        ("wall_s", 10),
        ("gen_tps", 10),
        ("gpu_gib", 10),
        ("sys_cpu", 10),
    ]
    header = " ".join(name.ljust(width) for name, width in cols)
    print("\n" + header)
    print("-" * len(header))
    for r in agg:
        vals = {
            "model": str(r["model"])[:24],
            "cases": str(r["cases"]),
            "exact": str(r["exact_matches"]),
            "acc": f"{100*r['accuracy']:.1f}%",
            "json": f"{100*r['valid_json_rate']:.1f}%",
            "wall_s": f"{r['client_wall_s_total']:.1f}",
            "gen_tps": f"{r['mean_gen_tps']:.2f}",
            "gpu_gib": f"{r['mean_ps_vram_gib']:.2f}",
            "sys_cpu": f"{r['mean_system_cpu_avg']:.1f}",
        }
        print(" ".join(vals[name].ljust(width) for name, width in cols))


def write_csv(path: Path, rows: List[dict]) -> None:
    fieldnames = sorted({k for row in rows for k in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: List[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def resolve_default_manifest() -> Path:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "benchmark_manifest.json",
        Path.cwd() / "benchmark_manifest.json",
        script_dir / "plant_benchmark_jsonl" / "benchmark_manifest.json",
        Path.cwd() / "plant_benchmark_jsonl" / "benchmark_manifest.json",
        Path("/mnt/data/plant_benchmark_jsonl/benchmark_manifest.json"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Could not find benchmark_manifest.json next to the script, in the current working directory, "
        "or in a plant_benchmark_jsonl subdirectory. Use --manifest."
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run AIBioBench Ollama benchmark cases from JSONL case/gold files.")
    p.add_argument("--manifest", type=Path, default=resolve_default_manifest())
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    p.add_argument("--passes", nargs="*", type=int, default=[1, 2, 3, 4, 5])
    p.add_argument("--languages", nargs="*", default=None)
    p.add_argument("--case-ids", nargs="*", default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--no-validate", action="store_true")
    p.add_argument("--keep-alive", default=KEEP_ALIVE)
    p.add_argument("--temperature", type=float, default=DEFAULT_OPTIONS["temperature"])
    p.add_argument("--top-p", type=float, default=DEFAULT_OPTIONS["top_p"])
    p.add_argument("--top-k", type=int, default=DEFAULT_OPTIONS["top_k"])
    p.add_argument("--no-cold-first-case", action="store_false", dest="cold_first_case")
    p.add_argument("--no-stop-between-models", action="store_false", dest="stop_between_models")
    p.set_defaults(cold_first_case=True, stop_between_models=True)
    return p.parse_args()


def signal_handler(sig, frame):
    log("KeyboardInterrupt received. Exiting benchmark.")
    sys.exit(130)


def main() -> None:
    signal.signal(signal.SIGINT, signal_handler)
    args = parse_args()

    options = {
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
    }

    bm = load_benchmark(args.manifest, validate=not args.no_validate)
    manifest = bm["manifest"]
    dataset = bm["dataset"]
    cases = bm["cases"]
    gold_lookup = bm["gold_lookup"]
    instruction_lookup = bm["instruction_lookup"]
    result_schema = bm["result_schema"]

    selected_cases = []
    for case in cases:
        if case["pass"] not in set(args.passes):
            continue
        if args.languages and case["language"] not in set(args.languages):
            continue
        if args.case_ids and case["case_id"] not in set(args.case_ids):
            continue
        selected_cases.append(case)

    selected_cases.sort(key=lambda x: (x["pass"], x["query"]))
    if args.limit is not None:
        selected_cases = selected_cases[: args.limit]

    if not selected_cases:
        raise SystemExit("No benchmark cases selected.")

    run_started_at_utc = utc_now_iso()
    run_id = f"{manifest['benchmark_id']}__{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    repo_root = args.manifest.resolve().parent
    output_dir = args.output_dir or (repo_root / "results" / run_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    version = api_json("GET", "/version").get("version", "unknown")
    log(f"Ollama version: {version}")
    log(f"Benchmark: {manifest['benchmark_id']} v{manifest['version']} | selected_cases={len(selected_cases)} | models={len(args.models)}")
    log("Stopping any currently loaded models before benchmark...")
    stop_all_loaded()

    all_rows: List[dict] = []
    result_rows: List[dict] = []

    for model in args.models:
        log("=" * 96)
        log(f"Testing model: {model}")
        try:
            show = get_show(model)
        except Exception as e:
            log(f"{model}: failed to fetch model metadata: {e}")
            continue

        parameters_text = show.get("parameters", "")
        details = show.get("details", {}) or {}
        family = details.get("family", "")
        param_size = details.get("parameter_size", "")
        quant = details.get("quantization_level", "")
        cfg_num_ctx = extract_num_ctx(parameters_text)

        log(
            f"{model}: family={family or '-'} params={param_size or '-'} quant={quant or '-'} "
            f"cfg_num_ctx={cfg_num_ctx or '-'}"
        )

        for idx, case in enumerate(selected_cases):
            gold = gold_lookup[case["expected_result_id"]]
            row = run_case(
                model=model,
                case=case,
                gold=gold,
                dataset=dataset,
                instruction_lookup=instruction_lookup,
                options=options,
                keep_alive=args.keep_alive,
                cold_start=bool(args.cold_first_case and idx == 0),
            )
            row["family"] = family
            row["parameter_size"] = param_size
            row["quantization"] = quant
            row["cfg_num_ctx"] = cfg_num_ctx
            row["ollama_version"] = version
            row["run_id"] = run_id
            row["run_started_at_utc"] = run_started_at_utc
            all_rows.append(row)

            result_rec = make_run_result_record(manifest["benchmark_id"], run_id, case["case_id"], model, row)
            validate_single_record(result_rec, result_schema, f"result {model} {case['case_id']}")
            result_rows.append(result_rec)

        if args.stop_between_models:
            stop_model(model)
            log(f"{model}: selected cases complete; model stopped")

    all_rows.sort(key=lambda r: (r["model"], r["pass"], r["query"]))
    result_rows.sort(key=lambda r: (r["model_name"], r["case_id"]))

    print_model_summary(all_rows)
    print_summary_table(all_rows)

    detailed_csv = output_dir / "detailed_results.csv"
    detailed_jsonl = output_dir / "detailed_results.jsonl"
    run_results_jsonl = output_dir / "run_results.jsonl"
    model_summary_csv = output_dir / "summary_by_model.csv"
    model_pass_summary_csv = output_dir / "summary_by_model_pass.csv"
    run_meta_json = output_dir / "run_meta.json"

    write_csv(detailed_csv, all_rows)
    write_jsonl(detailed_jsonl, all_rows)
    write_jsonl(run_results_jsonl, result_rows)
    write_csv(model_summary_csv, aggregate_rows(all_rows, ["model"]))
    write_csv(model_pass_summary_csv, aggregate_rows(all_rows, ["model", "pass", "language", "difficulty"]))

    run_meta = {
        "run_id": run_id,
        "benchmark_id": manifest["benchmark_id"],
        "benchmark_version": manifest["version"],
        "manifest_path": str(args.manifest),
        "ollama_version": version,
        "models": args.models,
        "passes": args.passes,
        "case_count": len(selected_cases),
        "cases": [c["case_id"] for c in selected_cases],
        "options": options,
        "keep_alive": args.keep_alive,
        "run_started_at_utc": run_started_at_utc,
        "output_dir": str(output_dir),
        "repo_root": str(repo_root),
    }
    run_meta_json.write_text(json.dumps(run_meta, indent=2), encoding="utf-8")

    log(f"Detailed CSV written to: {detailed_csv}")
    log(f"Detailed JSONL written to: {detailed_jsonl}")
    log(f"Run results JSONL written to: {run_results_jsonl}")
    log(f"Model summary CSV written to: {model_summary_csv}")
    log(f"Model/pass summary CSV written to: {model_pass_summary_csv}")
    log(f"Run metadata JSON written to: {run_meta_json}")


if __name__ == "__main__":
    main()
