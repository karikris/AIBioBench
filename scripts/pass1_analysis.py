#!/usr/bin/env python3
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap


PAGE_BG = "#102A43"
PANEL_BG = "#173B59"
GRID = "#3B6386"
TEXT = "#F4FAFF"
MUTED = "#9FC3E6"
BLUE_DARK = "#0F4C81"
BLUE = "#2F80ED"
BLUE_LIGHT = "#89C8FF"
BLUE_PALE = "#D9F0FF"
BLUE_MID = "#4DA3FF"
FAIL_LIGHT = "#5D8CB8"
FAIL_PALE = "#B9D8F2"


QUERY_LABELS = {
    "pass1.query1": "Q1\nsample\ninner join",
    "pass1.query2": "Q2\nvariant\njoin + sort",
    "pass1.query3": "Q3\nsample\nleft join",
    "pass1.query4": "Q4\nsample\nouter agg",
    "pass1.query5": "Q5\nsnowflake\nchain join",
    "pass1.query6": "Q6\nimpact\naggregation",
    "pass1.query7": "Q7\ntissue\nqual agg",
    "pass1.query8": "Q8\ncondition\nexpr agg",
    "pass1.query9": "Q9\ncondition\ndecision",
    "pass1.query10": "Q10\nvariant\naudit",
}

QUERY_SHORT_NAMES = {
    "pass1.query1": "Sample inner join",
    "pass1.query2": "Variant join + qual sort",
    "pass1.query3": "Sample left join",
    "pass1.query4": "Outer join aggregate",
    "pass1.query5": "Variant to gene chain",
    "pass1.query6": "Impact aggregate",
    "pass1.query7": "Tissue qual aggregate",
    "pass1.query8": "Condition expression aggregate",
    "pass1.query9": "Condition decision screen",
    "pass1.query10": "Variant anomaly audit",
}

MODEL_DISPLAY = {
    "codellama-70b-sqlbench:latest": "CodeLlama 70B",
    "command-r-plus-sqlbench:latest": "Command R+",
    "dbrx-sqlbench:latest": "DBRX",
    "deepseek-coder-33b-sqlbench:latest": "DeepSeek Coder 33B",
    "gemma4-26b-sqlbench:latest": "Gemma 4 26B",
    "gemma4-31b-sqlbench:latest": "Gemma 4 31B",
    "llama3-70b-sqlbench:latest": "Llama 3 70B",
    "mixtral-8x22b-sqlbench:latest": "Mixtral 8x22B",
    "phi4-mini-sqlbench:latest": "Phi-4 Mini",
    "qwen2.5-72b-sqlbench:latest": "Qwen 2.5 72B",
    "qwen2.5-coder-32b-sqlbench:latest": "Qwen 2.5 Coder 32B",
    "qwen3-coder-30b-sqlbench:latest": "Qwen3 Coder 30B",
    "qwen3.6-sqlbench:latest": "Qwen3.6",
    "qwen3.6-27b-sqlbench:latest": "Qwen3.6 27B",
}

MODEL_GROUP_COLORS = {
    "Broad pass leader": BLUE_PALE,
    "Strong but narrow exactness": BLUE_LIGHT,
    "Near-miss operators": BLUE_MID,
    "Brittle / low-coverage": BLUE_DARK,
}

ISSUE_LABELS = {
    "q1_included_orphan_s999": "Included orphan sample row S999/call_id 8 that should disappear under the inner join.",
    "q1_dropped_call9": "Dropped call_id 9 even though sample S2 exists and should survive the sample join.",
    "q1_attribute_leakage": "Leaked tissue or condition values across rows instead of preserving sample attributes.",
    "q2_wrong_sort": "Returned the matched row set but not in `qual DESC, call_id ASC` order.",
    "q2_included_v999": "Included call_id 9 / V999 despite the required inner join to `variant_dim`.",
    "q2_dropped_matched_calls": "Dropped valid matched calls from the joined result.",
    "q3_type_only": "Matched the table semantically but serialized numbers/nulls with the wrong types.",
    "q3_bad_unmatched_row": "Did not preserve the unmatched `S999` row cleanly in the left join output.",
    "q3_attribute_mixup": "Mixed condition values into tissue/batch fields or used the wrong expression values.",
    "q4_missing_s5": "Dropped zero-call sample `S5`, so the outer join coverage was incomplete.",
    "q4_s2_undercounted": "Undercounted `S2` by missing one fact row, usually call_id 9.",
    "q4_s2_avg_wrong": "Computed the `S2` average incorrectly, often from the wrong row set or over-rounded output.",
    "q5_kept_call6": "Kept call_id 6 / V5 after the second inner join instead of dropping the incomplete chain.",
    "q5_kept_call9": "Kept unmatched call_id 9 / V999 even though the chain join should remove it.",
    "q5_dropped_matched_rows": "Dropped valid matched rows while traversing the fact -> variant -> gene chain.",
    "q6_high_undercount": "Under-counted high-impact calls by not aggregating both V2 and V3 duplicates.",
    "q6_moderate_undercount": "Under-counted the two moderate V1 calls.",
    "q6_missing_categories": "Dropped one or more impact categories such as `modifier` or `low`.",
    "q6_avg_wrong": "Used the wrong row set for average quality per impact bucket.",
    "q7_included_root": "Included `root` / `S5` even though the task required an inner join to fact rows only.",
    "q7_misweighted_avg": "Computed tissue averages from the wrong grain instead of fact-call-weighted quality values.",
    "q7_wrong_extrema": "Minimum or maximum quality per tissue came from the wrong row set.",
    "q8_sample_counts": "Used sample counts instead of fact-call counts for one or more conditions.",
    "q8_high_light_leak": "Leaked `S5` / `high_light` into the aggregate, inflating the high-light bucket.",
    "q8_expr_misweighted": "Averaged expression at the wrong grain instead of call-weighting by joined fact rows.",
    "q9_wrong_total_calls": "Used the wrong total-call counts, usually from sample-level counting or leaked rows.",
    "q9_high_impact_miss": "Missed the high-impact filter/count after joining to `variant_dim`.",
    "q9_high_light_leak": "Inflated the high-light bucket by leaking unmatched or extra rows.",
    "q10_type_only": "Matched the audit semantically but serialized identifiers with the wrong types.",
    "q10_nullified_v999": "Nullified `variant_id` for call_id 9 instead of preserving `V999` from the fact table.",
    "q10_false_missing_variant": "Marked matched variants as `MISSING_VARIANT` instead of `MATCHED`.",
    "q10_dropped_call9": "Dropped the unmatched call_id 9 row despite the required left join.",
}


