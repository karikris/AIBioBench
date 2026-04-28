#!/usr/bin/env python3
"""Prepare the photosynthesis snowflake benchmark for the v4 prompt pass.

The v4 strategy intentionally moves most of the extra guardrails out of the
shared standard instructions and into case-specific prompts.  The shared
instructions are restored to the shorter v2 shape, while each query receives
warnings derived from the v3 query failure-point analyses.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ID = "AIBioBench_photosynthesis_snowflake_v4"
SQL_STANDARD_ID = "sql_v4"
PYTHON_STANDARD_ID = "python_v4"
REPEAT_GROUP_ID = "default_repeatability_v4"
GUIDANCE_MARKER = "Task-specific guidance for v4:"

SCHEMA_TREE = "fact_calls\n\u251c\u2500\u2500 sample_dim\n\u2514\u2500\u2500 variant_dim\n    \u2514\u2500\u2500 gene_dim"

SQL_STANDARD_V2_TEXT = f"""You are given four CSV tables in a snowflake schema:

{SCHEMA_TREE}

Rules:
1. Use ANSI SQL.
2. Show the SQL first, then show the final result table.
3. Use NULL for missing values.
4. Preserve the exact requested sort order.
5. Round derived decimal values to 3 decimals.
6. If your SQL dialect does not support RIGHT JOIN, use an equivalent reversed LEFT JOIN.
7. If your SQL dialect does not support FULL OUTER JOIN, emulate it correctly.
8. Do not invent rows or columns.
9. Unless explicitly stated otherwise, summaries that follow a join should be computed over the joined rows, not over distinct source rows.
10. Zero-count rows requested by a preserving join are mandatory.
11. This benchmark scores row-set correctness, numeric correctness, and sort-order correctness separately, so preserve all requested rows and ordering."""

PYTHON_STANDARD_V2_TEXT = f"""You are given four CSV tables in a snowflake schema:

{SCHEMA_TREE}

Rules:
1. Use Python with pandas and numpy only.
2. Show the Python code first, then show the final result table.
3. Use NaN/None in code, but present missing values as NULL in the final table.
4. Preserve the exact requested sort order.
5. Round derived decimal values to 3 decimals.
6. Use numpy.log2(x + 1) for all requested log transforms.
7. When a task requests matched expression by gene_symbol, use this mapping:
   - NDHB -> expr_ndhb
   - NDHK -> expr_ndhk
   - PGR5 -> expr_pgr5
   - all other genes -> NULL
8. When a task requests standard deviation or coefficient of variation, use population standard deviation with ddof=0 unless the prompt says otherwise.
9. Do not invent rows or columns.
10. This benchmark scores row-set correctness, numeric correctness, and sort-order correctness separately, so preserve all requested rows and ordering."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    payload = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n"
    path.write_text(payload, encoding="utf-8")


def case_sort_key(case_id: str) -> tuple[int, int]:
    pass_text, query_text = case_id.replace("pass", "").split(".query")
    return int(pass_text), int(query_text)


def load_failure_points() -> dict[str, list[dict[str, str]]]:
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    base = REPO_ROOT / "results" / "photosynthesis_snowflake_v3"
    for pass_no in range(1, 6):
        path = base / f"pass{pass_no}_analysis" / f"pass{pass_no}_query_failure_points.csv"
        if not path.exists():
            raise SystemExit(f"Missing failure analysis file: {path}")
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                by_case[row["case_id"]].append(row)
    for rows in by_case.values():
        rows.sort(key=lambda row: int(row["attempts_with_issue"]), reverse=True)
    return by_case


def load_gold_contracts() -> dict[str, dict[str, Any]]:
    return {row["case_id"]: row for row in load_jsonl(REPO_ROOT / "gold_answers.jsonl")}


def strip_existing_guidance(prompt: str) -> str:
    marker_index = prompt.find(f"\n\n{GUIDANCE_MARKER}")
    if marker_index == -1:
        return prompt.strip()
    return prompt[:marker_index].strip()


