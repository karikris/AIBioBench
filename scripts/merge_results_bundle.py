#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import aibiobench


ANALYSIS_SCRIPTS = [
    ROOT / "scripts" / "pass1_analysis.py",
    ROOT / "scripts" / "pass2_analysis.py",
    ROOT / "scripts" / "pass3_analysis.py",
    ROOT / "scripts" / "pass4_analysis.py",
    ROOT / "scripts" / "pass5_analysis.py",
    ROOT / "scripts" / "pass123_overall_analysis.py",
    ROOT / "scripts" / "pass45_overall_analysis.py",
    ROOT / "scripts" / "all_passes_overview_analysis.py",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge one benchmark result bundle into another and regenerate summaries.")
    parser.add_argument("target_dir", type=Path, help="Existing results directory to update in-place.")
    parser.add_argument("source_dir", type=Path, help="Source results directory to union into the target.")
    parser.add_argument("--skip-analysis", action="store_true", help="Only rewrite root raw/summary files.")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def merge_by_key(target_rows: list[dict], source_rows: list[dict], key_fields: list[str]) -> tuple[list[dict], int]:
    merged: dict[tuple, dict] = {}
    insertion_order: list[tuple] = []
    duplicate_count = 0

    for row in target_rows + source_rows:
        key = tuple(row.get(field) for field in key_fields)
        if key in merged:
            duplicate_count += 1
        else:
            insertion_order.append(key)
        merged[key] = row

    return [merged[key] for key in insertion_order], duplicate_count


def case_sort_key(case_id: str) -> tuple[int, int]:
    left, right = case_id.split(".query")
    return int(left.replace("pass", "")), int(right)


def merge_ordered_unique(existing: list, incoming: list) -> list:
    out = []
    seen = set()
    for item in existing + incoming:
        marker = json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else item
        if marker in seen:
            continue
        seen.add(marker)
        out.append(item)
    return out


def build_run_meta(target_meta: dict, source_meta: dict, target_dir: Path, source_dir: Path, all_rows: list[dict]) -> dict:
    merged_meta = dict(target_meta)
    merged_meta["models"] = merge_ordered_unique(target_meta.get("models", []), source_meta.get("models", []))
    merged_meta["passes"] = sorted({int(row["pass"]) for row in all_rows})
    merged_meta["cases"] = sorted({row["case_id"] for row in all_rows}, key=case_sort_key)
    merged_meta["case_count"] = len(merged_meta["cases"])
    merged_meta["repeats"] = max(int(row["attempt_index"]) for row in all_rows)
    merged_meta["output_dir"] = str(target_dir)
    merged_meta["repo_root"] = str(ROOT)
    merged_meta["merged_source_run_ids"] = merge_ordered_unique(
        target_meta.get("merged_source_run_ids", []),
        [source_meta.get("run_id")] if source_meta.get("run_id") else [],
    )
    merged_meta["merged_source_dirs"] = merge_ordered_unique(
        target_meta.get("merged_source_dirs", []),
        [str(source_dir.resolve())],
    )
    merged_meta["merged_model_count"] = len(merged_meta["models"])
    merged_meta["merged_attempt_count"] = len(all_rows)
    merged_meta["merged_at_utc"] = aibiobench.utc_now_iso()
    if "reporting_views" not in merged_meta and "reporting_views" in source_meta:
        merged_meta["reporting_views"] = source_meta["reporting_views"]
    if "repairable_near_miss_examples" not in merged_meta and "repairable_near_miss_examples" in source_meta:
        merged_meta["repairable_near_miss_examples"] = source_meta["repairable_near_miss_examples"]
    return merged_meta


def regenerate_root_files(target_dir: Path, all_rows: list[dict], result_rows: list[dict], run_meta: dict) -> None:
    all_rows = sorted(all_rows, key=lambda r: (r["model"], r["case_id"], int(r["attempt_index"])))
    result_rows = sorted(result_rows, key=lambda r: (r["model_name"], r["case_id"], int(r["attempt_index"])))

    repeatability_rows = aibiobench.build_repeatability_summary(all_rows)
    model_repeatability_rows = aibiobench.build_model_repeatability_summary(repeatability_rows)

    aibiobench.write_csv(target_dir / "detailed_results.csv", all_rows)
    aibiobench.write_jsonl(target_dir / "detailed_results.jsonl", all_rows)
    aibiobench.write_jsonl(target_dir / "run_results.jsonl", result_rows)
    aibiobench.write_csv(target_dir / "summary_by_model.csv", aibiobench.aggregate_rows(all_rows, ["model"]))
    aibiobench.write_csv(
        target_dir / "summary_by_model_pass.csv",
        aibiobench.aggregate_rows(all_rows, ["model", "pass", "language", "difficulty"]),
    )
    aibiobench.write_csv(
        target_dir / "summary_by_failure_family_primary.csv",
        aibiobench.aggregate_rows(all_rows, ["failure_family_primary_case"]),
    )
    aibiobench.write_csv(
        target_dir / "summary_by_model_failure_family_primary.csv",
        aibiobench.aggregate_rows(all_rows, ["model", "failure_family_primary_case"]),
    )
    aibiobench.write_csv(
        target_dir / "summary_by_failure_family_exploded.csv",
        aibiobench.aggregate_rows(aibiobench.explode_failure_family_rows(all_rows), ["failure_family"]),
    )
    aibiobench.write_csv(target_dir / "summary_repeatability_by_model_case.csv", repeatability_rows)
    aibiobench.write_csv(target_dir / "summary_repeatability_by_model.csv", model_repeatability_rows)
    write_json(target_dir / "run_meta.json", run_meta)


def rerun_analysis_bundles(target_dir: Path) -> None:
    env = dict(os.environ)
    env.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    for script in ANALYSIS_SCRIPTS:
        subprocess.run([sys.executable, str(script), str(target_dir)], cwd=ROOT, env=env, check=True)


def main() -> None:
    args = parse_args()
    target_dir = args.target_dir.resolve()
    source_dir = args.source_dir.resolve()

    target_rows = load_jsonl(target_dir / "detailed_results.jsonl")
    source_rows = load_jsonl(source_dir / "detailed_results.jsonl")
    merged_rows, raw_duplicates = merge_by_key(target_rows, source_rows, ["model", "case_id", "attempt_index"])

    target_result_rows = load_jsonl(target_dir / "run_results.jsonl")
    source_result_rows = load_jsonl(source_dir / "run_results.jsonl")
    merged_result_rows, result_duplicates = merge_by_key(
        target_result_rows,
        source_result_rows,
        ["model_name", "case_id", "attempt_index"],
    )

    target_meta = json.loads((target_dir / "run_meta.json").read_text(encoding="utf-8"))
    source_meta = json.loads((source_dir / "run_meta.json").read_text(encoding="utf-8"))
    merged_meta = build_run_meta(target_meta, source_meta, target_dir, source_dir, merged_rows)

    regenerate_root_files(target_dir, merged_rows, merged_result_rows, merged_meta)

    if not args.skip_analysis:
        rerun_analysis_bundles(target_dir)

    print(
        json.dumps(
            {
                "target_dir": str(target_dir),
                "source_dir": str(source_dir),
                "merged_models": merged_meta["models"],
                "merged_model_count": merged_meta["merged_model_count"],
                "merged_attempt_count": merged_meta["merged_attempt_count"],
                "raw_duplicate_rows_overwritten": raw_duplicates,
                "run_result_duplicate_rows_overwritten": result_duplicates,
                "analysis_regenerated": not args.skip_analysis,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