def as_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def as_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def coerce_numeric_strings(value):
    if isinstance(value, list):
        return [coerce_numeric_strings(v) for v in value]
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"[+-]?\d+", text):
            return int(text)
        if re.fullmatch(r"[+-]?(?:(?:\d+\.\d*)|(?:\.\d+)|(?:\d+[eE][+-]?\d+)|(?:(?:\d+\.\d*)|(?:\.\d+))[eE][+-]?\d+)", text):
            try:
                number = float(text)
                if math.isfinite(number):
                    return number
            except Exception:
                return value
    return value


def canonical_model_name(model: str) -> str:
    return MODEL_DISPLAY.get(model, model.replace(":latest", ""))


def wrap_display_name(name: str) -> str:
    if " " not in name:
        return name
    first, rest = name.split(" ", 1)
    return f"{first}\n{rest}"


def classify_failure(row: dict) -> str:
    if row["status"] != "ok" or not as_bool(row["valid_json"]):
        return "invalid_json_or_error"
    if not as_bool(row["column_exact_match"]):
        return "column_error"
    if as_bool(row["exact_match"]):
        return "exact"

    try:
        gold_rows = json.loads(row["gold_rows_json"])
        pred_rows = json.loads(row["parsed_rows_json"])
    except Exception:
        return "invalid_json_or_error"
    if coerce_numeric_strings(pred_rows) == coerce_numeric_strings(gold_rows):
        return "type_only"

    if not as_bool(row["row_count_match"]):
        return "row_count_mismatch"

    if int(row["missing_rows_count"]) == 0 and int(row["extra_rows_count"]) == 0:
        return "order_only"

    return "same_count_wrong_values"


def load_metadata(repo_root: Path):
    case_meta = {}
    with (repo_root / "benchmark_cases.jsonl").open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            if item["case_id"].startswith("pass1."):
                case_meta[item["case_id"]] = item

    gold = {}
    with (repo_root / "gold_answers.jsonl").open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            if item["case_id"].startswith("pass1."):
                gold[item["case_id"]] = item

    return case_meta, gold