def output_contract_lines(case: dict[str, Any], gold: dict[str, Any]) -> list[str]:
    scoring = case["scoring"]
    columns = ", ".join(gold["columns"])
    row_count = len(gold["rows"])
    sort_keys = ", ".join(scoring.get("sort_key_columns") or [])
    row_keys = ", ".join(scoring.get("row_identity_columns") or [])
    numeric_columns = ", ".join(scoring.get("numeric_columns") or [])

    lines = [
        f"Expected output contract: return exactly {row_count} data rows and exactly these columns in this order: {columns}.",
        "Do not add explanatory columns, helper columns, row numbers, confidence labels, or alternative summaries to the final table.",
    ]
    if row_keys:
        lines.append(f"Row identity is scored by {row_keys}; do not duplicate, omit, or relabel those keys.")
    if numeric_columns:
        lines.append(f"Numeric columns checked for tolerance are: {numeric_columns}; compute them from the correct joined/filter row set before rounding.")
    if sort_keys:
        lines.append(f"Sort-order scoring uses {sort_keys}; follow the prompt's sort direction and tie-breakers exactly.")
    return lines


def row_boundary_lines(case: dict[str, Any]) -> list[str]:
    prompt = strip_existing_guidance(case["prompt"])
    lower = prompt.lower()
    lines: list[str] = []

    if "sample_dim only" in lower:
        lines.append("Use sample_dim only: return the five real sample_dim rows S1-S5 exactly once; do not join to fact_calls or introduce S999.")
    if "sample_dim as the preserving table" in lower or "for each sample in sample_dim" in lower or "start from sample_dim" in lower:
        lines.append("sample_dim is the preserving table: include S1-S5, keep zero-count samples such as S5, and never include orphan fact key S999 as a sample row.")
    if "one row per sample" in lower or "include samples with zero" in lower or "include samples with zero calls" in lower or "include samples with zero burden" in lower:
        lines.append("For sample-preserving output, produce one row per sample_dim sample; zero-call or zero-burden samples still need count 0 and NULL/rounded derived values as requested.")
    if "gene_dim and left join" in lower or "start from gene_dim" in lower or "one row per gene" in lower:
        lines.append("gene_dim is the preserving gene table: include real genes from gene_dim, including genes with zero observed calls, but do not invent an output gene for orphan variant gene_id G999.")
    if "left join fact_calls" in lower or "keep all fact rows" in lower or "all fact rows" in lower:
        lines.append("Fact-preserving logic must keep every fact_calls row unless the prompt later applies an explicit filter; preserve fact-side keys such as V999/S999 and put NULLs only in missing dimension attributes.")
    if "full outer join" in lower:
        lines.append("FULL OUTER JOIN must include matched rows, fact-only V999, and variant-only V6; use a coalesced variant_id key and do not drop either side-only row.")

    complete_chain_terms = (
        "complete-chain",
        "complete chain",
        "complete inner joins",
        "inner join across all four tables",
        "across the full snowflake",
    )
    if any(term in lower for term in complete_chain_terms):
        lines.append("A complete-chain row requires sample_dim, variant_dim, and gene_dim all to match; call_id 6 lacks a gene_dim match, call_id 8 lacks a sample_dim match, and call_id 9 lacks a variant_dim match.")
    if "inner join fact_calls to sample_dim" in lower and "variant_dim" not in lower:
        lines.append("For the sample inner join only, call_id 8/S999 must be removed, but call_id 9/S2 must remain because S2 exists in sample_dim.")
    if "inner join fact_calls to variant_dim" in lower and "gene_dim" not in lower:
        lines.append("For the variant inner join only, call_id 9/V999 must be removed, but call_id 6/V5 remains because V5 exists in variant_dim.")
    if "variant_dim, then to gene_dim" in lower or "variant_dim and gene_dim" in lower:
        if "sample_dim" not in lower and "all four" not in lower and "complete-chain" not in lower:
            lines.append("For a fact -> variant -> gene chain without sample_dim, drop V5/G999 and V999, but do not drop call_id 8 solely because S999 is not in sample_dim.")

    if "genotype <> '0/0'" in prompt:
        lines.append("Apply the non-reference filter exactly as genotype <> '0/0'; do not count 0/0 reference calls in non-reference summaries.")
    if "impact = 'high'" in prompt:
        lines.append("Apply the high-impact filter only to rows whose joined variant_dim impact is exactly 'high'.")
    if "impact in ('high', 'moderate')" in lower:
        lines.append("For high/moderate burden filters, include only joined variants with impact exactly 'high' or 'moderate'; exclude low, modifier, missing, and unmatched variants.")
    return lines


