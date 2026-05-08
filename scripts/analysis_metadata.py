#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Iterable, Optional


def load_run_meta(results_dir: Path) -> dict:
    path = results_dir / "run_meta.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_manifest_path(results_dir: Path, repo_root: Path) -> Optional[Path]:
    manifest_value = str(load_run_meta(results_dir).get("manifest_path", "")).strip()
    if not manifest_value:
        candidate = repo_root / "benchmark_manifest.json"
    else:
        candidate = Path(manifest_value)
        if not candidate.is_absolute():
            candidate = repo_root / candidate
    return candidate if candidate.exists() else None


def benchmark_file_path(results_dir: Path, repo_root: Path, manifest_key: str, fallback_name: str) -> Path:
    manifest_path = resolve_manifest_path(results_dir, repo_root)
    if manifest_path is None:
        return repo_root / fallback_name

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    relative_path = manifest.get(manifest_key, fallback_name)
    path = Path(relative_path)
    if not path.is_absolute():
        path = manifest_path.parent / path
    return path


def load_case_meta(results_dir: Path, repo_root: Path, passes: Optional[Iterable[int]] = None) -> dict:
    wanted_passes = set(passes or [])
    path = benchmark_file_path(results_dir, repo_root, "cases_file", "benchmark_cases.jsonl")
    out = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if wanted_passes and int(row["pass"]) not in wanted_passes:
                continue
            out[row["case_id"]] = row
    return out


def load_gold_answers(results_dir: Path, repo_root: Path, passes: Optional[Iterable[int]] = None) -> dict:
    wanted_prefixes = tuple(f"pass{pass_no}." for pass_no in passes or [])
    path = benchmark_file_path(results_dir, repo_root, "gold_file", "gold_answers.jsonl")
    out = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if wanted_prefixes and not row["case_id"].startswith(wanted_prefixes):
                continue
            out[row["case_id"]] = row
    return out