def load_rows(results_dir: Path) -> list[dict]:
    rows = []
    with (results_dir / "detailed_results.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["pass"] != "1":
                continue
            row["_failure_mode"] = classify_failure(row)
            try:
                row["_pred_rows"] = json.loads(row["parsed_rows_json"])
            except Exception:
                row["_pred_rows"] = []
            try:
                row["_gold_rows"] = json.loads(row["gold_rows_json"])
            except Exception:
                row["_gold_rows"] = []
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def case_sort_key(case_id: str) -> int:
    return int(case_id.split("query")[1])


def rows_to_keyed_dict(rows, key_index: int):
    out = {}
    for row in rows:
        if isinstance(row, list) and len(row) > key_index:
            out[row[key_index]] = row
    return out


def detect_issue_flags(case_id: str, pred_rows: list, gold_rows: list, row: dict) -> list[str]:
    flags = []
    pred_rows = coerce_numeric_strings(pred_rows)
    gold_rows = coerce_numeric_strings(gold_rows)
    pred_keyed = None
    gold_keyed = None

    if case_id in {
        "pass1.query1",
        "pass1.query2",
        "pass1.query3",
        "pass1.query5",
        "pass1.query10",
    }:
        pred_keyed = rows_to_keyed_dict(pred_rows, 0)
        gold_keyed = rows_to_keyed_dict(gold_rows, 0)

    if case_id == "pass1.query1":
        if 8 in pred_keyed:
            flags.append("q1_included_orphan_s999")
        if 9 not in pred_keyed:
            flags.append("q1_dropped_call9")
        for call_id in [2, 3, 4, 5, 6, 9]:
            if call_id in pred_keyed and call_id in gold_keyed and pred_keyed[call_id][2:4] != gold_keyed[call_id][2:4]:
                flags.append("q1_attribute_leakage")
                break

    elif case_id == "pass1.query2":
        pred_ids = [r[0] for r in pred_rows if r]
        gold_ids = [r[0] for r in gold_rows if r]
        if row["_failure_mode"] == "order_only":
            flags.append("q2_wrong_sort")
        if 9 in pred_ids:
            flags.append("q2_included_v999")
        if not set(gold_ids).issubset(set(pred_ids)):
            flags.append("q2_dropped_matched_calls")
        elif pred_ids != gold_ids:
            flags.append("q2_wrong_sort")

    elif case_id == "pass1.query3":
        if row["_failure_mode"] == "type_only":
            flags.append("q3_type_only")
        row8 = pred_keyed.get(8)
        if row8 is None or row8[1] != "S999" or row8[2:] != [None, None, None]:
            flags.append("q3_bad_unmatched_row")
        for call_id in [5, 6, 7]:
            if call_id in pred_keyed and call_id in gold_keyed and pred_keyed[call_id][2:] != gold_keyed[call_id][2:]:
                flags.append("q3_attribute_mixup")
                break

    elif case_id == "pass1.query4":
        pred_keyed = rows_to_keyed_dict(pred_rows, 0)
        s5 = pred_keyed.get("S5")
        s2 = pred_keyed.get("S2")
        if s5 is None:
            flags.append("q4_missing_s5")
        if s2 is not None and s2[2] != 3:
            flags.append("q4_s2_undercounted")
        if s2 is not None:
            try:
                if s2[3] is not None and abs(float(s2[3]) - 76.667) > 0.001:
                    flags.append("q4_s2_avg_wrong")
            except Exception:
                flags.append("q4_s2_avg_wrong")

    elif case_id == "pass1.query5":
        pred_ids = {r[0] for r in pred_rows if r}
        gold_ids = {r[0] for r in gold_rows if r}
        if 6 in pred_ids:
            flags.append("q5_kept_call6")
        if 9 in pred_ids:
            flags.append("q5_kept_call9")
        if not gold_ids.issubset(pred_ids):
            flags.append("q5_dropped_matched_rows")

    elif case_id == "pass1.query6":
        pred_keyed = rows_to_keyed_dict(pred_rows, 0)
        high = pred_keyed.get("high")
        moderate = pred_keyed.get("moderate")
        if high is None or high[1] != 4:
            flags.append("q6_high_undercount")
        if moderate is None or moderate[1] != 2:
            flags.append("q6_moderate_undercount")
        if "low" not in pred_keyed or "modifier" not in pred_keyed:
            flags.append("q6_missing_categories")
        for label, expected in [("high", 78.75), ("moderate", 97.0), ("low", 70.0), ("modifier", 92.0)]:
            if label in pred_keyed:
                try:
                    if abs(float(pred_keyed[label][2]) - expected) > 0.001:
                        flags.append("q6_avg_wrong")
                        break
                except Exception:
                    flags.append("q6_avg_wrong")
                    break

    elif case_id == "pass1.query7":
        pred_keyed = rows_to_keyed_dict(pred_rows, 0)
        if "root" in pred_keyed:
            flags.append("q7_included_root")
        expected = {"young_leaf": (83.333, 70, 92), "mature_leaf": (83.2, 55, 99)}
        for tissue, metrics in expected.items():
            if tissue in pred_keyed:
                row_vals = pred_keyed[tissue]
                try:
                    if abs(float(row_vals[1]) - metrics[0]) > 0.001:
                        flags.append("q7_misweighted_avg")
                    if row_vals[2] != metrics[1] or row_vals[3] != metrics[2]:
                        flags.append("q7_wrong_extrema")
                except Exception:
                    flags.append("q7_misweighted_avg")
            else:
                flags.append("q7_misweighted_avg")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass1.query8":
        pred_keyed = rows_to_keyed_dict(pred_rows, 0)
        counts = {"control": 4, "drought": 2, "high_light": 2}
        expected_expr = {"control": 475.0, "drought": 700.0, "high_light": 800.0}
        for condition, expected_count in counts.items():
            if condition not in pred_keyed or pred_keyed[condition][1] != expected_count:
                flags.append("q8_sample_counts")
        if "high_light" in pred_keyed:
            try:
                if float(pred_keyed["high_light"][1]) > 2:
                    flags.append("q8_high_light_leak")
            except Exception:
                pass
        for condition, expected_avg in expected_expr.items():
            if condition in pred_keyed:
                try:
                    if abs(float(pred_keyed[condition][2]) - expected_avg) > 0.001:
                        flags.append("q8_expr_misweighted")
                        break
                except Exception:
                    flags.append("q8_expr_misweighted")
                    break

    elif case_id == "pass1.query9":
        pred_keyed = rows_to_keyed_dict(pred_rows, 0)
        counts = {"control": 3, "drought": 2, "high_light": 2}
        impacts = {"control": 2, "drought": 0, "high_light": 1}
        for condition, expected_count in counts.items():
            if condition not in pred_keyed or pred_keyed[condition][1] != expected_count:
                flags.append("q9_wrong_total_calls")
        if "high_light" in pred_keyed and pred_keyed["high_light"][1] > 2:
            flags.append("q9_high_light_leak")
        for condition, expected_hits in impacts.items():
            if condition not in pred_keyed or pred_keyed[condition][3] != expected_hits:
                flags.append("q9_high_impact_miss")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass1.query10":
        if row["_failure_mode"] == "type_only":
            flags.append("q10_type_only")
        pred_keyed = rows_to_keyed_dict(pred_rows, 0)
        row9 = pred_keyed.get(9) or pred_keyed.get("9")
        if row9 is None:
            flags.append("q10_dropped_call9")
        else:
            if row9[1] is None:
                flags.append("q10_nullified_v999")
        for call_id, expected_impact in [(2, "high"), (4, "high"), (5, "low"), (6, "modifier"), (7, "high")]:
            key = call_id if call_id in pred_keyed else str(call_id)
            if key in pred_keyed and pred_keyed[key][3] != "MATCHED":
                flags.append("q10_false_missing_variant")
                break

    return list(dict.fromkeys(flags))


def build_summaries(rows: list[dict], case_meta: dict):
    by_model = defaultdict(list)
    by_case = defaultdict(list)
    by_model_case = defaultdict(list)

    for row in rows:
        by_model[row["model"]].append(row)
        by_case[row["case_id"]].append(row)
        by_model_case[(row["model"], row["case_id"])].append(row)

    model_summary = []
    for model, items in by_model.items():
        exact_attempts = sum(as_bool(r["exact_match"]) for r in items)
        exact_query_coverage_any = sum(
            any(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)])
            for case_id in sorted({r["case_id"] for r in items}, key=case_sort_key)
        )
        stable_exact_queries = sum(
            sum(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) == 3
            for case_id in sorted({r["case_id"] for r in items}, key=case_sort_key)
        )
        partial_exact_queries = sum(
            0 < sum(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) < 3
            for case_id in sorted({r["case_id"] for r in items}, key=case_sort_key)
        )
        stable_fail_queries = sum(
            sum(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) == 0
            for case_id in sorted({r["case_id"] for r in items}, key=case_sort_key)
        )
        modes = Counter(r["_failure_mode"] for r in items)
        summary = {
            "model": model,
            "display_model": canonical_model_name(model),
            "attempts": len(items),
            "exact_attempts": exact_attempts,
            "exact_attempt_rate": exact_attempts / len(items),
            "exact_query_coverage_any": exact_query_coverage_any,
            "stable_exact_queries": stable_exact_queries,
            "partial_exact_queries": partial_exact_queries,
            "stable_fail_queries": stable_fail_queries,
            "mean_score": mean(as_float(r["score"]) for r in items),
            "mean_aligned_cell_accuracy": mean(as_float(r["aligned_cell_accuracy"]) for r in items),
            "mean_row_set_correctness": mean(as_float(r["row_set_correctness_score"]) for r in items),
            "mean_numeric_correctness": mean(as_float(r["numeric_correctness_score"]) for r in items),
            "mean_sort_correctness": mean(as_float(r["sort_order_correctness_score"]) for r in items),
            "row_count_mismatch_rate": mean(not as_bool(r["row_count_match"]) for r in items),
            "mean_wall_s": mean(as_float(r["client_wall_s"]) for r in items),
            "mean_gen_tps": mean(as_float(r["server_gen_tps"]) for r in items),
            "exact": modes["exact"],
            "order_only": modes["order_only"],
            "type_only": modes["type_only"],
            "same_count_wrong_values": modes["same_count_wrong_values"],
            "row_count_mismatch": modes["row_count_mismatch"],
            "column_error": modes["column_error"],
            "invalid_json_or_error": modes["invalid_json_or_error"],
            "dominant_failure_mode": modes.most_common(1)[0][0],
            "dominant_non_exact_failure_mode": (modes - Counter({"exact": modes["exact"]})).most_common(1)[0][0]
            if sum(count for mode, count in modes.items() if mode != "exact")
            else "none",
        }
        model_summary.append(summary)

    model_summary.sort(
        key=lambda r: (
            -r["exact_attempts"],
            -r["exact_query_coverage_any"],
            -r["mean_score"],
            r["mean_wall_s"],
            r["display_model"],
        )
    )

    case_summary = []
    for case_id in sorted(by_case, key=case_sort_key):
        items = by_case[case_id]
        modes = Counter(r["_failure_mode"] for r in items)
        exact_attempts = sum(as_bool(r["exact_match"]) for r in items)
        exact_models_any = sum(
            any(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)])
            for model in sorted({r["model"] for r in items})
        )
        exact_models_stable = sum(
            sum(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) == 3
            for model in sorted({r["model"] for r in items})
        )
        issue_counter = Counter()
        issue_models = defaultdict(set)
        for row in items:
            issue_flags = detect_issue_flags(case_id, row["_pred_rows"], row["_gold_rows"], row)
            row["_issue_flags"] = issue_flags
            for issue in issue_flags:
                issue_counter[issue] += 1
                issue_models[issue].add(canonical_model_name(row["model"]))

        top_issues = []
        for issue, count in issue_counter.most_common(3):
            example_models = ", ".join(sorted(issue_models[issue])[:4])
            top_issues.append(
                {
                    "issue_code": issue,
                    "issue_label": ISSUE_LABELS[issue],
                    "attempts_with_issue": count,
                    "attempt_pct": count / len(items),
                    "example_models": example_models,
                }
            )

        case_summary.append(
            {
                "case_id": case_id,
                "query": f"Q{case_sort_key(case_id)}",
                "short_name": QUERY_SHORT_NAMES.get(case_id, case_id),
                "prompt": case_meta[case_id]["prompt"],
                "run_benchmark_id": items[0].get("benchmark_id", ""),
                "metadata_benchmark_id": case_meta[case_id].get("benchmark_id", ""),
                "metadata_matches_run": items[0].get("benchmark_id", "") == case_meta[case_id].get("benchmark_id", ""),
                "primary_failure_family": case_meta[case_id]["metadata"]["failure_family_primary"],
                "total_attempts": len(items),
                "exact_attempts": exact_attempts,
                "exact_attempt_rate": exact_attempts / len(items),
                "exact_models_any": exact_models_any,
                "exact_models_stable": exact_models_stable,
                "mean_score": mean(as_float(r["score"]) for r in items),
                "mean_aligned_cell_accuracy": mean(as_float(r["aligned_cell_accuracy"]) for r in items),
                "row_count_mismatch_attempts": sum(not as_bool(r["row_count_match"]) for r in items),
                "same_count_wrong_attempts": modes["same_count_wrong_values"],
                "order_only_attempts": modes["order_only"],
                "type_only_attempts": modes["type_only"],
                "column_error_attempts": modes["column_error"],
                "invalid_json_or_error_attempts": modes["invalid_json_or_error"],
                "dominant_failure_mode": modes.most_common(1)[0][0],
                "dominant_non_exact_failure_mode": (modes - Counter({"exact": modes["exact"]})).most_common(1)[0][0]
                if sum(count for mode, count in modes.items() if mode != "exact")
                else "none",
                "top_issues": top_issues,
            }
        )

    model_query_rows = []
    for (model, case_id), items in sorted(by_model_case.items(), key=lambda x: (canonical_model_name(x[0][0]), case_sort_key(x[0][1]))):
        modes = Counter(r["_failure_mode"] for r in items)
        exact_attempts = sum(as_bool(r["exact_match"]) for r in items)
        model_query_rows.append(
            {
                "model": model,
                "display_model": canonical_model_name(model),
                "case_id": case_id,
                "query": f"Q{case_sort_key(case_id)}",
                "short_name": QUERY_SHORT_NAMES.get(case_id, case_id),
                "exact_attempts": exact_attempts,
                "exact_rate": exact_attempts / len(items),
                "mean_score": mean(as_float(r["score"]) for r in items),
                "mean_aligned_cell_accuracy": mean(as_float(r["aligned_cell_accuracy"]) for r in items),
                "dominant_failure_mode": modes.most_common(1)[0][0],
                "dominant_non_exact_failure_mode": (modes - Counter({"exact": modes["exact"]})).most_common(1)[0][0]
                if sum(count for mode, count in modes.items() if mode != "exact")
                else "none",
                "stable_outcome": "stable_exact" if exact_attempts == 3 else ("partial_exact" if exact_attempts > 0 else "stable_fail"),
            }
        )

    return model_summary, case_summary, model_query_rows


