#!/usr/bin/env python3
"""Prepare the photosynthesis snowflake benchmark for the v5 prompt pass.

v5 keeps the shared standard instructions at the shorter v2/v4 wording and
keeps every case prompt's first part byte-for-byte aligned to the v2/v3 base
query text.  Model-specific guidance is stored in a registry and appended by
the runner at request time.
"""

from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pass4_analysis as base
from prepare_v4_queries import PYTHON_STANDARD_V2_TEXT, SQL_STANDARD_V2_TEXT, strip_existing_guidance


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ID = "AIBioBench_photosynthesis_snowflake_v5"
SQL_STANDARD_ID = "sql_v5"
PYTHON_STANDARD_ID = "python_v5"
REPEAT_GROUP_ID = "default_repeatability_v5"
REGISTRY_ROOT = REPO_ROOT / "query_engineering_registry"
V5_DIR = REGISTRY_ROOT / "v5"
REGISTRY_ID = "photosynthesis_snowflake_v5_model_query_guidance"
MODEL_GUIDANCE_FILE = V5_DIR / "model_query_guidance.json"

RUN_REFS = {
    "v2": "2f8b7c5^",
    "v3": "2f8b7c5",
    "v4": "9892f7a",
}

MODE_GUIDANCE = {
    "row_count_mismatch": "Resolve the row boundary before calculating values: identify the preserving table, join type, explicit filters, and whether orphan/unmatched rows should survive.",
    "same_count_wrong_values": "The row shape may look plausible while values are wrong; recompute attributes and numeric columns from the joined/filter-preserved rows instead of filling plausible values.",
    "order_only": "Your main risk is final ordering; make the last operation an explicit ORDER BY or DataFrame sort_values using the requested sort keys and tie-breakers.",
    "type_only": "Keep the same row and column structure but normalize output types: JSON null for missing values, numbers as numbers, and booleans as true/false.",
    "column_error": "Return exactly the requested columns in the requested order. Do not add helper columns, comments, row numbers, confidence fields, or alternative summaries.",
    "invalid_json_or_error": "Return only valid JSON matching {\"columns\": [...], \"rows\": [[...], ...]}; no markdown, code block, prose, or trailing analysis.",
}

COMPONENT_GUIDANCE = {
    "row_set": "Row-set score was weak before; do a row identity audit before values: each output row should correspond to the requested grain only.",
    "numeric": "Numeric score was weak before; calculate formulas from unrounded intermediate values and round only the final displayed decimals.",
    "sort": "Sort score was weak before; verify the final output order after all filtering, grouping, and calculations.",
}

