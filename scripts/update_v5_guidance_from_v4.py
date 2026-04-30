#!/usr/bin/env python3
"""Append v4-derived model/case guidance to the v5 query registry.

The active v5 benchmark keeps base case prompts unchanged and appends
model-specific query-engineering addenda at runtime.  This script updates those
addenda with run-v4 evidence while preserving the existing v2/v3 guidance unless
the old wording would now conflict with the v4 result pattern.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pass4_analysis as base
import prepare_v5_queries as prep


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ID = prep.REGISTRY_ID
V5_DIR = REPO_ROOT / "query_engineering_registry" / "v5"
GUIDANCE_FILE = V5_DIR / "model_query_guidance.json"
PREVIEW_FILE = V5_DIR / "prompt_parts_preview.jsonl"
SUMMARY_FILE = V5_DIR / "model_query_guidance_summary.csv"
FAILURE_POINTS_FILE = V5_DIR / "source_failure_points_by_case.csv"
V5_QUERIES_FILE = REPO_ROOT / "query_engineering_registry" / "runs" / "v5" / "queries.jsonl"
V4_RESULTS_DIR = REPO_ROOT / "results" / "photosynthesis_snowflake_v4"
SOURCE_RUNS = ("photosynthesis_snowflake_v2", "photosynthesis_snowflake_v3", "photosynthesis_snowflake_v4")
SOURCE_RUN_LABELS = ("v2", "v3", "v4")


GENERAL_BEST_PRACTICES = [
    "v5 best-practice checklist: determine the preserving row grain first, then apply joins and filters, then compute values, then perform the final requested sort.",
    "Keep output schema locked: exactly the requested column names in exactly the requested order, valid JSON only, and no helper columns or prose.",
    "Use JSON null for missing values; keep numeric outputs numeric and booleans as true/false.",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n", encoding="utf-8")


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


def load_result_rows(run_name: str) -> list[dict[str, Any]]:
    path = REPO_ROOT / "results" / run_name / "detailed_results.csv"
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["_run"] = run_name.rsplit("_", 1)[-1]
            row["_failure_mode"] = base.classify_failure(row)
            rows.append(row)
    return rows


def load_query_failure_points(run_names: tuple[str, ...]) -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for run_name in run_names:
        run_label = run_name.rsplit("_", 1)[-1]
        base_dir = REPO_ROOT / "results" / run_name
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
                            "runs": set(),
                            "attempts_with_issue": 0,
                            "v2_attempts_with_issue": 0,
                            "v3_attempts_with_issue": 0,
                            "v4_attempts_with_issue": 0,
                        },
                    )
                    count = int(float(row["attempts_with_issue"]))
                    existing["runs"].add(run_label)
                    existing["attempts_with_issue"] += count
                    existing[f"{run_label}_attempts_with_issue"] += count
    out: dict[str, list[dict[str, Any]]] = {}
    for case_id, issues in merged.items():
        case_rows = []
        for issue in issues.values():
            row = dict(issue)
            row["runs"] = ",".join(sorted(row["runs"]))
            row["source_category"] = prep.safe_issue_category(row)
            case_rows.append(row)
        out[case_id] = sorted(case_rows, key=lambda row: (-int(row["v4_attempts_with_issue"]), -int(row["attempts_with_issue"]), row["issue_code"]))
    return out


def load_v5_queries() -> dict[str, dict[str, Any]]:
    return {row["case_id"]: row for row in load_jsonl(V5_QUERIES_FILE)}


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    modes = Counter(row["_failure_mode"] for row in rows)
    exact_attempts = sum(as_bool(row.get("exact_match")) for row in rows)
    return {
        "attempts": len(rows),
        "exact_attempts": exact_attempts,
        "mean_score": avg([base.as_float(row.get("score")) for row in rows]),
        "mean_row_set_correctness": avg([base.as_float(row.get("row_set_correctness_score")) for row in rows]),
        "mean_numeric_correctness": avg([base.as_float(row.get("numeric_correctness_score")) for row in rows]),
        "mean_sort_correctness": avg([base.as_float(row.get("sort_order_correctness_score")) for row in rows]),
        "dominant_failure_mode": modes.most_common(1)[0][0] if modes else "",
        "dominant_non_exact_failure_mode": base.dominant_non_exact_mode(modes) if modes else "none",
        "failure_modes": dict(modes),
    }


def weak_component_lines(stats: dict[str, Any]) -> list[str]:
    lines = []
    if stats["mean_row_set_correctness"] < 0.99:
        lines.append(prep.COMPONENT_GUIDANCE["row_set"])
    if stats["mean_numeric_correctness"] < 0.99:
        lines.append(prep.COMPONENT_GUIDANCE["numeric"])
    if stats["mean_sort_correctness"] < 0.99:
        lines.append(prep.COMPONENT_GUIDANCE["sort"])
    return lines


def weakest_component_line(stats: dict[str, Any], display_model: str) -> str | None:
    components = [
        ("row-set", stats["mean_row_set_correctness"], prep.COMPONENT_GUIDANCE["row_set"]),
        ("numeric", stats["mean_numeric_correctness"], prep.COMPONENT_GUIDANCE["numeric"]),
        ("sort", stats["mean_sort_correctness"], prep.COMPONENT_GUIDANCE["sort"]),
    ]
    name, value, guidance = min(components, key=lambda item: item[1])
    if value >= 0.90:
        return None
    return f"Across all v4 tasks, {display_model}'s weakest scoring component was {name} ({value:.3f}); use this self-check here: {guidance}"


def prompt_derived_lines(case: dict[str, Any]) -> list[str]:
    prompt = case["prompt"].lower()
    lines: list[str] = []
    if "full outer join" in prompt:
        lines.append("Prompt-derived guardrail: FULL OUTER JOIN means preserve unmatched rows from both sides and use the requested coalesced key rather than silently converting to an inner or left join.")
    elif "left join" in prompt or "preserving table" in prompt or "include samples with zero" in prompt or "include genes with zero" in prompt:
        lines.append("Prompt-derived guardrail: preserve the stated left/preserving table even when downstream joins or calculations have no match.")
    elif "inner join" in prompt or "complete-chain" in prompt or "complete chain" in prompt:
        lines.append("Prompt-derived guardrail: inner/complete-chain wording means remove rows missing any required join before grouping or calculating values.")
    if "group by" in prompt or "for each" in prompt or "one row per" in prompt:
        lines.append("Prompt-derived guardrail: set the grouping grain before calculations; do not mix call-level, sample-level, gene-level, and tissue-level denominators.")
    if "round" in prompt:
        lines.append("Prompt-derived guardrail: keep intermediate arithmetic unrounded and round only the final requested output values.")
    if "sort by" in prompt:
        lines.append("Prompt-derived guardrail: make the requested sort order the final operation, including every tie-breaker in the prompt.")
    return lines


def parse_existing_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        lines.append(line)
    return lines


def filter_controversial_existing(lines: list[str], v4_stats: dict[str, Any]) -> list[str]:
    if int(v4_stats["exact_attempts"]) > 0:
        return lines
    filtered = []
    for line in lines:
        lower = line.lower()
        if "reached exact output" in lower and "reuse the same conservative approach" in lower:
            continue
        filtered.append(line)
    return filtered


def v4_case_update_lines(
    model: str,
    case_id: str,
    v4_stats: dict[str, Any],
    v4_model_profile: dict[str, Any],
    issues: list[dict[str, Any]],
    case: dict[str, Any],
) -> list[str]:
    display = base.canonical_model_name(model)
    attempts = int(v4_stats["attempts"])
    exact = int(v4_stats["exact_attempts"])
    dominant = v4_stats["dominant_non_exact_failure_mode"]
    lines: list[str] = []

    if exact == attempts:
        lines.append(f"v4 update: {display} solved this case exactly {exact}/{attempts} times. Keep the v4 approach concise: follow the base query literally, verify the schema, and do the final sort.")
    elif exact > 0:
        lines.append(f"v4 update: {display} was prompt-sensitive on this case ({exact}/{attempts} exact, mean score {v4_stats['mean_score']:.3f}); keep the successful row grain but explicitly check the remaining failure mode `{dominant}` before returning.")
        lines.append(prep.MODE_GUIDANCE.get(dominant, "Rebuild the result from the prompt and dataset rather than relying on a plausible table shape."))
    else:
        lines.append(f"v4 update: {display} still had no exact match on this case (0/{attempts}, mean score {v4_stats['mean_score']:.3f}); treat this as a high-risk query and do not return until the join/filter grain, values, and sort have all been independently checked.")
        lines.append(prep.MODE_GUIDANCE.get(dominant, "Rebuild the result from the prompt and dataset rather than relying on a plausible table shape."))

    model_mode = v4_model_profile.get("dominant_non_exact_failure_mode", "")
    if model_mode and model_mode not in {"none", dominant}:
        lines.append(f"Across all v4 tasks this model often failed as `{model_mode}`; use that as a model-specific second self-check.")
    component_line = weakest_component_line(v4_model_profile, display)
    if component_line:
        lines.append(component_line)

    if exact < attempts:
        lines.extend(weak_component_lines(v4_stats))
        for issue in issues[:4]:
            if int(issue.get("v4_attempts_with_issue", 0)) > 0:
                lines.append(prep.safe_issue_guidance(issue))
    else:
        for issue in issues[:2]:
            if int(issue.get("v4_attempts_with_issue", 0)) > 0:
                lines.append(prep.safe_issue_guidance(issue))

    lines.extend(prompt_derived_lines(case))
    lines.extend(GENERAL_BEST_PRACTICES)
    return lines


def dedupe(lines: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if not line or line in seen:
            continue
        out.append(line)
        seen.add(line)
    return out


def update_manifest() -> None:
    path = REPO_ROOT / "benchmark_manifest.json"
    manifest = load_json(path)
    qe = manifest.setdefault("query_engineering", {})
    qe["addendum_source"] = "v2, v3, and v4 raw results plus per-pass failure-point analyses"
    qe["strategy"] = "base_v2_v3_query_plus_model_specific_v5_addendum_with_v4_updates"
    write_json(path, manifest)


def active_models() -> list[str]:
    manifest = load_json(REPO_ROOT / "benchmark_manifest.json")
    models = manifest.get("default_models", [])
    return [str(model) for model in models]


def update_registry_readme() -> None:
    path = REPO_ROOT / "query_engineering_registry" / "README.md"
    text = "\n".join(
        [
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
            "- `v5/source_failure_points_by_case.csv`: combined v2/v3/v4 failure-point source table.",
            "",
            "The runner appends the addendum after the base task text only when the manifest enables `query_engineering`.",
            "Addenda are derived from v2/v3/v4 failures and avoid embedding complete gold answer rows, expected row counts, or row identifiers.",
            "The source failure-point CSV keeps detailed audit labels; those labels are sanitized before becoming runtime guidance.",
            "",
            f"Current registry id: `{REGISTRY_ID}`",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    registry = load_json(GUIDANCE_FILE)
    v5_cases = load_v5_queries()
    all_source_rows = []
    for run_name in SOURCE_RUNS:
        all_source_rows.extend(load_result_rows(run_name))
    v4_rows = [row for row in all_source_rows if row["_run"] == "v4"]

    rows_by_model_v4: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rows_by_model_case_v4: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    rows_by_model_case_all: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in all_source_rows:
        rows_by_model_case_all[(row["model"], row["case_id"])].append(row)
        if row["_run"] == "v4":
            rows_by_model_v4[row["model"]].append(row)
            rows_by_model_case_v4[(row["model"], row["case_id"])].append(row)

    issues_by_case = load_query_failure_points(SOURCE_RUNS)
    v4_model_profiles = {model: summarize_rows(rows) for model, rows in rows_by_model_v4.items()}
    prompt_parts_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    selected_models = active_models()
    guidance_by_model = {
        model: registry["guidance_by_model"][model]
        for model in selected_models
        if model in registry["guidance_by_model"]
    }
    registry["guidance_by_model"] = guidance_by_model
    for model in sorted(guidance_by_model, key=base.canonical_model_name):
        model_entry = guidance_by_model[model]
        model_entry["model_profile_v4"] = v4_model_profiles.get(model, {})
        for case_id in sorted(model_entry["cases"], key=prep.case_sort_key):
            addendum = model_entry["cases"][case_id]
            case = v5_cases[case_id]
            v4_stats = summarize_rows(rows_by_model_case_v4[(model, case_id)])
            all_stats = summarize_rows(rows_by_model_case_all[(model, case_id)])
            existing_lines = parse_existing_lines(addendum["text"])
            existing_lines = filter_controversial_existing(existing_lines, v4_stats)
            update_lines = v4_case_update_lines(
                model=model,
                case_id=case_id,
                v4_stats=v4_stats,
                v4_model_profile=v4_model_profiles.get(model, {}),
                issues=issues_by_case.get(case_id, []),
                case=case,
            )
            combined_lines = dedupe(existing_lines + update_lines)

            addendum["heading"] = "Model-specific guidance for v5"
            addendum["source_runs"] = list(SOURCE_RUN_LABELS)
            addendum["source_exact_attempts"] = all_stats["exact_attempts"]
            addendum["source_attempts"] = all_stats["attempts"]
            addendum["source_mean_score"] = all_stats["mean_score"]
            addendum["dominant_non_exact_failure_mode"] = all_stats["dominant_non_exact_failure_mode"]
            addendum["source_issue_categories"] = sorted({prep.safe_issue_category(issue) for issue in issues_by_case.get(case_id, [])[:4]})
            addendum["v4_exact_attempts"] = v4_stats["exact_attempts"]
            addendum["v4_attempts"] = v4_stats["attempts"]
            addendum["v4_mean_score"] = v4_stats["mean_score"]
            addendum["v4_mean_row_set_correctness"] = v4_stats["mean_row_set_correctness"]
            addendum["v4_mean_numeric_correctness"] = v4_stats["mean_numeric_correctness"]
            addendum["v4_mean_sort_correctness"] = v4_stats["mean_sort_correctness"]
            addendum["v4_dominant_non_exact_failure_mode"] = v4_stats["dominant_non_exact_failure_mode"]
            addendum["text"] = "\n".join(f"- {line}" for line in combined_lines)

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
            summary_rows.append(
                {
                    "model": model,
                    "display_model": addendum["display_model"],
                    "model_family": addendum.get("model_family", ""),
                    "case_id": case_id,
                    "source_runs": ",".join(SOURCE_RUN_LABELS),
                    "source_exact_attempts": addendum["source_exact_attempts"],
                    "source_attempts": addendum["source_attempts"],
                    "source_mean_score": addendum["source_mean_score"],
                    "dominant_non_exact_failure_mode": addendum["dominant_non_exact_failure_mode"],
                    "v4_exact_attempts": addendum["v4_exact_attempts"],
                    "v4_attempts": addendum["v4_attempts"],
                    "v4_mean_score": addendum["v4_mean_score"],
                    "v4_mean_row_set_correctness": addendum["v4_mean_row_set_correctness"],
                    "v4_mean_numeric_correctness": addendum["v4_mean_numeric_correctness"],
                    "v4_mean_sort_correctness": addendum["v4_mean_sort_correctness"],
                    "v4_dominant_non_exact_failure_mode": addendum["v4_dominant_non_exact_failure_mode"],
                    "addendum_chars": len(addendum["text"]),
                }
            )

    registry["created_by"] = "scripts/update_v5_guidance_from_v4.py"
    registry["strategy"] = "compose prompt as shared v2/v3 base query plus model-specific v5 addendum updated with v4 evidence"
    registry["non_leakage_policy"] = "Runtime addenda use failure modes, component weaknesses, prompt-derived guardrails, and sanitized failure categories; they do not include gold answer rows, expected row counts, or row identifiers."
    registry["source_runs"] = list(SOURCE_RUNS)
    registry["active_models"] = selected_models
    registry["v4_update_policy"] = "Preserve existing v2/v3 guidance, remove only exact-success reuse wording when v4 had zero exact attempts, then append v4 model/case evidence and best-practice checks."

    write_json(GUIDANCE_FILE, registry)
    write_jsonl(PREVIEW_FILE, prompt_parts_rows)
    write_csv(SUMMARY_FILE, summary_rows)

    failure_rows = []
    for case_id, issues in sorted(issues_by_case.items(), key=lambda item: prep.case_sort_key(item[0])):
        failure_rows.extend(issues)
    write_csv(FAILURE_POINTS_FILE, failure_rows)
    update_manifest()
    update_registry_readme()

    guidance_count = sum(len(entry["cases"]) for entry in guidance_by_model.values())
    print(f"Updated {guidance_count} v5 model-specific addenda with v4 failure evidence.")


if __name__ == "__main__":
    main()