def compute_family_scores(model_query_rows: list[dict], case_meta: dict) -> list[dict]:
    family_lookup = {
        row["case_id"]: case_meta[row["case_id"]]["metadata"]["failure_family_primary"]
        for row in model_query_rows
    }
    acc = defaultdict(list)
    for row in model_query_rows:
        family = family_lookup[row["case_id"]]
        acc[(row["model"], family)].append(row)

    out = []
    for (model, family), items in sorted(acc.items(), key=lambda x: (canonical_model_name(x[0][0]), x[0][1])):
        out.append(
            {
                "model": model,
                "display_model": canonical_model_name(model),
                "family": family,
                "mean_score": mean(item["mean_score"] for item in items),
                "mean_exact_rate": mean(item["exact_rate"] for item in items),
            }
        )
    return out


def assign_model_groups(model_summary: list[dict], model_query_rows: list[dict]) -> list[dict]:
    matrix = defaultdict(dict)
    for row in model_query_rows:
        matrix[row["model"]][row["case_id"]] = row

    groups = []
    for item in model_summary:
        model = item["model"]
        structural_cases = ["pass1.query1", "pass1.query3", "pass1.query4", "pass1.query5", "pass1.query10"]
        analytical_cases = ["pass1.query6", "pass1.query7", "pass1.query8", "pass1.query9"]
        sorting_cases = ["pass1.query2"]
        structural_score = mean(matrix[model][case]["mean_score"] for case in structural_cases)
        analytical_score = mean(matrix[model][case]["mean_score"] for case in analytical_cases)
        sorting_score = mean(matrix[model][case]["mean_score"] for case in sorting_cases)

        if item["exact_attempts"] >= 12 or item["exact_query_coverage_any"] >= 5:
            group = "Broad pass leader"
            reason = "Only model family with exact coverage spanning half of the suite and strong partial credit on the remaining aggregation tasks."
        elif item["exact_attempts"] >= 6 and item["mean_score"] >= 0.82:
            group = "Strong but narrow exactness"
            reason = "Reliable exactness on a few structural tasks, then near-exact rather than exact on the harder aggregation screens."
        elif item["mean_score"] >= 0.78 and item["exact_query_coverage_any"] <= 1:
            group = "Near-miss operators"
            reason = "Often one join/filter/count fix away from correctness, but exact-match brittleness kept them from converting those near misses."
        else:
            group = "Brittle / low-coverage"
            reason = "Low exact coverage plus repeated row-count, type, or schema-level mistakes kept performance unstable."

        groups.append(
            {
                "model": model,
                "display_model": item["display_model"],
                "group": group,
                "group_reason": reason,
                "structural_score": structural_score,
                "analytical_score": analytical_score,
                "sorting_score": sorting_score,
                "exact_attempts": item["exact_attempts"],
                "stable_exact_queries": item["stable_exact_queries"],
                "partial_exact_queries": item["partial_exact_queries"],
                "stable_fail_queries": item["stable_fail_queries"],
                "mean_score": item["mean_score"],
            }
        )

    group_order = {
        "Broad pass leader": 0,
        "Strong but narrow exactness": 1,
        "Near-miss operators": 2,
        "Brittle / low-coverage": 3,
    }
    groups.sort(key=lambda r: (group_order[r["group"]], -r["exact_attempts"], -r["mean_score"], r["display_model"]))
    return groups