def calculation_lines(case: dict[str, Any]) -> list[str]:
    prompt = strip_existing_guidance(case["prompt"])
    lower = prompt.lower()
    prompt_without_table_names = lower.replace("fact_calls", "")
    lines: list[str] = []

    has_count_request = any(
        term in lower
        for term in (
            "call_count",
            "total_calls",
            "n_calls",
            "non_reference_calls",
            "complete_chain_calls",
            "incomplete_chain_calls",
            "missing_sample_calls",
            "missing_variant_calls",
            "missing_gene_calls",
            "count calls",
            "count high-impact",
            "count genotype",
            "count matched",
            "count of distinct",
        )
    ) or bool(re.search(r"\bcount\b|\bcalls\b", prompt_without_table_names))
    if has_count_request:
        lines.append("Count fact-call rows at the post-join/post-filter grain unless the prompt explicitly says distinct; do not substitute sample counts, variant counts, or plausible biological categories.")
    if "average qual" in lower or "avg_qual" in lower or "mean_qual" in lower or "max_qual" in lower or "min_qual" in lower:
        lines.append("Quality statistics must use qual values from the correctly joined/filter-preserved fact rows; compute min/max/mean after the row boundary is correct.")
    if "vaf" in lower:
        lines.append("Compute VAF per fact row as alt_reads / total_reads, then average those row-level VAF values when a mean/average VAF is requested; do not use a ratio of summed reads unless explicitly requested.")
    if "alt_reads" in lower:
        lines.append("Use alt_reads from the filtered fact rows; include zero alt_reads when the row satisfies the filter, especially for high-impact/reference boundary cases.")
    if "distinct" in lower:
        lines.append("For distinct counts, count distinct values only after the required joins and filters have been applied.")
    if "matched expression" in lower or "matched_expr" in lower or "matched expression mapping" in lower:
        lines.append("Matched expression must use gene_symbol mapping NDHB -> expr_ndhb, NDHK -> expr_ndhk, PGR5 -> expr_pgr5, and NULL for all other genes; do not average the wrong marker column.")
    if "expr_ndhb" in lower or "expr_pgr5" in lower or "expr_ndhk" in lower:
        lines.append("Expression summaries must use the marker column named in the prompt and the correct grain: sample-only tasks average samples, joined tasks average the joined sample-call rows.")
    if "log2" in lower:
        lines.append("Use numpy.log2(x + 1) or SQL-equivalent log2(x + 1) exactly; apply +1 before the log transform and round only the final displayed value.")
    if "population" in lower or "ddof=0" in lower or "pop_std" in lower or "z-score" in lower or "cv_" in lower:
        lines.append("Use population statistics with ddof=0 for standard deviation, z-scores, and coefficient of variation; sample standard deviation will score wrong.")
    if "ratio" in lower or "share" in lower or "imbalance" in lower:
        lines.append("For ratios/shares, use the exact denominator in the prompt for each row; calculate all component shares first, then derive imbalance or ratios from those components.")
    if "decision_score" in lower or "burden_score" in lower or "pressure" in lower or "weighted_signal" in lower:
        lines.append("Compute composite decision/burden/pressure scores from the already-correct intermediate metrics; do not recompute them from rounded display values unless the prompt explicitly says so.")
    if "round" in lower or case["scoring"].get("numeric_columns"):
        lines.append("Round derived decimal outputs to 3 decimals in the final table only; keep intermediate calculations unrounded.")
    return lines


