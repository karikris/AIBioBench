#!/usr/bin/env python3
import argparse
import csv
import json
import math
import os
import re
import signal
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import psutil
from jsonschema import Draft202012Validator

BASE = "http://127.0.0.1:11434/api"

DEFAULT_MODELS = [
    "gemma4-26b-sqlbench:latest",
    "phi4-mini-sqlbench:latest",
    "gemma4-31b-sqlbench:latest",
    "qwen3-coder-30b-sqlbench:latest",
    "qwen3.6-sqlbench:latest",
    "qwen3.6-27b-sqlbench:latest",
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
                "items": {"type": ["string", "number", "integer", "boolean", "null"]},
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


def scalar_for_json(value: Any) -> Any:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def json_safe(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: scalar_for_json(v) for k, v in row.items()}


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
            valid_power = [x for x in power if not math.isnan(x)]
            valid_temp = [x for x in temp if not math.isnan(x)]
            return {
                "gpu_util_avg_pct": sum(utils) / len(utils),
                "gpu_util_max_pct": max(utils),
                "gpu_mem_used_mib": sum(mem_used),
                "gpu_mem_total_mib": sum(mem_total),
                "gpu_mem_util_pct": 100.0 * safe_div(sum(mem_used), sum(mem_total)),
                "gpu_power_draw_w": None if not valid_power else sum(valid_power),
                "gpu_temp_avg_c": None if not valid_temp else sum(valid_temp) / len(valid_temp),
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


def call_nonstream(path: str, payload: dict, model: str, case_attempt_id: str) -> dict:
    url = BASE + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    t0 = time.perf_counter()
    hb = Heartbeat(model=model, case_id=case_attempt_id, endpoint_name=path, started_at=t0)
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


def invoke_nonstream(path: str, model: str, prompt: str, schema: dict, case_attempt_id: str, options: dict, keep_alive: str) -> dict:
    if path == "/generate":
        payload = build_generate_payload(model, prompt, schema, options, keep_alive)
    else:
        payload = build_chat_payload(model, prompt, schema, options, keep_alive)
    return call_nonstream(path, payload, model, case_attempt_id)


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


def load_query_engineering_registry(repo_root: Path, manifest: dict, args: argparse.Namespace) -> dict:
    if not getattr(args, "query_engineering", True):
        return {}

    cfg = manifest.get("query_engineering", {}) or {}
    registry_value = args.query_engineering_registry or cfg.get("registry_file")
    if not registry_value:
        return {}
    registry_path = Path(registry_value)
    if not registry_path.is_absolute():
        registry_path = repo_root / registry_path
    if not registry_path.exists():
        raise FileNotFoundError(f"Query engineering registry not found: {registry_path}")
    registry = load_json(registry_path)
    registry["_registry_path"] = str(registry_path)
    return registry


def model_guidance_entry(registry: dict, model: str, case_id: str) -> Optional[dict]:
    if not registry:
        return None
    guidance_by_model = registry.get("guidance_by_model", {})
    model_entry = guidance_by_model.get(model)
    if model_entry is None and model.endswith(":latest"):
        model_entry = guidance_by_model.get(model[:-7])
    if model_entry is None:
        return None
    return (model_entry.get("cases") or {}).get(case_id)


def build_case_prompt(
    case: dict,
    dataset: dict,
    instruction_lookup: Dict[str, dict],
    answer_columns: List[str],
    model_guidance: Optional[dict] = None,
) -> str:
    inst = instruction_lookup[case["standard_instructions_id"]]["text"].strip()
    table_blocks = []
    for table_name, table in dataset["tables"].items():
        table_blocks.append(f"{table_name}:\n{make_csv_text(table_name, table)}")

    output_columns_text = ", ".join(answer_columns)
    model_guidance_text = ""
    if model_guidance and model_guidance.get("text"):
        heading = model_guidance.get("heading") or "Model-specific guidance for v5"
        model_guidance_text = (
            f"{heading}:\n"
            f"{str(model_guidance['text']).strip()}\n\n"
        )

    return (
        "/no_think\n"
        "You are benchmarking a local model on data analysis accuracy.\n\n"
        f"{inst}\n\n"
        "For this automated benchmark run, do NOT output SQL or Python code.\n"
        "Return ONLY the final result table as JSON matching the required schema.\n"
        'The JSON must be: {"columns": [...], "rows": [[...], ...]}\n'
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
        + model_guidance_text
        + f"Return these columns in this exact order:\n{output_columns_text}\n"
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
    results_template = load_jsonl(base_dir / manifest["results_template_file"]) if manifest.get("results_template_file") else []

    if validate:
        validate_records(cases, case_schema, base_dir / manifest["cases_file"])
        validate_records(gold, gold_schema, base_dir / manifest["gold_file"])

    instruction_lookup = {x["standard_instructions_id"]: x for x in instructions["instructions"]}
    gold_lookup = {x["case_id"]: x for x in gold}
    template_lookup: Dict[Tuple[str, int], dict] = {}
    for rec in results_template:
        template_lookup[(rec["case_id"], int(rec["attempt_index"]))] = rec

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
        "template_lookup": template_lookup,
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


def canonicalize_table(columns: List[str], rows: List[List[Any]]) -> Tuple[List[str], List[List[Any]]]:
    return [canonicalize_scalar(x) for x in columns], [list(canonicalize_row(r)) for r in rows]


def compare_numeric(gold_value: Any, pred_value: Any, tol: float) -> bool:
    gv = canonicalize_scalar(gold_value)
    pv = canonicalize_scalar(pred_value)
    if gv is None and pv is None:
        return True
    try:
        return abs(float(gv) - float(pv)) <= tol
    except Exception:
        return gv == pv


def build_row_dicts(columns: List[str], rows: List[List[Any]]) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        d = {}
        for i, col in enumerate(columns):
            d[col] = canonicalize_scalar(row[i]) if i < len(row) else None
        out.append(d)
    return out


def with_occurrence_keys(row_dicts: List[Dict[str, Any]], identity_cols: List[str]) -> List[Tuple[Tuple[Any, ...], int, Dict[str, Any]]]:
    seen: Dict[Tuple[Any, ...], int] = defaultdict(int)
    out = []
    for row in row_dicts:
        identity = tuple(row.get(col) for col in identity_cols)
        seen[identity] += 1
        out.append((identity, seen[identity], row))
    return out


def score_exact_ordered_table(case: dict, gold: dict, pred_columns: List[str], pred_rows: List[List[Any]]) -> Dict[str, Any]:
    gold_columns, gold_rows = gold["columns"], gold["rows"]
    row_order_matters = case["scoring"].get("row_order_matters", True)
    column_order_matters = case["scoring"].get("column_order_matters", True)

    gold_columns_norm, gold_rows_norm = canonicalize_table(gold_columns, gold_rows)
    pred_columns_norm, pred_rows_norm = canonicalize_table(pred_columns, pred_rows)

    column_exact_match = (
        pred_columns_norm == gold_columns_norm
        if column_order_matters
        else sorted(pred_columns_norm) == sorted(gold_columns_norm)
    )
    row_exact_match = (
        pred_rows_norm == gold_rows_norm
        if row_order_matters
        else Counter(map(tuple, pred_rows_norm)) == Counter(map(tuple, gold_rows_norm))
    )
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
        "row_set_correctness_score": 1.0 if row_exact_match else 0.0,
        "numeric_correctness_score": 1.0 if row_exact_match else 0.0,
        "sort_order_correctness_score": 1.0 if row_exact_match else 0.0,
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


def score_row_numeric_sort_split(case: dict, gold: dict, pred_columns: List[str], pred_rows: List[List[Any]]) -> Dict[str, Any]:
    gold_columns = gold["columns"]
    gold_rows = gold["rows"]
    scoring_cfg = case["scoring"]
    weights = scoring_cfg["split_weights"]
    tol = float(scoring_cfg.get("numeric_tolerance_abs", 0.0))
    identity_cols = list(scoring_cfg["row_identity_columns"])
    numeric_cols = list(scoring_cfg.get("numeric_columns", []))

    gold_columns_norm, gold_rows_norm = canonicalize_table(gold_columns, gold_rows)
    pred_columns_norm, pred_rows_norm = canonicalize_table(pred_columns, pred_rows)

    row_order_matters = scoring_cfg.get("row_order_matters", True)
    column_order_matters = scoring_cfg.get("column_order_matters", True)

    column_exact_match = (
        pred_columns_norm == gold_columns_norm
        if column_order_matters
        else sorted(pred_columns_norm) == sorted(gold_columns_norm)
    )
    row_exact_match = (
        pred_rows_norm == gold_rows_norm
        if row_order_matters
        else Counter(map(tuple, pred_rows_norm)) == Counter(map(tuple, gold_rows_norm))
    )
    exact_match = column_exact_match and row_exact_match

    gold_row_dicts = build_row_dicts(gold_columns_norm, gold_rows_norm)
    pred_row_dicts = build_row_dicts(pred_columns_norm, pred_rows_norm)
    gold_eff = with_occurrence_keys(gold_row_dicts, identity_cols) if all(c in gold_columns_norm for c in identity_cols) else []
    pred_eff = with_occurrence_keys(pred_row_dicts, identity_cols) if all(c in pred_columns_norm for c in identity_cols) else []

    gold_eff_keys = [(ident, occ) for ident, occ, _ in gold_eff]
    pred_eff_keys = [(ident, occ) for ident, occ, _ in pred_eff]

    gold_counter = Counter(gold_eff_keys)
    pred_counter = Counter(pred_eff_keys)
    matched_counter = gold_counter & pred_counter
    matched_row_count = sum(matched_counter.values())
    row_set_den = max(len(gold_eff_keys), len(pred_eff_keys), 1)
    row_set_correctness_score = safe_div(matched_row_count, row_set_den)

    pred_eff_map = {(ident, occ): row for ident, occ, row in pred_eff}
    numeric_total = max(len(gold_eff_keys) * max(len(numeric_cols), 1), 1)
    numeric_matches = 0

    if not numeric_cols:
        numeric_correctness_score = 1.0
    else:
        for ident, occ, gold_row in gold_eff:
            pred_row = pred_eff_map.get((ident, occ))
            for col in numeric_cols:
                if pred_row is not None and col in gold_row and col in pred_row and compare_numeric(gold_row.get(col), pred_row.get(col), tol):
                    numeric_matches += 1
        numeric_correctness_score = safe_div(numeric_matches, len(gold_eff_keys) * len(numeric_cols))

    sort_den = max(len(gold_eff_keys), len(pred_eff_keys), 1)
    sort_pos_matches = 0
    for i in range(min(len(gold_eff_keys), len(pred_eff_keys))):
        if gold_eff_keys[i] == pred_eff_keys[i]:
            sort_pos_matches += 1
    sort_order_correctness_score = safe_div(sort_pos_matches, sort_den)

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

    total_score = (
        weights["row_set_correctness"] * row_set_correctness_score
        + weights["numeric_correctness"] * numeric_correctness_score
        + weights["sort_order_correctness"] * sort_order_correctness_score
    )

    return {
        "score": total_score,
        "max_score": float(scoring_cfg.get("max_score", 1.0)),
        "row_set_correctness_score": row_set_correctness_score,
        "numeric_correctness_score": numeric_correctness_score,
        "sort_order_correctness_score": sort_order_correctness_score,
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
        "row_position_accuracy": safe_div(row_position_matches, max(len(gold_rows_norm), len(pred_rows_norm), 1)),
        "aligned_cell_matches": aligned_cell_matches,
        "aligned_total_cells": aligned_total_cells,
        "aligned_cell_accuracy": safe_div(aligned_cell_matches, max(aligned_total_cells, 1)),
        "missing_rows_count": missing_rows_count,
        "extra_rows_count": extra_rows_count,
        "matched_row_count_by_identity": matched_row_count,
        "numeric_cell_matches": numeric_matches,
        "numeric_cell_total": len(gold_eff_keys) * len(numeric_cols) if numeric_cols else 0,
    }


def score_case(case: dict, gold: dict, pred_columns: List[str], pred_rows: List[List[Any]]) -> Dict[str, Any]:
    method = case["scoring"]["method"]
    if method == "row_numeric_sort_split_v1":
        return score_row_numeric_sort_split(case, gold, pred_columns, pred_rows)
    if method == "exact_ordered_table":
        return score_exact_ordered_table(case, gold, pred_columns, pred_rows)
    raise ValueError(f"Unsupported scoring method: {method}")


def audience_band(value: int) -> str:
    if value >= 5:
        return "critical"
    if value >= 4:
        return "high"
    if value >= 3:
        return "medium"
    return "low"


def estimate_cost_usd(prompt_tokens: int, completion_tokens: int, prompt_cost_per_1m: float, completion_cost_per_1m: float) -> float:
    return (
        safe_div(prompt_tokens, 1_000_000.0) * prompt_cost_per_1m
        + safe_div(completion_tokens, 1_000_000.0) * completion_cost_per_1m
    )


def infer_repairability(case: dict, score_row: dict, manifest: dict) -> Tuple[bool, Optional[str]]:
    if score_row.get("exact_match"):
        return False, None

    repair_class = case["metadata"].get("repairability_class")
    row_score = float(score_row.get("row_set_correctness_score", 0.0) or 0.0)
    num_score = float(score_row.get("numeric_correctness_score", 0.0) or 0.0)
    sort_score = float(score_row.get("sort_order_correctness_score", 0.0) or 0.0)
    total_score = float(score_row.get("score", 0.0) or 0.0)

    if repair_class == "human_repairable":
        example_note = None
        for ex in manifest.get("repairable_near_miss_examples", []):
            if ex.get("case_id") == case["case_id"]:
                example_note = ex.get("why_salvageable")
                break

        likely = (
            (row_score >= 0.99 and num_score >= 0.99 and sort_score < 1.0)
            or (row_score >= 0.80 and num_score >= 0.80 and total_score >= 0.80)
        )
        if likely:
            note = example_note or "Human review can likely salvage this near-miss without recomputing the full analysis."
            return True, note
    return False, None


def run_case(
    model: str,
    provider: str,
    case: dict,
    gold: dict,
    dataset: dict,
    instruction_lookup: Dict[str, dict],
    options: dict,
    keep_alive: str,
    cold_start: bool,
    attempt_index: int,
    repeat_group_id: str,
    repeat_count_planned: int,
    manifest: dict,
    query_engineering_registry: dict,
    prompt_cost_per_1m: float,
    completion_cost_per_1m: float,
) -> dict:
    case_id = case["case_id"]
    answer_columns = gold["columns"]
    guidance = model_guidance_entry(query_engineering_registry, model, case_id)
    prompt = build_case_prompt(case, dataset, instruction_lookup, answer_columns, guidance)

    if cold_start:
        log(f"{model} {case_id} attempt={attempt_index}: cold start requested; stopping loaded copy first")
        stop_model(model)

    primary_path = "/generate"
    fallback_path = "/chat"
    fallback_used = False
    parse_error = ""
    output_validation_error = ""
    status = "ok"
    error = None
    parsed = None

    prompt_chars = len(prompt)
    prompt_bytes = len(prompt.encode("utf-8"))

    try:
        case_attempt_id = f"{case_id}.attempt{attempt_index}"
        log(f"{model} {case_id} attempt={attempt_index}: starting primary request via {primary_path}")
        primary = invoke_nonstream(primary_path, model, prompt, OUTPUT_TABLE_SCHEMA, case_attempt_id, options, keep_alive)
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
            log(f"{model} {case_id} attempt={attempt_index}: primary invalid; retrying via {fallback_path}")
            fallback = invoke_nonstream(fallback_path, model, prompt, OUTPUT_TABLE_SCHEMA, case_attempt_id + ".fallback_chat", options, keep_alive)
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
            scoring = score_case(case, gold, pred_columns, pred_rows)
        else:
            pred_columns = []
            pred_rows = []
            scoring = score_case(case, gold, pred_columns, pred_rows)
            scoring["score"] = 0.0
            scoring["row_set_correctness_score"] = 0.0
            scoring["numeric_correctness_score"] = 0.0
            scoring["sort_order_correctness_score"] = 0.0

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
        scoring = score_case(case, gold, pred_columns, pred_rows)
        scoring["score"] = 0.0
        scoring["row_set_correctness_score"] = 0.0
        scoring["numeric_correctness_score"] = 0.0
        scoring["sort_order_correctness_score"] = 0.0
        parse_error = error

    ps = get_ps_model(model) or {}
    ps_loaded_gib = bytes_to_gib(ps.get("size", 0) or 0)
    ps_vram_gib = bytes_to_gib(ps.get("size_vram", 0) or 0)

    prompt_tokens = int(result.get("server_prompt_eval_count", 0) or 0)
    completion_tokens = int(result.get("server_eval_count", 0) or 0)
    total_tokens = prompt_tokens + completion_tokens
    estimated_cost = estimate_cost_usd(prompt_tokens, completion_tokens, prompt_cost_per_1m, completion_cost_per_1m)

    repairable_near_miss, repair_notes = infer_repairability(case, scoring, manifest)
    if scoring.get("exact_match"):
        failure_families = []
        primary_failure_family = None
    else:
        failure_families = list(case["metadata"].get("failure_families", []))
        primary_failure_family = case["metadata"].get("failure_family_primary")

    audience = case["metadata"].get("audience_relevance", {})
    row = {
        "benchmark_id": case["benchmark_id"],
        "dataset_id": case["dataset_id"],
        "case_id": case["case_id"],
        "pass": case["pass"],
        "query": case["query"],
        "difficulty": case["difficulty"],
        "language": case["language"],
        "model": model,
        "provider": provider,
        "attempt_index": attempt_index,
        "repeat_group_id": repeat_group_id,
        "repeat_count_planned": repeat_count_planned,
        "status": status,
        "cold_start": cold_start,
        "endpoint_used": result["endpoint_used"],
        "fallback_used": fallback_used,
        "valid_json": parsed is not None if status == "ok" else False,
        "score": scoring["score"],
        "max_score": scoring["max_score"],
        "row_set_correctness_score": scoring.get("row_set_correctness_score"),
        "numeric_correctness_score": scoring.get("numeric_correctness_score"),
        "sort_order_correctness_score": scoring.get("sort_order_correctness_score"),
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
        "server_prompt_eval_count": prompt_tokens,
        "server_eval_count": completion_tokens,
        "server_prompt_tps": safe_div(prompt_tokens, result["server_prompt_eval_s"]),
        "server_gen_tps": safe_div(completion_tokens, result["server_eval_s"]),
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
        "query_engineering_registry_id": query_engineering_registry.get("registry_id", "") if query_engineering_registry else "",
        "query_engineering_registry_path": query_engineering_registry.get("_registry_path", "") if query_engineering_registry else "",
        "query_engineering_addendum_id": guidance.get("addendum_id", "") if guidance else "",
        "query_engineering_model_family": guidance.get("model_family", "") if guidance else "",
        "query_engineering_source_runs": json.dumps(guidance.get("source_runs", []), ensure_ascii=False) if guidance else "[]",
        "query_engineering_addendum_chars": len(guidance.get("text", "")) if guidance else 0,
        "query_engineering_prompt_parts": 2 if guidance else 1,
        "ps_context": ps.get("context_length"),
        "ps_loaded_gib": ps_loaded_gib,
        "ps_vram_gib": ps_vram_gib,
        "ps_expires_at": ps.get("expires_at", ""),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": estimated_cost,
        "cost_per_correct_answer_usd": estimated_cost,
        "repairable_near_miss": repairable_near_miss,
        "repair_notes": repair_notes or "",
        "failure_family_primary_case": case["metadata"].get("failure_family_primary"),
        "failure_families_case_json": json.dumps(case["metadata"].get("failure_families", []), ensure_ascii=False),
        "result_failure_families_json": json.dumps(failure_families, ensure_ascii=False),
        "result_primary_failure_family": primary_failure_family or "",
        "repairability_class": case["metadata"].get("repairability_class", ""),
        "tags_json": json.dumps(case["metadata"].get("tags", []), ensure_ascii=False),
        "procurement_relevance": audience.get("procurement"),
        "research_relevance": audience.get("research"),
        "model_selection_relevance": audience.get("model_selection"),
        "procurement_score_band": audience_band(int(audience.get("procurement", 1))),
        "research_score_band": audience_band(int(audience.get("research", 1))),
        "model_selection_score_band": audience_band(int(audience.get("model_selection", 1))),
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
        f"{model} {case_id} attempt={attempt_index}: status={row['status']} valid_json={row['valid_json']} "
        f"score={row['score']:.3f}/{row['max_score']:.1f} exact={row['exact_match']} "
        f"row={row['row_set_correctness_score']:.3f} num={row['numeric_correctness_score']:.3f} "
        f"sort={row['sort_order_correctness_score']:.3f}"
    )
    log(
        f"{model} {case_id} attempt={attempt_index}: wall={row['client_wall_s']:.2f}s total={row['server_total_s']:.2f}s "
        f"load={row['server_load_s']:.2f}s prompt_eval={row['server_prompt_eval_s']:.2f}s eval={row['server_eval_s']:.2f}s "
        f"prompt_toks={prompt_tokens} completion_toks={completion_tokens}"
    )
    log(
        f"{model} {case_id} attempt={attempt_index}: prompt_tps={row['server_prompt_tps']:.2f} gen_tps={row['server_gen_tps']:.2f} "
        f"gpu_share={100 * row['ps_vram_ratio']:.0f}% host_share={100 * row['ps_host_ratio_est']:.0f}% "
        f"loaded_gib={row['ps_loaded_gib']:.2f} vram_gib={row['ps_vram_gib']:.2f} cost_usd={row['estimated_cost_usd']:.6f}"
    )
    if row.get("resource_samples", 0):
        log(
            f"{model} {case_id} attempt={attempt_index}: sys_cpu_avg={row.get('system_cpu_avg', 0.0):.1f}% "
            f"ollama_cpu_avg={row.get('ollama_cpu_avg', 0.0):.1f}% "
            f"ollama_rss_avg_mib={row.get('ollama_rss_mib_avg', 0.0):.1f}"
        )

    if row["parse_error"]:
        response_sample = row["response_text"][:800].replace("\n", "\\n")
        log(f"{model} {case_id} attempt={attempt_index}: parse_error={row['parse_error']}")
        log(f"{model} {case_id} attempt={attempt_index}: raw_response_sample={response_sample!r}")

    return json_safe(row)


def make_run_result_record(benchmark_id: str, run_id: str, row: dict) -> dict:
    rec = {
        "benchmark_id": benchmark_id,
        "run_id": run_id,
        "case_id": row["case_id"],
        "model_name": row["model"],
        "provider": row["provider"],
        "attempt_index": row["attempt_index"],
        "repeat_group_id": row["repeat_group_id"],
        "repeat_count_planned": row["repeat_count_planned"],
        "status": "error" if row.get("status") == "error" else "ok",
        "answer_text": row.get("response_text") or None,
        "parsed_columns": json.loads(row.get("parsed_columns_json") or "null"),
        "parsed_rows": json.loads(row.get("parsed_rows_json") or "null"),
        "score": row.get("score"),
        "max_score": row.get("max_score"),
        "row_set_correctness_score": row.get("row_set_correctness_score"),
        "numeric_correctness_score": row.get("numeric_correctness_score"),
        "sort_order_correctness_score": row.get("sort_order_correctness_score"),
        "exact_match": row.get("exact_match"),
        "failure_families": json.loads(row.get("result_failure_families_json") or "[]"),
        "primary_failure_family": row.get("result_primary_failure_family") or None,
        "repairable_near_miss": row.get("repairable_near_miss"),
        "repair_notes": row.get("repair_notes") or None,
        "prompt_tokens": row.get("prompt_tokens"),
        "completion_tokens": row.get("completion_tokens"),
        "total_tokens": row.get("total_tokens"),
        "estimated_cost_usd": row.get("estimated_cost_usd"),
        "cost_per_correct_answer_usd": row.get("cost_per_correct_answer_usd"),
        "wall_s": row.get("client_wall_s"),
        "error": row.get("error") or row.get("parse_error") or None,
    }
    return json_safe(rec)


def aggregate_rows(rows: List[dict], group_keys: List[str]) -> List[dict]:
    groups: Dict[Tuple[Any, ...], List[dict]] = {}
    for row in rows:
        key = tuple(row.get(k) for k in group_keys)
        groups.setdefault(key, []).append(row)

    out = []
    for key, items in sorted(groups.items()):
        rec = {k: v for k, v in zip(group_keys, key)}
        scores = [float(x.get("score", 0.0) or 0.0) for x in items]
        row_scores = [float(x.get("row_set_correctness_score", 0.0) or 0.0) for x in items]
        num_scores = [float(x.get("numeric_correctness_score", 0.0) or 0.0) for x in items]
        sort_scores = [float(x.get("sort_order_correctness_score", 0.0) or 0.0) for x in items]
        exacts = [bool(x.get("exact_match")) for x in items]

        rec["attempts"] = len(items)
        rec["exact_matches"] = sum(exacts)
        rec["valid_json_attempts"] = sum(1 for x in items if x.get("valid_json"))
        rec["score_total"] = sum(scores)
        rec["max_score_total"] = sum(float(x.get("max_score", 0.0) or 0.0) for x in items)
        rec["mean_score"] = safe_div(rec["score_total"], rec["attempts"])
        rec["accuracy"] = safe_div(rec["score_total"], rec["max_score_total"])
        rec["exact_match_rate"] = safe_div(rec["exact_matches"], rec["attempts"])
        rec["valid_json_rate"] = safe_div(rec["valid_json_attempts"], rec["attempts"])
        rec["row_set_correctness_mean"] = safe_div(sum(row_scores), rec["attempts"])
        rec["numeric_correctness_mean"] = safe_div(sum(num_scores), rec["attempts"])
        rec["sort_order_correctness_mean"] = safe_div(sum(sort_scores), rec["attempts"])
        rec["estimated_cost_usd_total"] = sum(float(x.get("estimated_cost_usd", 0.0) or 0.0) for x in items)
        rec["cost_per_correct_answer_usd"] = safe_div(rec["estimated_cost_usd_total"], max(rec["exact_matches"], 1))
        rec["wall_s_total"] = sum(float(x.get("client_wall_s", 0.0) or 0.0) for x in items)
        rec["wall_s_mean"] = safe_div(rec["wall_s_total"], rec["attempts"])
        rec["server_total_s_total"] = sum(float(x.get("server_total_s", 0.0) or 0.0) for x in items)
        rec["prompt_tokens_total"] = sum(int(x.get("prompt_tokens", 0) or 0) for x in items)
        rec["completion_tokens_total"] = sum(int(x.get("completion_tokens", 0) or 0) for x in items)
        rec["total_tokens_total"] = sum(int(x.get("total_tokens", 0) or 0) for x in items)
        rec["mean_gen_tps"] = safe_div(sum(float(x.get("server_gen_tps", 0.0) or 0.0) for x in items), rec["attempts"])
        rec["mean_prompt_tps"] = safe_div(sum(float(x.get("server_prompt_tps", 0.0) or 0.0) for x in items), rec["attempts"])
        rec["mean_ps_loaded_gib"] = safe_div(sum(float(x.get("ps_loaded_gib", 0.0) or 0.0) for x in items), rec["attempts"])
        rec["mean_ps_vram_gib"] = safe_div(sum(float(x.get("ps_vram_gib", 0.0) or 0.0) for x in items), rec["attempts"])
        rec["mean_system_cpu_avg"] = safe_div(sum(float(x.get("system_cpu_avg", 0.0) or 0.0) for x in items), rec["attempts"])
        rec["mean_ollama_cpu_avg"] = safe_div(sum(float(x.get("ollama_cpu_avg", 0.0) or 0.0) for x in items), rec["attempts"])
        rec["mean_gpu_util_pct_avg"] = safe_div(sum(float(x.get("gpu_util_pct_avg", 0.0) or 0.0) for x in items), rec["attempts"])
        out.append(json_safe(rec))
    return out


def explode_failure_family_rows(rows: List[dict]) -> List[dict]:
    out = []
    for row in rows:
        families = json.loads(row.get("failure_families_case_json") or "[]")
        for family in families:
            rec = dict(row)
            rec["failure_family"] = family
            out.append(rec)
    return out


def build_repeatability_summary(rows: List[dict]) -> List[dict]:
    groups: Dict[Tuple[str, str], List[dict]] = defaultdict(list)
    for row in rows:
        groups[(str(row["model"]), str(row["case_id"]))].append(row)

    out = []
    for (model, case_id), items in sorted(groups.items()):
        items = sorted(items, key=lambda x: int(x["attempt_index"]))
        scores = [float(x.get("score", 0.0) or 0.0) for x in items]
        exacts = [bool(x.get("exact_match")) for x in items]
        mean_score = safe_div(sum(scores), len(scores))
        stddev = statistics.pstdev(scores) if len(scores) > 1 else 0.0
        exact_count = sum(exacts)
        stable_failure = exact_count == 0
        stable_success = exact_count == len(exacts)
        prompt_sensitive_failure = 0 < exact_count < len(exacts)

        first = items[0]
        rec = {
            "model": model,
            "case_id": case_id,
            "pass": first["pass"],
            "difficulty": first["difficulty"],
            "language": first["language"],
            "attempts": len(items),
            "attempt_exact_match_rate": safe_div(exact_count, len(exacts)),
            "attempt_score_mean": mean_score,
            "attempt_score_stddev": stddev,
            "attempt_score_cv": safe_div(stddev, mean_score) if mean_score else 0.0,
            "stable_failure": stable_failure,
            "stable_success": stable_success,
            "prompt_sensitive_failure": prompt_sensitive_failure,
            "stable_failure_rate": 1.0 if stable_failure else 0.0,
            "prompt_sensitive_failure_rate": 1.0 if prompt_sensitive_failure else 0.0,
            "failure_family_primary_case": first.get("failure_family_primary_case"),
            "failure_families_case_json": first.get("failure_families_case_json"),
            "repairability_class": first.get("repairability_class"),
            "estimated_cost_usd_total": sum(float(x.get("estimated_cost_usd", 0.0) or 0.0) for x in items),
            "wall_s_total": sum(float(x.get("client_wall_s", 0.0) or 0.0) for x in items),
        }
        out.append(json_safe(rec))
    return out


def build_model_repeatability_summary(repeat_rows: List[dict]) -> List[dict]:
    groups: Dict[str, List[dict]] = defaultdict(list)
    for row in repeat_rows:
        groups[str(row["model"])].append(row)
    out = []
    for model, items in sorted(groups.items()):
        rec = {
            "model": model,
            "cases": len(items),
            "attempt_exact_match_rate_mean": safe_div(sum(float(x["attempt_exact_match_rate"]) for x in items), len(items)),
            "attempt_score_stddev_mean": safe_div(sum(float(x["attempt_score_stddev"]) for x in items), len(items)),
            "attempt_score_cv_mean": safe_div(sum(float(x["attempt_score_cv"]) for x in items), len(items)),
            "stable_failure_rate": safe_div(sum(1 for x in items if x["stable_failure"]), len(items)),
            "prompt_sensitive_failure_rate": safe_div(sum(1 for x in items if x["prompt_sensitive_failure"]), len(items)),
            "stable_success_rate": safe_div(sum(1 for x in items if x["stable_success"]), len(items)),
        }
        out.append(json_safe(rec))
    return out


def print_summary_table(rows: List[dict]) -> None:
    cols = [
        ("model", 24),
        ("case_id", 14),
        ("att", 3),
        ("exact", 5),
        ("score", 7),
        ("row", 6),
        ("num", 6),
        ("sort", 6),
        ("gen_tps", 9),
        ("cost", 10),
    ]
    header = " ".join(name.ljust(width) for name, width in cols)
    print("\n" + header)
    print("-" * len(header))
    for r in rows:
        vals = {
            "model": str(r["model"])[:24],
            "case_id": str(r["case_id"])[:14],
            "att": str(r["attempt_index"]),
            "exact": "Y" if r.get("exact_match") else "N",
            "score": f"{r['score']:.3f}",
            "row": f"{r['row_set_correctness_score']:.2f}",
            "num": f"{r['numeric_correctness_score']:.2f}",
            "sort": f"{r['sort_order_correctness_score']:.2f}",
            "gen_tps": f"{r['server_gen_tps']:.2f}",
            "cost": f"{r['estimated_cost_usd']:.4f}",
        }
        print(" ".join(vals[name].ljust(width) for name, width in cols))


def print_model_summary(rows: List[dict]) -> None:
    agg = aggregate_rows(rows, ["model"])
    cols = [
        ("model", 24),
        ("atts", 6),
        ("exact", 7),
        ("mean", 7),
        ("row", 7),
        ("num", 7),
        ("sort", 7),
        ("cost/corr", 10),
        ("wall_s", 10),
    ]
    header = " ".join(name.ljust(width) for name, width in cols)
    print("\n" + header)
    print("-" * len(header))
    for r in agg:
        vals = {
            "model": str(r["model"])[:24],
            "atts": str(r["attempts"]),
            "exact": f"{100*r['exact_match_rate']:.1f}%",
            "mean": f"{100*r['mean_score']:.1f}%",
            "row": f"{100*r['row_set_correctness_mean']:.1f}%",
            "num": f"{100*r['numeric_correctness_mean']:.1f}%",
            "sort": f"{100*r['sort_order_correctness_mean']:.1f}%",
            "cost/corr": f"{r['cost_per_correct_answer_usd']:.4f}",
            "wall_s": f"{r['wall_s_total']:.1f}",
        }
        print(" ".join(vals[name].ljust(width) for name, width in cols))


def write_csv(path: Path, rows: List[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({k for row in rows for k in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: List[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(json_safe(row), ensure_ascii=False) + "\n")


def resolve_default_manifest() -> Path:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "benchmark_manifest.json",
        Path.cwd() / "benchmark_manifest.json",
        script_dir / "AIBioBench_v2" / "benchmark_manifest.json",
        Path.cwd() / "AIBioBench_v2" / "benchmark_manifest.json",
        script_dir / "plant_benchmark_jsonl" / "benchmark_manifest.json",
        Path.cwd() / "plant_benchmark_jsonl" / "benchmark_manifest.json",
        Path("/mnt/data/AIBioBench_v2/benchmark_manifest.json"),
        Path("/mnt/data/plant_benchmark_jsonl/benchmark_manifest.json"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Could not find benchmark_manifest.json next to the script, in the current working directory, "
        "or in supported subdirectories. Use --manifest."
    )


def resolve_default_models(args_models: Optional[List[str]], manifest: dict) -> List[str]:
    if args_models is not None:
        return args_models
    manifest_models = manifest.get("default_models")
    if isinstance(manifest_models, list) and manifest_models:
        return [str(model) for model in manifest_models]
    return list(DEFAULT_MODELS)


def bundle_dir_basename(benchmark_id: str) -> str:
    prefix = "AIBioBench_"
    return benchmark_id[len(prefix):] if benchmark_id.startswith(prefix) else benchmark_id


def resolve_shared_bundle_dir(results_root: Path, benchmark_id: str, bundle_dir_name: Optional[str] = None) -> Path:
    base_name = bundle_dir_name or bundle_dir_basename(benchmark_id)
    return results_root / base_name


def resolve_output_dir(
    requested_output_dir: Optional[Path],
    repo_root: Path,
    benchmark_id: str,
    run_id: str,
    append_output: bool,
    bundle_dir_name: Optional[str],
) -> Path:
    if requested_output_dir is not None:
        return requested_output_dir

    results_root = repo_root / "results"
    if append_output:
        return resolve_shared_bundle_dir(results_root, benchmark_id, bundle_dir_name)

    return results_root / run_id


def load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def merge_by_key(target_rows: List[dict], source_rows: List[dict], key_fields: List[str]) -> Tuple[List[dict], int]:
    merged: Dict[Tuple[Any, ...], dict] = {}
    insertion_order: List[Tuple[Any, ...]] = []
    duplicate_count = 0

    for row in target_rows + source_rows:
        key = tuple(row.get(field) for field in key_fields)
        if key in merged:
            duplicate_count += 1
        else:
            insertion_order.append(key)
        merged[key] = row

    return [merged[key] for key in insertion_order], duplicate_count


def merge_ordered_unique(existing: List[Any], incoming: List[Any]) -> List[Any]:
    out: List[Any] = []
    seen = set()
    for item in existing + incoming:
        marker = json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else item
        if marker in seen:
            continue
        seen.add(marker)
        out.append(item)
    return out


def case_sort_key(case_id: str) -> Tuple[int, int]:
    left, right = case_id.split(".query")
    return int(left.replace("pass", "")), int(right)


def build_run_meta(
    existing_meta: Optional[dict],
    manifest: dict,
    args: argparse.Namespace,
    version: str,
    models: List[str],
    selected_cases: List[dict],
    repeats: int,
    options: dict,
    repo_root: Path,
    output_dir: Path,
    run_id: str,
    run_started_at_utc: str,
    merged_rows: List[dict],
) -> dict:
    base_meta = dict(existing_meta or {})
    bundle_run_id = base_meta.get("run_id") or run_id
    merged_models = merge_ordered_unique(base_meta.get("models", []), models)
    merged_cases = sorted({row["case_id"] for row in merged_rows}, key=case_sort_key)
    merged_passes = sorted({int(row["pass"]) for row in merged_rows})
    latest_case_ids = [c["case_id"] for c in selected_cases]
    source_run_ids = base_meta.get("merged_source_run_ids", [])
    if run_id != bundle_run_id:
        source_run_ids = merge_ordered_unique(source_run_ids, [run_id])

    return {
        **base_meta,
        "run_id": bundle_run_id,
        "latest_run_id": run_id,
        "benchmark_id": manifest["benchmark_id"],
        "benchmark_version": manifest["version"],
        "manifest_path": str(args.manifest),
        "ollama_version": version,
        "provider": args.provider,
        "models": merged_models,
        "passes": merged_passes,
        "repeats": max(int(base_meta.get("repeats", 0) or 0), repeats),
        "case_count": len(merged_cases),
        "cases": merged_cases,
        "options": options,
        "keep_alive": args.keep_alive,
        "prompt_cost_per_1m": args.prompt_cost_per_1m,
        "completion_cost_per_1m": args.completion_cost_per_1m,
        "run_started_at_utc": base_meta.get("run_started_at_utc") or run_started_at_utc,
        "latest_run_started_at_utc": run_started_at_utc,
        "latest_run_models": models,
        "latest_run_case_count": len(latest_case_ids),
        "latest_run_cases": latest_case_ids,
        "latest_run_repeats": repeats,
        "output_dir": str(output_dir),
        "repo_root": str(repo_root),
        "reporting_views": manifest.get("reporting_views", {}),
        "repairable_near_miss_examples": manifest.get("repairable_near_miss_examples", []),
        "append_output_enabled": args.append_output,
        "bundle_dir_name": args.bundle_dir_name or bundle_dir_basename(manifest["benchmark_id"]),
        "query_engineering_enabled": bool(getattr(args, "query_engineering", True) and manifest.get("query_engineering")),
        "query_engineering_registry": str(args.query_engineering_registry) if getattr(args, "query_engineering_registry", None) else (manifest.get("query_engineering", {}) or {}).get("registry_file", ""),
        "merged_model_count": len(merged_models),
        "merged_attempt_count": len(merged_rows),
        "merged_source_run_ids": source_run_ids,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run AIBioBench benchmark cases from JSONL case/gold files.")
    p.add_argument("--manifest", type=Path, default=resolve_default_manifest())
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument(
        "--no-append-output",
        action="store_false",
        dest="append_output",
        help="Write a fresh timestamped results directory instead of merging into the shared benchmark bundle.",
    )
    p.add_argument(
        "--bundle-dir-name",
        default=None,
        help="Override the shared results directory basename used when appending output.",
    )
    p.add_argument("--provider", default="ollama")
    p.add_argument("--models", nargs="*", default=None)
    p.add_argument("--passes", nargs="*", type=int, default=[1, 2, 3, 4, 5])
    p.add_argument("--languages", nargs="*", default=None)
    p.add_argument("--case-ids", nargs="*", default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--repeats", type=int, default=None)
    p.add_argument("--repeat-group-id", default=None)
    p.add_argument("--no-validate", action="store_true")
    p.add_argument("--keep-alive", default=KEEP_ALIVE)
    p.add_argument("--temperature", type=float, default=DEFAULT_OPTIONS["temperature"])
    p.add_argument("--top-p", type=float, default=DEFAULT_OPTIONS["top_p"])
    p.add_argument("--top-k", type=int, default=DEFAULT_OPTIONS["top_k"])
    p.add_argument("--prompt-cost-per-1m", type=float, default=0.0)
    p.add_argument("--completion-cost-per-1m", type=float, default=0.0)
    p.add_argument(
        "--query-engineering-registry",
        type=Path,
        default=None,
        help="Override the manifest query-engineering registry path.",
    )
    p.add_argument(
        "--no-query-engineering",
        action="store_false",
        dest="query_engineering",
        help="Disable manifest-driven model-specific query addenda.",
    )
    p.add_argument("--no-cold-first-case", action="store_false", dest="cold_first_case")
    p.add_argument("--no-stop-between-models", action="store_false", dest="stop_between_models")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(cold_first_case=True, stop_between_models=True, append_output=True, query_engineering=True)
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
    models = resolve_default_models(args.models, manifest)
    repo_root = args.manifest.resolve().parent
    query_engineering_registry = load_query_engineering_registry(repo_root, manifest, args)

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

    repeats = int(args.repeats or manifest.get("default_repeats_per_case", 1))
    args.repeat_group_id = args.repeat_group_id or manifest.get("default_repeat_group_id", "default_repeatability")
    run_started_at_utc = utc_now_iso()
    run_id = f"{manifest['benchmark_id']}__{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = resolve_output_dir(
        requested_output_dir=args.output_dir,
        repo_root=repo_root,
        benchmark_id=manifest["benchmark_id"],
        run_id=run_id,
        append_output=args.append_output,
        bundle_dir_name=args.bundle_dir_name,
    )

    log(f"Manifest: {args.manifest}")
    log(f"Benchmark: {manifest['benchmark_id']} v{manifest['version']}")
    log(f"Selected cases: {len(selected_cases)} | Repeats per case: {repeats} | Models: {len(models)}")
    log(f"Output directory: {output_dir}")
    if query_engineering_registry:
        log(
            "Query engineering registry: "
            f"{query_engineering_registry.get('registry_id', '-')}"
            f" ({query_engineering_registry.get('_registry_path', '-')})"
        )
    if args.dry_run:
        for case in selected_cases:
            guidance_count = sum(1 for model in models if model_guidance_entry(query_engineering_registry, model, case["case_id"]))
            suffix = f" guidance_models={guidance_count}/{len(models)}" if query_engineering_registry else ""
            log(f"DRY RUN case={case['case_id']} pass={case['pass']} lang={case['language']} difficulty={case['difficulty']}{suffix}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    version = api_json("GET", "/version").get("version", "unknown")
    log(f"Ollama version: {version}")
    log("Stopping any currently loaded models before benchmark...")
    stop_all_loaded()

    all_rows: List[dict] = []
    result_rows: List[dict] = []

    for model in models:
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

        first_attempt = True
        for case in selected_cases:
            gold = gold_lookup[case["expected_result_id"]]
            for attempt_index in range(1, repeats + 1):
                row = run_case(
                    model=model,
                    provider=args.provider,
                    case=case,
                    gold=gold,
                    dataset=dataset,
                    instruction_lookup=instruction_lookup,
                    options=options,
                    keep_alive=args.keep_alive,
                    cold_start=bool(args.cold_first_case and first_attempt),
                    attempt_index=attempt_index,
                    repeat_group_id=args.repeat_group_id,
                    repeat_count_planned=repeats,
                    manifest=manifest,
                    query_engineering_registry=query_engineering_registry,
                    prompt_cost_per_1m=args.prompt_cost_per_1m,
                    completion_cost_per_1m=args.completion_cost_per_1m,
                )
                first_attempt = False
                row["family"] = family
                row["parameter_size"] = param_size
                row["quantization"] = quant
                row["cfg_num_ctx"] = cfg_num_ctx
                row["ollama_version"] = version
                row["run_id"] = run_id
                row["run_started_at_utc"] = run_started_at_utc
                all_rows.append(json_safe(row))

                result_rec = make_run_result_record(manifest["benchmark_id"], run_id, row)
                validate_single_record(result_rec, result_schema, f"result {model} {case['case_id']} attempt={attempt_index}")
                result_rows.append(json_safe(result_rec))

        if args.stop_between_models:
            stop_model(model)
            log(f"{model}: selected cases complete; model stopped")

    all_rows.sort(key=lambda r: (r["model"], r["case_id"], int(r["attempt_index"])))
    result_rows.sort(key=lambda r: (r["model_name"], r["case_id"], int(r["attempt_index"])))

    print_model_summary(all_rows)
    print_summary_table(all_rows)

    existing_all_rows: List[dict] = []
    existing_result_rows: List[dict] = []
    existing_meta: Optional[dict] = None
    duplicate_raw_rows = 0
    duplicate_result_rows = 0

    if args.append_output:
        detailed_jsonl = output_dir / "detailed_results.jsonl"
        run_results_jsonl = output_dir / "run_results.jsonl"
        run_meta_json = output_dir / "run_meta.json"
        existing_all_rows = load_jsonl(detailed_jsonl)
        existing_result_rows = load_jsonl(run_results_jsonl)
        if run_meta_json.exists():
            existing_meta = json.loads(run_meta_json.read_text(encoding="utf-8"))
        if existing_all_rows or existing_result_rows:
            log(
                f"Appending into existing bundle: {len(existing_all_rows)} raw rows, "
                f"{len(existing_result_rows)} result rows already present"
            )

    merged_all_rows, duplicate_raw_rows = merge_by_key(existing_all_rows, all_rows, ["model", "case_id", "attempt_index"])
    merged_result_rows, duplicate_result_rows = merge_by_key(
        existing_result_rows,
        result_rows,
        ["model_name", "case_id", "attempt_index"],
    )

    repeatability_rows = build_repeatability_summary(merged_all_rows)
    model_repeatability_rows = build_model_repeatability_summary(repeatability_rows)

    detailed_csv = output_dir / "detailed_results.csv"
    detailed_jsonl = output_dir / "detailed_results.jsonl"
    run_results_jsonl = output_dir / "run_results.jsonl"
    model_summary_csv = output_dir / "summary_by_model.csv"
    model_pass_summary_csv = output_dir / "summary_by_model_pass.csv"
    failure_primary_summary_csv = output_dir / "summary_by_failure_family_primary.csv"
    failure_exploded_summary_csv = output_dir / "summary_by_failure_family_exploded.csv"
    model_failure_primary_summary_csv = output_dir / "summary_by_model_failure_family_primary.csv"
    repeatability_csv = output_dir / "summary_repeatability_by_model_case.csv"
    model_repeatability_csv = output_dir / "summary_repeatability_by_model.csv"
    run_meta_json = output_dir / "run_meta.json"

    write_csv(detailed_csv, merged_all_rows)
    write_jsonl(detailed_jsonl, merged_all_rows)
    write_jsonl(run_results_jsonl, merged_result_rows)
    write_csv(model_summary_csv, aggregate_rows(merged_all_rows, ["model"]))
    write_csv(model_pass_summary_csv, aggregate_rows(merged_all_rows, ["model", "pass", "language", "difficulty"]))
    write_csv(failure_primary_summary_csv, aggregate_rows(merged_all_rows, ["failure_family_primary_case"]))
    write_csv(model_failure_primary_summary_csv, aggregate_rows(merged_all_rows, ["model", "failure_family_primary_case"]))
    write_csv(failure_exploded_summary_csv, aggregate_rows(explode_failure_family_rows(merged_all_rows), ["failure_family"]))
    write_csv(repeatability_csv, repeatability_rows)
    write_csv(model_repeatability_csv, model_repeatability_rows)

    run_meta = build_run_meta(
        existing_meta=existing_meta,
        manifest=manifest,
        args=args,
        version=version,
        models=models,
        selected_cases=selected_cases,
        repeats=repeats,
        options=options,
        repo_root=repo_root,
        output_dir=output_dir,
        run_id=run_id,
        run_started_at_utc=run_started_at_utc,
        merged_rows=merged_all_rows,
    )
    run_meta_json.write_text(json.dumps(run_meta, indent=2), encoding="utf-8")

    log(f"Detailed CSV written to: {detailed_csv}")
    log(f"Detailed JSONL written to: {detailed_jsonl}")
    log(f"Run results JSONL written to: {run_results_jsonl}")
    log(f"Model summary CSV written to: {model_summary_csv}")
    log(f"Model/pass summary CSV written to: {model_pass_summary_csv}")
    log(f"Failure-family summary CSV written to: {failure_primary_summary_csv}")
    log(f"Exploded failure-family summary CSV written to: {failure_exploded_summary_csv}")
    log(f"Repeatability by model/case CSV written to: {repeatability_csv}")
    log(f"Repeatability by model CSV written to: {model_repeatability_csv}")
    log(f"Run metadata JSON written to: {run_meta_json}")
    if args.append_output:
        log(
            f"Bundle totals after merge: attempts={len(merged_all_rows)} models={len(run_meta['models'])} "
            f"overwritten_raw_rows={duplicate_raw_rows} overwritten_result_rows={duplicate_result_rows}"
        )


if __name__ == "__main__":
    main()