SAFE_ISSUE_GUIDANCE = {
    "over_inclusion": "Historical query-level risk: prior attempts included rows or groups that should be removed by the requested join/filter boundary.",
    "under_inclusion": "Historical query-level risk: prior attempts dropped rows or groups that should be preserved by the requested join/filter boundary.",
    "sort": "Historical query-level risk: prior attempts produced the right-looking table but missed the requested final sort and tie-break order.",
    "numeric": "Historical query-level risk: prior attempts used the wrong arithmetic grain, denominator, or unrounded intermediate values.",
    "grouping": "Historical query-level risk: prior attempts grouped at the wrong grain or returned the wrong set of output groups.",
    "classification": "Historical query-level risk: prior attempts assigned the wrong status/reason/repairability class after the joins.",
    "null_key_type": "Historical query-level risk: prior attempts mishandled nulls, coalesced keys, or JSON scalar types for unmatched rows.",
    "attribute_mapping": "Historical query-level risk: prior attempts mapped attributes or expression fields from the wrong joined row.",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_jsonl_text(text: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return load_jsonl_text(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n", encoding="utf-8")


def git_show_jsonl(ref: str, path: str) -> list[dict[str, Any]]:
    text = subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=REPO_ROOT, text=True)
    return load_jsonl_text(text)


def git_show_json(ref: str, path: str) -> dict[str, Any]:
    text = subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=REPO_ROOT, text=True)
    return json.loads(text)


def case_sort_key(case_id: str) -> tuple[int, int]:
    pass_text, query_text = case_id.replace("pass", "").split(".query")
    return int(pass_text), int(query_text)


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def model_family_from_rows(rows: list[dict[str, str]]) -> str:
    values = [row.get("family", "") for row in rows if row.get("family")]
    return Counter(values).most_common(1)[0][0] if values else ""


def load_result_rows(run_name: str) -> list[dict[str, Any]]:
    path = REPO_ROOT / "results" / run_name / "detailed_results.csv"
    out: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["_run"] = run_name.rsplit("_", 1)[-1]
            row["_failure_mode"] = base.classify_failure(row)
            out.append(row)
    return out


def load_query_failure_points() -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for run in ("photosynthesis_snowflake_v2", "photosynthesis_snowflake_v3"):
        base_dir = REPO_ROOT / "results" / run
        for pass_no in range(1, 6):
            path = base_dir / f"pass{pass_no}_analysis" / f"pass{pass_no}_query_failure_points.csv"
            if not path.exists():
                continue
            with path.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    case_id = row["case_id"]
                    issue_code = row["issue_code"]
                    existing = merged[case_id].setdefault(
                        issue_code,
                        {
                            "case_id": case_id,
                            "issue_code": issue_code,
                            "issue_label": row["issue_label"].rstrip("."),
                            "runs": [],
                            "attempts_with_issue": 0,
                        },
                    )
                    existing["runs"].append(run.rsplit("_", 1)[-1])
                    existing["attempts_with_issue"] += int(float(row["attempts_with_issue"]))
    out: dict[str, list[dict[str, Any]]] = {}
    for case_id, issues in merged.items():
        out[case_id] = sorted(issues.values(), key=lambda row: (-row["attempts_with_issue"], row["issue_code"]))
    return out


def summarize_case_model(rows: list[dict[str, Any]]) -> dict[str, Any]:
    modes = Counter(row["_failure_mode"] for row in rows)
    exact_attempts = sum(as_bool(row["exact_match"]) for row in rows)
    return {
        "attempts": len(rows),
        "exact_attempts": exact_attempts,
        "mean_score": avg([base.as_float(row["score"]) for row in rows]),
        "mean_row_set_correctness": avg([base.as_float(row["row_set_correctness_score"]) for row in rows]),
        "mean_numeric_correctness": avg([base.as_float(row["numeric_correctness_score"]) for row in rows]),
        "mean_sort_correctness": avg([base.as_float(row["sort_order_correctness_score"]) for row in rows]),
        "dominant_failure_mode": modes.most_common(1)[0][0] if modes else "",
        "dominant_non_exact_failure_mode": base.dominant_non_exact_mode(modes) if modes else "none",
        "failure_modes": dict(modes),
        "v2_exact_attempts": sum(as_bool(row["exact_match"]) for row in rows if row["_run"] == "v2"),
        "v3_exact_attempts": sum(as_bool(row["exact_match"]) for row in rows if row["_run"] == "v3"),
    }


def summarize_model(rows: list[dict[str, Any]]) -> dict[str, Any]:
    modes = Counter(row["_failure_mode"] for row in rows)
    return {
        "model_family": model_family_from_rows(rows),
        "attempts": len(rows),
        "exact_attempts": sum(as_bool(row["exact_match"]) for row in rows),
        "mean_score": avg([base.as_float(row["score"]) for row in rows]),
        "mean_row_set_correctness": avg([base.as_float(row["row_set_correctness_score"]) for row in rows]),
        "mean_numeric_correctness": avg([base.as_float(row["numeric_correctness_score"]) for row in rows]),
        "mean_sort_correctness": avg([base.as_float(row["sort_order_correctness_score"]) for row in rows]),
        "dominant_non_exact_failure_mode": base.dominant_non_exact_mode(modes) if modes else "none",
    }


def weak_component_lines(stats: dict[str, Any]) -> list[str]:
    lines = []
    if stats["mean_row_set_correctness"] < 0.75:
        lines.append(COMPONENT_GUIDANCE["row_set"])
    if stats["mean_numeric_correctness"] < 0.75:
        lines.append(COMPONENT_GUIDANCE["numeric"])
    if stats["mean_sort_correctness"] < 0.80:
        lines.append(COMPONENT_GUIDANCE["sort"])
    return lines


def safe_issue_category(issue: dict[str, Any]) -> str:
    """Convert detailed failure labels into a non-answer-leaking category."""
    text = f"{issue.get('issue_code', '')} {issue.get('issue_label', '')}".lower()
    if any(token in text for token in ("sort", "order")):
        return "sort"
    if any(token in text for token in ("avg", "mean", "vaf", "qual", "quality", "alt", "total", "count", "z-score", "score", "burden")):
        return "numeric"
    if any(token in text for token in ("group", "bucket", "ranking", "gene set", "condition-impact", "condition-pathway", "tissue-gene")):
        return "grouping"
    if any(token in text for token in ("status", "reason", "repair", "classified", "class", "label")):
        return "classification"
    if any(token in text for token in ("null", "coalesce", "type", "serialized", "key")):
        return "null_key_type"
    if any(token in text for token in ("mapped", "expression", "attribute", "tissue", "condition", "batch", "role")):
        return "attribute_mapping"
    if any(token in text for token in ("included", "kept", "leaked", "inflated", "counted non", "extra", "non-gold", "reference")):
        return "over_inclusion"
    if any(token in text for token in ("dropped", "missing", "missed", "undercount", "under-count", "under counted")):
        return "under_inclusion"
    return "generic"


def safe_issue_guidance(issue: dict[str, Any]) -> str:
    """Convert detailed failure labels into non-answer-leaking runtime guidance."""
    category = safe_issue_category(issue)
    return SAFE_ISSUE_GUIDANCE.get(
        category,
        "Historical query-level risk: prior attempts matched the visible task shape but violated at least one join, filter, arithmetic, or output-format constraint.",
    )


def build_addendum(
    model: str,
    case_id: str,
    stats: dict[str, Any],
    model_profile: dict[str, Any],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    exact_attempts = int(stats["exact_attempts"])
    attempts = int(stats["attempts"])
    dominant = stats["dominant_non_exact_failure_mode"]
    model_family = model_profile.get("model_family", "")
    display_model = base.canonical_model_name(model)
    source_runs = ["v2", "v3"]

    lines: list[str]
    if exact_attempts:
        lines = [
            f"Previous {display_model} attempts reached exact output on this case {exact_attempts}/{attempts} times across v2/v3. Reuse the same conservative approach: solve the requested join/filter grain first, then apply the requested final sort.",
            "Keep the response minimal and schema-locked: exactly the requested columns and valid JSON only.",
        ]
        if exact_attempts < attempts and dominant != "none":
            lines.append(f"Some earlier attempts still failed as `{dominant}`; do one final check for that risk before returning.")
    else:
        lines = [
            f"Previous {display_model} attempts had no exact match for this case across v2/v3. The dominant non-exact mode was `{dominant}`.",
            MODE_GUIDANCE.get(dominant, "Rebuild the result from the prompt and dataset rather than relying on a plausible table shape."),
        ]
        model_mode = model_profile.get("dominant_non_exact_failure_mode", "")
        if model_mode and model_mode not in {"none", dominant}:
            lines.append(f"Across all v2/v3 tasks this model often failed as `{model_mode}`; treat that as a second self-check.")
        lines.extend(weak_component_lines(stats))
        for issue in issues[:3]:
            lines.append(safe_issue_guidance(issue))
        lines.append("Do not use memorized answer rows; compute the table from the provided CSV data and prompt constraints.")

    deduped: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if line and line not in seen:
            deduped.append(line)
            seen.add(line)

    return {
        "addendum_id": f"v5::{model}::{case_id}",
        "heading": "Model-specific guidance for v5",
        "model": model,
        "display_model": display_model,
        "model_family": model_family,
        "case_id": case_id,
        "source_runs": source_runs,
        "source_exact_attempts": exact_attempts,
        "source_attempts": attempts,
        "source_mean_score": stats["mean_score"],
        "dominant_non_exact_failure_mode": dominant,
        "source_issue_categories": sorted({safe_issue_category(issue) for issue in issues[:3]}),
        "text": "\n".join(f"- {line}" for line in deduped),
    }


def update_standard_instructions() -> None:
    write_json(
        REPO_ROOT / "standard_instructions.json",
        {
            "benchmark_id": BENCHMARK_ID,
            "instructions": [
                {
                    "standard_instructions_id": SQL_STANDARD_ID,
                    "language": "sql",
                    "text": SQL_STANDARD_V2_TEXT,
                },
                {
                    "standard_instructions_id": PYTHON_STANDARD_ID,
                    "language": "python",
                    "text": PYTHON_STANDARD_V2_TEXT,
                },
            ],
        },
    )


def build_v5_cases(v2_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in v2_cases:
        row = dict(item)
        row["benchmark_id"] = BENCHMARK_ID
        row["standard_instructions_id"] = SQL_STANDARD_ID if row["language"] == "sql" else PYTHON_STANDARD_ID
        row["prompt"] = strip_existing_guidance(row["prompt"])
        rows.append(row)
    write_jsonl(REPO_ROOT / "benchmark_cases.jsonl", rows)
    return rows


def update_gold_dataset_template() -> None:
    dataset = load_json(REPO_ROOT / "shared_dataset.json")
    dataset["benchmark_id"] = BENCHMARK_ID
    write_json(REPO_ROOT / "shared_dataset.json", dataset)

    gold_rows = load_jsonl(REPO_ROOT / "gold_answers.jsonl")
    for row in gold_rows:
        row["benchmark_id"] = BENCHMARK_ID
    write_jsonl(REPO_ROOT / "gold_answers.jsonl", gold_rows)

    template_rows = load_jsonl(REPO_ROOT / "results_template.jsonl")
    for row in template_rows:
        row["benchmark_id"] = BENCHMARK_ID
        row["repeat_group_id"] = REPEAT_GROUP_ID
    write_jsonl(REPO_ROOT / "results_template.jsonl", template_rows)


def update_manifest() -> None:
    manifest = load_json(REPO_ROOT / "benchmark_manifest.json")
    manifest["benchmark_id"] = BENCHMARK_ID
    manifest["version"] = "5.0.0"
    manifest["default_repeat_group_id"] = REPEAT_GROUP_ID
    manifest["query_engineering"] = {
        "enabled": True,
        "registry_id": REGISTRY_ID,
        "registry_file": str(MODEL_GUIDANCE_FILE.relative_to(REPO_ROOT)),
        "strategy": "base_v2_v3_query_plus_model_specific_v5_addendum",
        "base_query_source": "v2/v3 benchmark_cases prompt text",
        "addendum_source": "v2 and v3 raw results plus per-pass failure-point analyses",
    }
    manifest["runner_notes"]["repeatability"] = (
        "Run each case at least three times per model to distinguish stable failures from prompt-sensitive failures. "
        "For v5, shared standards match the shorter v2/v4 wording, case prompts match the v2/v3 base query text, "
        "and model-specific guidance is appended at runtime from query_engineering_registry/v5/model_query_guidance.json."
    )
    write_json(REPO_ROOT / "benchmark_manifest.json", manifest)


def update_case_schema() -> None:
    schema = load_json(REPO_ROOT / "benchmark_case.schema.json")
    schema["properties"]["standard_instructions_id"]["enum"] = [SQL_STANDARD_ID, PYTHON_STANDARD_ID]
    schema["allOf"][0]["then"]["properties"]["standard_instructions_id"]["const"] = SQL_STANDARD_ID
    schema["allOf"][1]["then"]["properties"]["standard_instructions_id"]["const"] = PYTHON_STANDARD_ID
    write_json(REPO_ROOT / "benchmark_case.schema.json", schema)


def write_registry_run_snapshots(v2_cases: list[dict[str, Any]], v3_cases: list[dict[str, Any]], v4_cases: list[dict[str, Any]], v5_cases: list[dict[str, Any]]) -> None:
    run_cases = {"v2": v2_cases, "v3": v3_cases, "v4": v4_cases, "v5": v5_cases}
    for run, rows in run_cases.items():
        out_dir = REGISTRY_ROOT / "runs" / run
        write_jsonl(out_dir / "benchmark_cases.jsonl", rows)
        query_rows = [
            {
                "run": run,
                "benchmark_id": row["benchmark_id"],
                "case_id": row["case_id"],
                "pass": row["pass"],
                "query": row["query"],
                "language": row["language"],
                "standard_instructions_id": row["standard_instructions_id"],
                "prompt": row["prompt"],
            }
            for row in sorted(rows, key=lambda r: case_sort_key(r["case_id"]))
        ]
        write_jsonl(out_dir / "queries.jsonl", query_rows)

    for run, ref in RUN_REFS.items():
        write_json(REGISTRY_ROOT / "runs" / run / "standard_instructions.json", git_show_json(ref, "standard_instructions.json"))
    write_json(REGISTRY_ROOT / "runs" / "v5" / "standard_instructions.json", load_json(REPO_ROOT / "standard_instructions.json"))


def build_guidance_registry(v5_cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows = load_result_rows("photosynthesis_snowflake_v2") + load_result_rows("photosynthesis_snowflake_v3")
    rows_by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rows_by_model_case: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_model[row["model"]].append(row)
        rows_by_model_case[(row["model"], row["case_id"])].append(row)

    issues_by_case = load_query_failure_points()
    model_profiles = {model: summarize_model(items) for model, items in rows_by_model.items()}
    guidance_by_model: dict[str, Any] = {}
    prompt_parts_rows: list[dict[str, Any]] = []

    for model in sorted(rows_by_model, key=base.canonical_model_name):
        model_entry = {
            "display_model": base.canonical_model_name(model),
            "model_family": model_profiles[model].get("model_family", ""),
            "model_profile": model_profiles[model],
            "cases": {},
        }
        for case in sorted(v5_cases, key=lambda r: case_sort_key(r["case_id"])):
            case_id = case["case_id"]
            stats = summarize_case_model(rows_by_model_case[(model, case_id)])
            addendum = build_addendum(model, case_id, stats, model_profiles[model], issues_by_case.get(case_id, []))
            model_entry["cases"][case_id] = addendum
            prompt_parts_rows.append(
                {
                    "registry_id": REGISTRY_ID,
                    "model": model,
                    "display_model": addendum["display_model"],
                    "case_id": case_id,
                    "base_prompt_source": "v2/v3",
                    "base_prompt": case["prompt"],
                    "addendum_id": addendum["addendum_id"],
                    "addendum_text": addendum["text"],
                }
            )
        guidance_by_model[model] = model_entry

    registry = {
        "registry_id": REGISTRY_ID,
        "benchmark_id": BENCHMARK_ID,
        "created_by": "scripts/prepare_v5_queries.py",
        "strategy": "compose prompt as shared v2/v3 base query plus model-specific v5 addendum",
        "non_leakage_policy": "Runtime addenda use failure modes, component weaknesses, and sanitized failure categories; they do not include gold answer rows, expected row counts, or row identifiers.",
        "source_runs": ["photosynthesis_snowflake_v2", "photosynthesis_snowflake_v3"],
        "base_query_source": "query_engineering_registry/runs/v2/queries.jsonl and runs/v3/queries.jsonl",
        "guidance_by_model": guidance_by_model,
    }
    write_json(MODEL_GUIDANCE_FILE, registry)
    write_jsonl(V5_DIR / "prompt_parts_preview.jsonl", prompt_parts_rows)

    summary_rows = []
    for model, entry in guidance_by_model.items():
        for case_id, addendum in entry["cases"].items():
            summary_rows.append(
                {
                    "model": model,
                    "display_model": addendum["display_model"],
                    "model_family": addendum["model_family"],
                    "case_id": case_id,
                    "source_exact_attempts": addendum["source_exact_attempts"],
                    "source_attempts": addendum["source_attempts"],
                    "source_mean_score": addendum["source_mean_score"],
                    "dominant_non_exact_failure_mode": addendum["dominant_non_exact_failure_mode"],
                    "addendum_chars": len(addendum["text"]),
                }
            )
    write_csv(V5_DIR / "model_query_guidance_summary.csv", summary_rows)

    failure_rows = []
    for case_id, issues in sorted(issues_by_case.items(), key=lambda item: case_sort_key(item[0])):
        for issue in issues:
            failure_rows.append(issue)
    write_csv(V5_DIR / "source_failure_points_by_case.csv", failure_rows)
    return registry


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_standard_note() -> None:
    out_dir = REPO_ROOT / "results" / "photosynthesis_snowflake_v5"
    out_dir.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "# STANDARD5",
            "",
            f"Benchmark ID: `{BENCHMARK_ID}`",
            "",
            "Shared standard instructions intentionally match the v2/v4 wording.",
            "Case prompts intentionally match the v2/v3 base query wording.",
            "Model-specific query engineering is appended at runtime from `query_engineering_registry/v5/model_query_guidance.json`.",
            "",
            f"## `{SQL_STANDARD_ID}`",
            "",
            "```text",
            SQL_STANDARD_V2_TEXT,
            "```",
            "",
            f"## `{PYTHON_STANDARD_ID}`",
            "",
            "```text",
            PYTHON_STANDARD_V2_TEXT,
            "```",
            "",
        ]
    )
    (out_dir / "STANDARD5.md").write_text(text, encoding="utf-8")


def update_queries_markdown(cases: list[dict[str, Any]]) -> None:
    lines = [
        "# AIBioBench Queries",
        "",
        "Source: `benchmark_cases.jsonl`",
        "",
        f"Benchmark: `{BENCHMARK_ID}`",
        "",
        "Prompt strategy: v5 uses the v2/v3 base query text in this file plus model-specific runtime addenda from `query_engineering_registry/v5/model_query_guidance.json`.",
        "",
        f"Total queries: {len(cases)}",
        "",
    ]
    current_pass = None
    for case in sorted(cases, key=lambda row: case_sort_key(row["case_id"])):
        if case["pass"] != current_pass:
            current_pass = case["pass"]
            lines.extend([f"## Pass {current_pass}", ""])
        lines.extend(
            [
                f"### Query {case['query']}: `{case['case_id']}`",
                "",
                f"- Difficulty: `{case['difficulty']}`",
                f"- Language: `{case['language']}`",
                f"- Primary failure family: `{case['metadata']['failure_family_primary']}`",
                "",
                "```text",
                case["prompt"],
                "```",
                "",
            ]
        )
    (REPO_ROOT / "QUERIES.md").write_text("\n".join(lines), encoding="utf-8")


def update_docs_and_publisher() -> None:
    readme_path = REPO_ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = readme.replace("photosynthesis_snowflake_v4", "photosynthesis_snowflake_v5")
    readme = readme.replace("v4 results", "v5 results")
    readme = readme.replace("v4 bundle", "v5 bundle")
    readme = readme.replace("v4 benchmark", "v5 benchmark")
    readme = readme.replace("v4 workflow", "v5 workflow")
    readme = readme.replace("current v4", "current v5")
    readme = readme.replace("prepared v4", "prepared v5")
    readme = readme.replace("full v4", "full v5")
    readme = readme.replace(
        "`QUERIES.md` documents the full v4 prompt set with task-specific guardrails derived from v3 failure analyses",
        "`QUERIES.md` documents the v5 shared base query text; `query_engineering_registry/` stores run-by-run query snapshots and model-specific v5 addenda",
    )
    if "query_engineering_registry/" not in readme:
        readme += "\n- `query_engineering_registry/` stores run-by-run query snapshots and model-specific v5 addenda.\n"
    readme_path.write_text(readme, encoding="utf-8")

    publisher_path = REPO_ROOT / "aibiobench-results.py"
    publisher = publisher_path.read_text(encoding="utf-8")
    publisher = publisher.replace("photosynthesis_snowflake_v4", "photosynthesis_snowflake_v5")
    publisher = publisher.replace("AIBioBench v4", "AIBioBench v5")
    publisher = publisher.replace("v4 results", "v5 results")
    publisher = publisher.replace("v4 bundle", "v5 bundle")
    publisher = publisher.replace("local v4", "local v5")
    publisher = publisher.replace("full v4", "full v5")
    publisher_path.write_text(publisher, encoding="utf-8")


def write_registry_readme(registry: dict[str, Any]) -> None:
    lines = [
        "# Query Engineering Registry",
        "",
        "This registry records query prompt evolution and v5 runtime prompt composition.",
        "",
        "## Runs",
        "",
        "- `runs/v2/`: v2 case/query snapshot from git history.",
        "- `runs/v3/`: v3 case/query snapshot from git history.",
        "- `runs/v4/`: v4 case/query snapshot with task-specific prompt guidance.",
        "- `runs/v5/`: v5 shared base query snapshot; prompts match v2/v3 base query wording.",
        "",
        "## v5 Runtime Addenda",
        "",
        "- `v5/model_query_guidance.json`: model-specific addenda keyed by model and case.",
        "- `v5/prompt_parts_preview.jsonl`: base query and addendum parts without dataset tables.",
        "- `v5/model_query_guidance_summary.csv`: compact audit table.",
        "- `v5/source_failure_points_by_case.csv`: combined v2/v3 failure-point source table.",
        "",
        "The runner appends the addendum after the base task text only when the manifest enables `query_engineering`.",
        "Addenda are derived from v2/v3 failures and avoid embedding complete gold answer rows, expected row counts, or row identifiers.",
        "The source failure-point CSV keeps detailed audit labels; those labels are sanitized before becoming runtime guidance.",
        "",
        f"Current registry id: `{registry['registry_id']}`",
        "",
    ]
    (REGISTRY_ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    v2_cases = git_show_jsonl(RUN_REFS["v2"], "benchmark_cases.jsonl")
    v3_cases = git_show_jsonl(RUN_REFS["v3"], "benchmark_cases.jsonl")
    v4_cases = git_show_jsonl(RUN_REFS["v4"], "benchmark_cases.jsonl")

    update_standard_instructions()
    v5_cases = build_v5_cases(v2_cases)
    update_gold_dataset_template()
    update_manifest()
    update_case_schema()
    write_registry_run_snapshots(v2_cases, v3_cases, v4_cases, v5_cases)
    registry = build_guidance_registry(v5_cases)
    write_registry_readme(registry)
    write_standard_note()
    update_queries_markdown(v5_cases)
    update_docs_and_publisher()

    base_mismatches = [
        case["case_id"]
        for case in v5_cases
        if case["prompt"] != next(row["prompt"] for row in v2_cases if row["case_id"] == case["case_id"])
    ]
    if base_mismatches:
        raise SystemExit(f"v5 base prompts differ from v2/v3 for: {base_mismatches[:10]}")
    guidance_count = sum(len(model_entry["cases"]) for model_entry in registry["guidance_by_model"].values())
    print(f"Prepared {len(v5_cases)} v5 base queries and {guidance_count} model-specific guidance addenda.")


if __name__ == "__main__":
    main()