def failure_warning_lines(failures: list[dict[str, str]]) -> list[str]:
    lines: list[str] = []
    for row in failures[:5]:
        pct = round(float(row["attempt_pct"]) * 100)
        label = row["issue_label"].rstrip(".")
        code = row["issue_code"]
        lines.append(f"Previous v3 failure warning ({code}, {pct}% of attempts): {label}. Check this explicitly before finalizing.")
    return lines


def final_check_lines(case: dict[str, Any], gold: dict[str, Any]) -> list[str]:
    first_key = gold["rows"][0][0] if gold["rows"] else None
    last_key = gold["rows"][-1][0] if gold["rows"] else None
    lines = [
        "Before outputting, self-check row count, row identity keys, numeric formulas, NULL handling, column order, and final sort order against the prompt.",
    ]
    if first_key is not None and last_key is not None:
        lines.append(f"The sorted final table should start with first row key/value {first_key!r} and end with last row key/value {last_key!r} for the first returned column.")
    if case["language"] == "sql":
        lines.append("For SQL answers, put the final ORDER BY in the SQL itself and make the displayed result match that ORDER BY.")
    else:
        lines.append("For pandas answers, explicitly sort the final DataFrame and select the final columns after all calculations are complete.")
    return lines


def build_guidance(case: dict[str, Any], gold: dict[str, Any], failures: list[dict[str, str]]) -> str:
    lines: list[str] = []
    lines.extend(output_contract_lines(case, gold))
    lines.extend(row_boundary_lines(case))
    lines.extend(calculation_lines(case))
    lines.extend(failure_warning_lines(failures))
    lines.extend(final_check_lines(case, gold))

    deduped: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if line not in seen:
            deduped.append(line)
            seen.add(line)

    return GUIDANCE_MARKER + "\n" + "\n".join(f"- {line}" for line in deduped)


def update_standard_instructions() -> None:
    obj = {
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
    }
    write_json(REPO_ROOT / "standard_instructions.json", obj)