def style_axis(ax):
    ax.set_facecolor(PANEL_BG)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=TEXT, labelcolor=TEXT)
    ax.title.set_color(TEXT)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)


def render_visual_report(model_summary, case_summary, model_query_rows, family_scores, out_base: Path):
    models = [m["model"] for m in model_summary]
    model_labels = [m["display_model"] for m in model_summary]
    cases = [c["case_id"] for c in case_summary]
    case_labels = [QUERY_LABELS.get(c, c) for c in cases]
    row_lookup = {(r["model"], r["case_id"]): r for r in model_query_rows}

    exact_matrix = [[row_lookup[(model, case)]["exact_rate"] for case in cases] for model in models]
    score_matrix = [[row_lookup[(model, case)]["mean_score"] for case in cases] for model in models]

    family_order = [
        "inner_join_accuracy",
        "sorting_presentation",
        "outer_join_coverage",
        "snowflake_traversal",
        "aggregation_numeric",
        "join_key_integrity",
        "decision_support",
    ]
    family_short = {
        "inner_join_accuracy": "Inner\njoin",
        "sorting_presentation": "Sort",
        "outer_join_coverage": "Outer\njoin",
        "snowflake_traversal": "3-table\nchain",
        "aggregation_numeric": "Agg\nnumeric",
        "join_key_integrity": "Join key\nintegrity",
        "decision_support": "Decision\nscreen",
    }
    family_lookup = {(r["model"], r["family"]): r for r in family_scores}
    family_matrix = [
        [
            family_lookup[(model, family)]["mean_score"] if (model, family) in family_lookup else float("nan")
            for family in family_order
        ]
        for model in models
    ]

    fig = plt.figure(figsize=(21, 16), facecolor=PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.25, 1.0])
    fig.suptitle(
        "AIBioBench Pass 1, Latest Run: Exactness, Near Misses, and Failure Shape",
        fontsize=24,
        fontweight="bold",
        color=TEXT,
    )

    ax1 = fig.add_subplot(gs[0, 0])
    style_axis(ax1)
    y = list(range(len(model_summary)))
    exacts = [m["exact_attempts"] for m in model_summary]
    colors = []
    for x in exacts:
        if x >= 12:
            colors.append(BLUE_PALE)
        elif x >= 6:
            colors.append(BLUE_LIGHT)
        elif x >= 3:
            colors.append(BLUE_MID)
        else:
            colors.append(BLUE_DARK)
    bars = ax1.barh(y, exacts, color=colors)
    ax1.set_yticks(y, model_labels)
    ax1.invert_yaxis()
    ax1.set_xlim(0, 30)
    ax1.set_xlabel("Exact attempts out of 30", color=TEXT)
    ax1.set_title("Exact Match Conversion by Model", fontweight="bold")
    ax1.grid(axis="x", color=GRID, linewidth=1)
    for bar, item in zip(bars, model_summary):
        ax1.text(
            min(bar.get_width() + 0.35, 29.4),
            bar.get_y() + bar.get_height() / 2,
            f"{item['exact_attempts']}/30  |  {item['exact_query_coverage_any']}/10 queries",
            va="center",
            ha="left",
            color=TEXT,
            fontsize=9,
        )

    ax2 = fig.add_subplot(gs[0, 1])
    style_axis(ax2)
    exact_cmap = LinearSegmentedColormap.from_list("exact_blues", [BLUE_DARK, BLUE, BLUE_LIGHT, BLUE_PALE])
    im1 = ax2.imshow(exact_matrix, aspect="auto", cmap=exact_cmap, vmin=0, vmax=1)
    ax2.set_xticks(range(len(cases)), case_labels)
    ax2.set_yticks(range(len(models)), model_labels)
    ax2.set_title("Exact Rate by Model and Query (3 repeats)", fontweight="bold")
    for i in range(len(models)):
        for j in range(len(cases)):
            val = exact_matrix[i][j]
            ax2.text(
                j,
                i,
                f"{val:.0%}",
                ha="center",
                va="center",
                color=PAGE_BG if val >= 0.67 else TEXT,
                fontsize=8,
                fontweight="bold" if val > 0 else "normal",
            )
    cbar1 = fig.colorbar(im1, ax=ax2, fraction=0.028, pad=0.02)
    cbar1.ax.tick_params(labelsize=8, colors=TEXT)
    cbar1.outline.set_edgecolor(GRID)

    ax3 = fig.add_subplot(gs[1, 0])
    style_axis(ax3)
    score_cmap = LinearSegmentedColormap.from_list("score_blues", [BLUE_DARK, BLUE, BLUE_LIGHT, BLUE_PALE])
    im2 = ax3.imshow(score_matrix, aspect="auto", cmap=score_cmap, vmin=0, vmax=1)
    ax3.set_xticks(range(len(cases)), case_labels)
    ax3.set_yticks(range(len(models)), model_labels)
    ax3.set_title("Mean Score by Model and Query", fontweight="bold")
    for i in range(len(models)):
        for j in range(len(cases)):
            val = score_matrix[i][j]
            ax3.text(
                j,
                i,
                f"{val:.2f}",
                ha="center",
                va="center",
                color=PAGE_BG if val >= 0.83 else TEXT,
                fontsize=8,
                fontweight="bold" if val >= 0.95 else "normal",
            )
    cbar2 = fig.colorbar(im2, ax=ax3, fraction=0.028, pad=0.02)
    cbar2.ax.tick_params(labelsize=8, colors=TEXT)
    cbar2.outline.set_edgecolor(GRID)

    ax4 = fig.add_subplot(gs[1, 1])
    style_axis(ax4)
    mode_order = [
        ("exact", "Exact", BLUE_PALE),
        ("order_only", "Right rows, wrong order", BLUE_LIGHT),
        ("type_only", "Type only", BLUE_MID),
        ("same_count_wrong_values", "Same count, wrong values", FAIL_LIGHT),
        ("row_count_mismatch", "Wrong row count", BLUE_DARK),
        ("column_error", "Column/schema error", FAIL_PALE),
        ("invalid_json_or_error", "Invalid JSON/error", TEXT),
    ]
    bottoms = [0] * len(cases)
    for mode, label, color in mode_order:
        vals = [
            sum(1 for row in model_query_rows if row["case_id"] == case and row["dominant_failure_mode"] == mode)
            for case in cases
        ]
        ax4.bar(range(len(cases)), vals, bottom=bottoms, label=label, color=color, edgecolor=PANEL_BG)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax4.set_xticks(range(len(cases)), [c.split(".")[-1].upper() for c in cases])
    ax4.set_ylim(0, len(models))
    ax4.set_ylabel("Models", color=TEXT)
    ax4.set_title("Dominant Failure Mode by Query", fontweight="bold")
    ax4.grid(axis="y", color=GRID, linewidth=1)
    leg = ax4.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=9)
    for text in leg.get_texts():
        text.set_color(TEXT)

    ax5 = fig.add_subplot(gs[2, 0])
    style_axis(ax5)
    im3 = ax5.imshow(family_matrix, aspect="auto", cmap=score_cmap, vmin=0, vmax=1)
    ax5.set_xticks(range(len(family_order)), [family_short[f] for f in family_order])
    ax5.set_yticks(range(len(models)), model_labels)
    ax5.set_title("Capability View: Mean Score by Failure Family", fontweight="bold")
    for i in range(len(models)):
        for j in range(len(family_order)):
            val = family_matrix[i][j]
            if not math.isnan(val):
                ax5.text(
                    j,
                    i,
                    f"{val:.2f}",
                    ha="center",
                    va="center",
                    color=PAGE_BG if val >= 0.83 else TEXT,
                    fontsize=8,
                )
    cbar3 = fig.colorbar(im3, ax=ax5, fraction=0.028, pad=0.02)
    cbar3.ax.tick_params(labelsize=8, colors=TEXT)
    cbar3.outline.set_edgecolor(GRID)

    ax6 = fig.add_subplot(gs[2, 1])
    style_axis(ax6)
    query_scores = [c["mean_score"] for c in case_summary]
    query_exacts = [c["exact_attempt_rate"] for c in case_summary]
    x = list(range(len(cases)))
    ax6.plot(x, query_scores, color=BLUE_PALE, linewidth=3, marker="o", markersize=8, label="Mean score")
    ax6.plot(x, query_exacts, color=BLUE_MID, linewidth=2.3, marker="s", markersize=6, label="Exact rate")
    ax6.fill_between(x, query_scores, color=BLUE_MID, alpha=0.15)
    ax6.set_xticks(x, [c.split(".")[-1].upper() for c in cases])
    ax6.set_ylim(0, 1.05)
    ax6.set_ylabel("Rate / score", color=TEXT)
    ax6.set_title("Which Questions Actually Broke the Models", fontweight="bold")
    ax6.grid(axis="y", color=GRID, linewidth=1)
    for idx, case in enumerate(case_summary):
        ax6.text(
            idx,
            min(case["mean_score"] + 0.04, 1.02),
            f"{case['exact_attempts']}/{case['total_attempts']} exact",
            ha="center",
            va="bottom",
            color=TEXT,
            fontsize=8,
        )
    leg = ax6.legend(frameon=False, fontsize=9, loc="lower left")
    for text in leg.get_texts():
        text.set_color(TEXT)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def render_model_groups(groups: list[dict], out_base: Path):
    fig = plt.figure(figsize=(18, 10), facecolor=PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0])
    fig.suptitle(
        "AIBioBench Pass 1: Model Grouping by Structural vs Analytical Performance",
        fontsize=22,
        fontweight="bold",
        color=TEXT,
    )

    ax1 = fig.add_subplot(gs[0, 0])
    style_axis(ax1)
    for item in groups:
        color = MODEL_GROUP_COLORS[item["group"]]
        ax1.scatter(
            item["structural_score"],
            item["analytical_score"],
            s=120 + item["exact_attempts"] * 28,
            color=color,
            edgecolors=BLUE_PALE,
            linewidth=1.2,
            alpha=0.95,
        )
        ax1.annotate(
            wrap_display_name(item["display_model"]),
            (item["structural_score"], item["analytical_score"]),
            xytext=(7, 6),
            textcoords="offset points",
            color=TEXT,
            fontsize=9,
        )
    ax1.set_xlabel("Structural tasks mean score\n(Q1, Q3, Q4, Q5, Q10)")
    ax1.set_ylabel("Analytical tasks mean score\n(Q6, Q7, Q8, Q9)")
    ax1.set_xlim(0, 1.03)
    ax1.set_ylim(0, 1.03)
    ax1.set_title("Group separation appears in structural exactness first", fontweight="bold")
    ax1.grid(color=GRID, linewidth=1)

    ax2 = fig.add_subplot(gs[0, 1])
    style_axis(ax2)
    y = list(range(len(groups)))
    stable_exact = [g["stable_exact_queries"] for g in groups]
    partial = [g["partial_exact_queries"] for g in groups]
    stable_fail = [g["stable_fail_queries"] for g in groups]
    ax2.barh(y, stable_fail, color=BLUE_DARK, label="Stable fail")
    ax2.barh(y, partial, left=stable_fail, color=BLUE_MID, label="Prompt-sensitive exact")
    ax2.barh(y, stable_exact, left=[a + b for a, b in zip(stable_fail, partial)], color=BLUE_PALE, label="Stable exact")
    ax2.set_yticks(y, [g["display_model"] for g in groups])
    ax2.invert_yaxis()
    ax2.set_xlim(0, 10)
    ax2.set_xlabel("Queries out of 10")
    ax2.set_title("Repeatability profile by model", fontweight="bold")
    ax2.grid(axis="x", color=GRID, linewidth=1)
    for idx, item in enumerate(groups):
        ax2.text(
            9.95,
            idx,
            item["group"],
            ha="right",
            va="center",
            color=TEXT,
            fontsize=8,
        )
    leg = ax2.legend(loc="lower right", frameon=False, fontsize=9)
    for text in leg.get_texts():
        text.set_color(TEXT)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def build_failure_point_rows(case_summary: list[dict]) -> list[dict]:
    rows = []
    for case in case_summary:
        for issue in case["top_issues"]:
            rows.append(
                {
                    "case_id": case["case_id"],
                    "query": case["query"],
                    "short_name": case["short_name"],
                    "issue_code": issue["issue_code"],
                    "issue_label": issue["issue_label"],
                    "attempts_with_issue": issue["attempts_with_issue"],
                    "attempt_pct": issue["attempt_pct"],
                    "example_models": issue["example_models"],
                }
            )
    return rows