def update_cases(failures: dict[str, list[dict[str, str]]], gold_by_case: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = load_jsonl(REPO_ROOT / "benchmark_cases.jsonl")
    for row in rows:
        case_id = row["case_id"]
        if case_id not in gold_by_case:
            raise SystemExit(f"Missing gold answer for {case_id}")
        row["benchmark_id"] = BENCHMARK_ID
        row["standard_instructions_id"] = SQL_STANDARD_ID if row["language"] == "sql" else PYTHON_STANDARD_ID
        base_prompt = strip_existing_guidance(row["prompt"])
        row["prompt"] = base_prompt + "\n\n" + build_guidance(row, gold_by_case[case_id], failures.get(case_id, []))
    write_jsonl(REPO_ROOT / "benchmark_cases.jsonl", rows)
    return rows


def update_gold_and_template() -> None:
    dataset_path = REPO_ROOT / "shared_dataset.json"
    dataset = load_json(dataset_path)
    dataset["benchmark_id"] = BENCHMARK_ID
    write_json(dataset_path, dataset)

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
    path = REPO_ROOT / "benchmark_manifest.json"
    manifest = load_json(path)
    manifest["benchmark_id"] = BENCHMARK_ID
    manifest["version"] = "4.0.0"
    manifest["runner_notes"]["repeatability"] = (
        "Run each case at least three times per model to distinguish stable failures from prompt-sensitive failures. "
        "For v4, shared standards intentionally match the shorter v2 standard instructions while query prompts carry task-specific guardrails from v3 failure analysis."
    )
    write_json(path, manifest)


def update_case_schema() -> None:
    path = REPO_ROOT / "benchmark_case.schema.json"
    schema = load_json(path)
    schema["properties"]["standard_instructions_id"]["enum"] = [SQL_STANDARD_ID, PYTHON_STANDARD_ID]
    schema["allOf"][0]["then"]["properties"]["standard_instructions_id"]["const"] = SQL_STANDARD_ID
    schema["allOf"][1]["then"]["properties"]["standard_instructions_id"]["const"] = PYTHON_STANDARD_ID
    write_json(path, schema)


def update_queries_markdown(cases: list[dict[str, Any]]) -> None:
    lines = [
        "# AIBioBench Queries",
        "",
        "Source: `benchmark_cases.jsonl`",
        "",
        f"Benchmark: `{BENCHMARK_ID}`",
        "",
        f"Total queries: {len(cases)}",
        "",
    ]
    current_pass: int | None = None
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


def update_readme_and_publisher() -> None:
    readme_path = REPO_ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = readme.replace("photosynthesis_snowflake_v3", "photosynthesis_snowflake_v4")
    readme = readme.replace("current v3 benchmark", "current v4 benchmark")
    readme = readme.replace("current v3 results bundle", "current v4 results bundle")
    readme = readme.replace("merged v3 workflow", "prepared v4 workflow")
    readme = readme.replace("shared v3 results bundle", "shared v4 results bundle")
    readme = readme.replace("full v3 bundle", "full v4 bundle")
    readme = readme.replace("v3 bundle", "v4 bundle")
    readme = readme.replace("v3 results bundle", "v4 results bundle")
    readme = readme.replace("v3 workflow", "v4 workflow")
    readme = readme.replace("current v3", "current v4")
    readme = readme.replace("The current repository is centered on the `photosynthesis_snowflake_v4` benchmark.", "The current repository is prepared for the `photosynthesis_snowflake_v4` benchmark.")
    readme = readme.replace(
        "- `QUERIES.md` documents the full prompt set",
        "- `QUERIES.md` documents the full v4 prompt set with task-specific guardrails derived from v3 failure analyses",
    )
    readme_path.write_text(readme, encoding="utf-8")

    publisher_path = REPO_ROOT / "aibiobench-results.py"
    publisher = publisher_path.read_text(encoding="utf-8")
    publisher = publisher.replace('DEFAULT_RESULTS_DIR_NAME = "photosynthesis_snowflake_v3"', 'DEFAULT_RESULTS_DIR_NAME = "photosynthesis_snowflake_v4"')
    publisher = publisher.replace("AIBioBench v3", "AIBioBench v4")
    publisher = publisher.replace("v3 results", "v4 results")
    publisher = publisher.replace("v3 bundle", "v4 bundle")
    publisher = publisher.replace("local v3 bundle", "local v4 bundle")
    publisher = publisher.replace("merged v3 bundle", "merged v4 bundle")
    publisher = publisher.replace("full v3", "full v4")
    publisher = publisher.replace("the v3 bundle", "the v4 bundle")
    publisher = publisher.replace("from the merged v3 bundle", "from the merged v4 bundle")
    publisher = publisher.replace("Update full v3 results bundle", "Update full v4 results bundle")
    publisher_path.write_text(publisher, encoding="utf-8")


def write_local_standard_note() -> None:
    out_dir = REPO_ROOT / "results" / "photosynthesis_snowflake_v4"
    out_dir.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "# STANDARD4",
            "",
            f"Benchmark ID: `{BENCHMARK_ID}`",
            "",
            "Shared standard instructions are intentionally restored to the v2 wording for v4.",
            "Task-specific guidance now lives in each `benchmark_cases.jsonl` prompt.",
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
    (out_dir / "STANDARD4.md").write_text(text, encoding="utf-8")


def main() -> None:
    failures = load_failure_points()
    gold_by_case = load_gold_contracts()

    update_standard_instructions()
    cases = update_cases(failures, gold_by_case)
    update_gold_and_template()
    update_manifest()
    update_case_schema()
    update_queries_markdown(cases)
    update_readme_and_publisher()
    write_local_standard_note()

    missing_failure_guidance = [case["case_id"] for case in cases if "Previous v3 failure warning" not in case["prompt"]]
    if missing_failure_guidance:
        raise SystemExit(f"Cases missing v3 failure warnings: {missing_failure_guidance}")

    print(f"Prepared {len(cases)} v4 cases with restored v2-standard shared instructions.")


if __name__ == "__main__":
    main()