def write_notes(path: Path, model_summary: list[dict], case_summary: list[dict], groups: list[dict], results_dir: Path) -> None:
    model_count = len(model_summary)
    top_model = model_summary[0]
    exact_queries = [case["query"] for case in case_summary if case["exact_attempts"] > 0]
    zero_exact_queries = [case["query"] for case in case_summary if case["exact_attempts"] == 0]
    exact_query_text = ", ".join(exact_queries) if exact_queries else "none"
    zero_exact_text = ", ".join(zero_exact_queries) if zero_exact_queries else "none"
    lines = [
        "# AIBioBench Pass 1 Analysis",
        "",
        f"Run analyzed: `{results_dir.name}`",
        "",
        f"Pass 1 in this run contains ten easy SQL tasks, each repeated three times across {model_count} models. The charts in this folder focus on exact-match conversion, partial-credit behavior, repeatability, and the recurring failure points that kept models from converting high partial scores into exact answers.",
        "",
        "## Headline Findings",
        "",
        f"- **{top_model['display_model']}** led the pass with {top_model['exact_attempts']}/30 exact attempts and exact coverage on {top_model['exact_query_coverage_any']}/10 questions.",
        f"- Exact answers appeared on **{exact_query_text}**; zero-exact questions were **{zero_exact_text}**.",
        "- Several models posted strong mean scores despite weak exact conversion. That means the main gap was often a final join/filter/count/sort decision, not total failure to understand the task.",
        "- Failure patterns split cleanly into structural join mistakes on Q1/Q4/Q5/Q10 and misweighted aggregation mistakes on Q6-Q9.",
        "",
        "## Model Groups",
        "",
        "| Group | Models | Why they belong there |",
        "|---|---|---|",
    ]

    grouped = defaultdict(list)
    reasons = {}
    for item in groups:
        grouped[item["group"]].append(item["display_model"])
        reasons[item["group"]] = item["group_reason"]
    group_order = [
        "Broad pass leader",
        "Strong but narrow exactness",
        "Near-miss operators",
        "Brittle / low-coverage",
    ]
    for group in group_order:
        if group in grouped:
            lines.append(f"| {group} | {', '.join(grouped[group])} | {reasons[group]} |")

    lines.extend(
        [
            "",
            "## Model Summary",
            "",
            "| Model | Exact Attempts | Queries With Any Exact | Stable Exact Queries | Mean Score | Mean Cell Accuracy | Dominant Non-Exact Failure Mode |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in model_summary:
        lines.append(
            f"| {item['display_model']} | {item['exact_attempts']}/30 | {item['exact_query_coverage_any']}/10 | "
            f"{item['stable_exact_queries']}/10 | {item['mean_score']:.3f} | "
            f"{item['mean_aligned_cell_accuracy']:.3f} | {item['dominant_non_exact_failure_mode']} |"
        )

    lines.extend(
        [
            "",
            "## Query-by-Query Failure Points",
            "",
            "| Query | Focus | Exact Attempts | Mean Score | Top failure points |",
            "|---|---|---:|---:|---|",
        ]
    )
    for case in case_summary:
        issue_text = "; ".join(
            f"{issue['attempts_with_issue']}/{case['total_attempts']}: {issue['issue_label']}"
            for issue in case["top_issues"]
        )
        lines.append(
            f"| {case['query']} | {case['short_name']} | {case['exact_attempts']}/{case['total_attempts']} | {case['mean_score']:.3f} | {issue_text} |"
        )

    lines.extend(["", "## Short Notes", ""])
    for case in case_summary:
        lines.append(
            f"- **{case['query']} {case['short_name']}**: {case['exact_attempts']}/{case['total_attempts']} exact, "
            f"dominant non-exact failure mode `{case['dominant_non_exact_failure_mode']}`. "
            f"Primary family: `{case['primary_failure_family']}`."
        )
        for issue in case["top_issues"]:
            lines.append(
                f"Issue: {issue['attempts_with_issue']}/{case['total_attempts']} attempts. {issue['issue_label']} "
                f"Example models: {issue['example_models']}."
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: pass1_analysis.py <results_dir>", file=sys.stderr)
        return 2

    results_dir = Path(sys.argv[1]).resolve()
    if not (results_dir / "detailed_results.csv").exists():
        print(f"missing detailed_results.csv in {results_dir}", file=sys.stderr)
        return 1

    repo_root = results_dir.parent.parent
    if not (repo_root / "benchmark_cases.jsonl").exists():
        print(f"missing benchmark_cases.jsonl in repo root inferred from {results_dir}", file=sys.stderr)
        return 1

    out_dir = results_dir / "pass1_analysis"
    out_dir.mkdir(exist_ok=True)

    case_meta, _gold = load_metadata(repo_root)
    rows = load_rows(results_dir)
    model_summary, case_summary, model_query_rows = build_summaries(rows, case_meta)
    family_scores = compute_family_scores(model_query_rows, case_meta)
    model_groups = assign_model_groups(model_summary, model_query_rows)
    failure_point_rows = build_failure_point_rows(case_summary)

    write_csv(
        out_dir / "pass1_model_summary.csv",
        model_summary,
        [
            "model",
            "display_model",
            "attempts",
            "exact_attempts",
            "exact_attempt_rate",
            "exact_query_coverage_any",
            "stable_exact_queries",
            "partial_exact_queries",
            "stable_fail_queries",
            "mean_score",
            "mean_aligned_cell_accuracy",
            "mean_row_set_correctness",
            "mean_numeric_correctness",
            "mean_sort_correctness",
            "row_count_mismatch_rate",
            "mean_wall_s",
            "mean_gen_tps",
            "exact",
            "order_only",
            "type_only",
            "same_count_wrong_values",
            "row_count_mismatch",
            "column_error",
            "invalid_json_or_error",
            "dominant_failure_mode",
            "dominant_non_exact_failure_mode",
        ],
    )
    write_csv(
        out_dir / "pass1_case_summary.csv",
        [
            {
                key: value
                for key, value in row.items()
                if key not in {"top_issues"}
            }
            for row in case_summary
        ],
        [
            "case_id",
            "query",
            "short_name",
            "prompt",
            "run_benchmark_id",
            "metadata_benchmark_id",
            "metadata_matches_run",
            "primary_failure_family",
            "total_attempts",
            "exact_attempts",
            "exact_attempt_rate",
            "exact_models_any",
            "exact_models_stable",
            "mean_score",
            "mean_aligned_cell_accuracy",
            "row_count_mismatch_attempts",
            "same_count_wrong_attempts",
            "order_only_attempts",
            "type_only_attempts",
            "column_error_attempts",
            "invalid_json_or_error_attempts",
            "dominant_failure_mode",
            "dominant_non_exact_failure_mode",
        ],
    )
    write_csv(
        out_dir / "pass1_model_query_matrix.csv",
        model_query_rows,
        [
            "model",
            "display_model",
            "case_id",
            "query",
            "short_name",
            "exact_attempts",
            "exact_rate",
            "mean_score",
            "mean_aligned_cell_accuracy",
            "dominant_failure_mode",
            "dominant_non_exact_failure_mode",
            "stable_outcome",
        ],
    )
    write_csv(
        out_dir / "pass1_family_scores.csv",
        family_scores,
        ["model", "display_model", "family", "mean_score", "mean_exact_rate"],
    )
    write_csv(
        out_dir / "pass1_model_groups.csv",
        model_groups,
        [
            "model",
            "display_model",
            "group",
            "group_reason",
            "structural_score",
            "analytical_score",
            "sorting_score",
            "exact_attempts",
            "stable_exact_queries",
            "partial_exact_queries",
            "stable_fail_queries",
            "mean_score",
        ],
    )
    write_csv(
        out_dir / "pass1_query_failure_points.csv",
        failure_point_rows,
        [
            "case_id",
            "query",
            "short_name",
            "issue_code",
            "issue_label",
            "attempts_with_issue",
            "attempt_pct",
            "example_models",
        ],
    )

    render_visual_report(model_summary, case_summary, model_query_rows, family_scores, out_dir / "pass1_visual_report")
    render_model_groups(model_groups, out_dir / "pass1_model_groups")
    write_notes(out_dir / "pass1_analysis_notes.md", model_summary, case_summary, model_groups, results_dir)

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
