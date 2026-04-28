#!/usr/bin/env python3
import csv
import json
import math
import os
import re
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
warnings.filterwarnings("ignore", message="Unable to import Axes3D.*")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


PAGE_BG = "#102A43"
PANEL_BG = "#173B59"
GRID = "#3B6386"
TEXT = "#F4FAFF"
BLUE_DARK = "#0F4C81"
BLUE = "#2F80ED"
BLUE_LIGHT = "#89C8FF"
BLUE_PALE = "#D9F0FF"
BLUE_MID = "#4DA3FF"
FAIL_LIGHT = "#5D8CB8"
FAIL_PALE = "#B9D8F2"

QUERY_LABELS = {
    "pass2.query1": "Q1\n4-table\ninner",
    "pass2.query2": "Q2\nsnowflake\nleft join",
    "pass2.query3": "Q3\nvariant\nfull outer",
    "pass2.query4": "Q4\ncondition\nimpact agg",
    "pass2.query5": "Q5\ngene\nVAF agg",
    "pass2.query6": "Q6\ntissue\nchain agg",
    "pass2.query7": "Q7\nsample\nhigh impact",
    "pass2.query8": "Q8\ngene\nread agg",
    "pass2.query9": "Q9\npathway\ndecision",
    "pass2.query10": "Q10\nsample\ncoverage",
}

QUERY_SHORT_NAMES = {
    "pass2.query1": "Four-table inner join",
    "pass2.query2": "Full snowflake left join",
    "pass2.query3": "Variant full outer join",
    "pass2.query4": "Condition-impact aggregate",
    "pass2.query5": "Gene VAF aggregate",
    "pass2.query6": "Tissue complete-chain aggregate",
    "pass2.query7": "Sample high-impact screen",
    "pass2.query8": "Gene read-quality aggregate",
    "pass2.query9": "Pathway decision summary",
    "pass2.query10": "Sample coverage screen",
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
    "Strong exact converters": BLUE_LIGHT,
    "Partial-credit joiners": BLUE_MID,
    "Brittle / low-coverage": BLUE_DARK,
}

ISSUE_LABELS = {
    "q1_kept_call6": "Kept call_id 6 / V5 even though the complete four-table inner join should remove it.",
    "q1_kept_call8": "Kept call_id 8 / S999 even though the sample dimension is missing.",
    "q1_kept_call9": "Kept call_id 9 / V999 even though the variant/gene chain is incomplete.",
    "q1_dropped_valid_calls": "Dropped one or more valid complete-chain calls.",
    "q1_wrong_gene_or_impact": "Mapped a valid call to the wrong gene or impact value.",
    "q2_dropped_fact_rows": "Did not preserve all nine fact rows in the left-join snowflake.",
    "q2_wrong_gene_mapping": "Mapped matched variants to the wrong gene symbol or dropped a valid gene symbol.",
    "q2_bad_sample_nulls": "Filled sample attributes for S999 instead of leaving dimension fields null.",
    "q2_bad_chain_nulls": "Failed to leave gene_symbol null for incomplete V5/V999 chain rows.",
    "q3_missing_v6": "Dropped the variant-only V6 row from the full outer join.",
    "q3_missing_v999": "Dropped the fact-only V999 row from the full outer join.",
    "q3_bad_coalesced_key": "Failed to preserve the coalesced variant_id key for fact-only or matched rows.",
    "q3_wrong_impact": "Assigned an incorrect impact value in the full outer result.",
    "q4_wrong_group_set": "Returned the wrong condition-impact group set.",
    "q4_control_high_wrong": "Miscomputed the control/high bucket, especially the two-call count and average.",
    "q4_wrong_impact_bucket": "Used variant class or leaked an unmatched impact bucket instead of grouping by impact.",
    "q4_avg_wrong": "Computed one or more condition-impact average qualities from the wrong row set.",
    "q5_wrong_vaf": "Computed average VAF from the wrong numerator/denominator or row set.",
    "q5_leaked_unmatched_gene": "Included incomplete-chain or non-gold genes such as NDHT/PGR1B.",
    "q5_dropped_gene": "Dropped one of the expected genes NDHB, NDHK, or PGR5.",
    "q5_wrong_max_qual": "Computed max_qual from the wrong rows.",
    "q6_grouped_by_condition": "Grouped by condition instead of tissue.",
    "q6_included_root": "Included root/S5 even though complete inner joins should remove it.",
    "q6_wrong_distinct_genes": "Computed distinct gene counts from the wrong join grain.",
    "q6_wrong_expr_average": "Computed avg_expr_ndhb over samples instead of complete-chain joined calls.",
    "q7_missed_zero_alt_high": "Missed the zero-alt high-impact call for S4.",
    "q7_counted_non_high": "Counted non-high or incomplete rows as high-impact calls, often inflating S3.",
    "q7_missing_preserved_sample": "Dropped zero-call or zero-high samples from the sample-preserving output.",
    "q7_wrong_alt_average": "Averaged alt_reads over the wrong subset of rows.",
    "q8_used_gene_id": "Returned gene IDs instead of gene symbols.",
    "q8_leaked_unmatched_gene": "Included incomplete-chain genes that should not appear.",
    "q8_wrong_alt_total": "Computed total_alt_reads from the wrong row set.",
    "q8_wrong_avg_qual": "Computed avg_qual from the wrong row set.",
    "q8_dropped_gene": "Dropped one of the expected gene symbols.",
    "q9_wrong_group_set": "Returned the wrong condition-pathway group set.",
    "q9_leaked_incomplete_pathway": "Included incomplete-chain or non-gold pathways.",
    "q9_wrong_vaf": "Computed mean VAF from the wrong row set.",
    "q9_wrong_counts": "Miscomputed call_count or distinct_samples.",
    "q10_missing_s5": "Dropped zero-call sample S5 from the sample-preserving coverage screen.",
    "q10_wrong_total_calls": "Miscomputed total fact calls per sample.",
    "q10_wrong_chain_counts": "Misclassified complete vs incomplete chain calls.",
}


def as_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def as_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def numeric_close(value, expected, tol=0.001) -> bool:
    if value is None and expected is None:
        return True
    got = safe_float(value)
    if got is None or expected is None:
        return False
    return abs(got - expected) <= tol


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


def case_sort_key(case_id: str) -> int:
    return int(case_id.split("query")[1])


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


def dominant_non_exact_mode(modes: Counter) -> str:
    non_exact = Counter({mode: count for mode, count in modes.items() if mode != "exact"})
    return non_exact.most_common(1)[0][0] if non_exact else "none"


def load_metadata(repo_root: Path):
    case_meta = {}
    with (repo_root / "benchmark_cases.jsonl").open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            if item["case_id"].startswith("pass2."):
                case_meta[item["case_id"]] = item

    gold = {}
    with (repo_root / "gold_answers.jsonl").open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            if item["case_id"].startswith("pass2."):
                gold[item["case_id"]] = item

    return case_meta, gold


def load_rows(results_dir: Path) -> list[dict]:
    rows = []
    with (results_dir / "detailed_results.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["pass"] != "2":
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


def rows_by_index(rows, index=0):
    out = {}
    for row in rows:
        if isinstance(row, list) and len(row) > index:
            out[row[index]] = row
    return out


def rows_by_pair(rows, first=0, second=1):
    out = {}
    for row in rows:
        if isinstance(row, list) and len(row) > max(first, second):
            out[(row[first], row[second])] = row
    return out


def row_ids(rows):
    return {row[0] for row in rows if isinstance(row, list) and row}


def detect_issue_flags(case_id: str, pred_rows: list, gold_rows: list, row: dict) -> list[str]:
    flags = []
    pred_rows = coerce_numeric_strings(pred_rows)
    gold_rows = coerce_numeric_strings(gold_rows)

    if case_id == "pass2.query1":
        pred = rows_by_index(pred_rows, 0)
        gold = rows_by_index(gold_rows, 0)
        ids = set(pred)
        if 6 in ids or "6" in ids:
            flags.append("q1_kept_call6")
        if 8 in ids or "8" in ids:
            flags.append("q1_kept_call8")
        if 9 in ids or "9" in ids:
            flags.append("q1_kept_call9")
        if not set(gold).issubset(ids):
            flags.append("q1_dropped_valid_calls")
        for call_id, gold_row in gold.items():
            pred_row = pred.get(call_id) or pred.get(str(call_id))
            if pred_row and pred_row[3:5] != gold_row[3:5]:
                flags.append("q1_wrong_gene_or_impact")
                break

    elif case_id == "pass2.query2":
        pred = rows_by_index(pred_rows, 0)
        if len(pred_rows) != 9:
            flags.append("q2_dropped_fact_rows")
        expected_genes = {1: "NDHB", 2: "NDHB", 3: "NDHB", 4: "NDHK", 5: "PGR5", 6: None, 7: "NDHK", 8: "NDHB", 9: None}
        for call_id, expected in expected_genes.items():
            pred_row = pred.get(call_id) or pred.get(str(call_id))
            if pred_row is not None and pred_row[5] != expected:
                flags.append("q2_wrong_gene_mapping")
                break
        row8 = pred.get(8) or pred.get("8")
        if row8 is not None and row8[1:4] != ["S999", None, None]:
            flags.append("q2_bad_sample_nulls")
        for call_id in [6, 9]:
            pred_row = pred.get(call_id) or pred.get(str(call_id))
            if pred_row is not None and pred_row[5] is not None:
                flags.append("q2_bad_chain_nulls")
                break

    elif case_id == "pass2.query3":
        variant_ids = row_ids(pred_rows)
        if "V6" not in variant_ids:
            flags.append("q3_missing_v6")
        if "V999" not in variant_ids:
            flags.append("q3_missing_v999")
        if None in variant_ids:
            flags.append("q3_bad_coalesced_key")
        for pred_row in pred_rows:
            if len(pred_row) < 4:
                continue
            if pred_row[0] == "V999" and pred_row[3] is not None:
                flags.append("q3_wrong_impact")
            if pred_row[0] in {"V1", "V2", "V3", "V4", "V5", "V6"}:
                expected = {"V1": "moderate", "V2": "high", "V3": "high", "V4": "low", "V5": "modifier", "V6": "moderate"}[pred_row[0]]
                if pred_row[3] != expected:
                    flags.append("q3_wrong_impact")
                    break

    elif case_id == "pass2.query4":
        pred = rows_by_pair(pred_rows, 0, 1)
        expected = {
            ("control", "high"): (2, 84.0),
            ("control", "moderate"): (1, 95.0),
            ("drought", "low"): (1, 70.0),
            ("drought", "modifier"): (1, 92.0),
            ("high_light", "high"): (1, 87.0),
            ("high_light", "moderate"): (1, 99.0),
        }
        if set(pred) != set(expected):
            flags.append("q4_wrong_group_set")
        if ("control", "high") not in pred or pred[("control", "high")][2] != 2 or not numeric_close(pred[("control", "high")][3], 84.0):
            flags.append("q4_control_high_wrong")
        if any(key[1] in {"SNV", "indel", "chloroplast_NDH_complex"} for key in pred):
            flags.append("q4_wrong_impact_bucket")
        for key, (count, avg_qual) in expected.items():
            if key in pred:
                if pred[key][2] != count or not numeric_close(pred[key][3], avg_qual):
                    flags.append("q4_avg_wrong")
                    break

    elif case_id == "pass2.query5":
        pred = rows_by_index(pred_rows, 0)
        expected = {"PGR5": (0.5, 70), "NDHB": (0.459, 99), "NDHK": (0.25, 88)}
        if not set(expected).issubset(set(pred)):
            flags.append("q5_dropped_gene")
        if any(gene not in expected for gene in pred):
            flags.append("q5_leaked_unmatched_gene")
        for gene, (avg_vaf, max_qual) in expected.items():
            if gene in pred:
                if not numeric_close(pred[gene][1], avg_vaf):
                    flags.append("q5_wrong_vaf")
                if pred[gene][2] != max_qual:
                    flags.append("q5_wrong_max_qual")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass2.query6":
        pred = rows_by_index(pred_rows, 0)
        if any(key in pred for key in ["control", "drought", "high_light"]):
            flags.append("q6_grouped_by_condition")
        if "root" in pred:
            flags.append("q6_included_root")
        expected = {"mature_leaf": (2, 750.0), "young_leaf": (2, 500.0)}
        for tissue, (distinct_genes, avg_expr) in expected.items():
            if tissue not in pred or pred[tissue][1] != distinct_genes:
                flags.append("q6_wrong_distinct_genes")
            if tissue not in pred or not numeric_close(pred[tissue][2], avg_expr):
                flags.append("q6_wrong_expr_average")
        if set(pred) != set(expected):
            flags.append("q6_wrong_distinct_genes")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass2.query7":
        pred = rows_by_index(pred_rows, 0)
        expected_samples = {"S1", "S2", "S3", "S4", "S5"}
        if not expected_samples.issubset(set(pred)):
            flags.append("q7_missing_preserved_sample")
        row4 = pred.get("S4")
        if row4 is None or row4[2] != 1 or not numeric_close(row4[3], 0.0):
            flags.append("q7_missed_zero_alt_high")
        row3 = pred.get("S3")
        if row3 is not None and row3[2] != 0:
            flags.append("q7_counted_non_high")
        for sample, expected_avg in {"S1": 28.0, "S2": 10.0, "S4": 0.0}.items():
            if sample in pred and not numeric_close(pred[sample][3], expected_avg):
                flags.append("q7_wrong_alt_average")
                break

    elif case_id == "pass2.query8":
        pred = rows_by_index(pred_rows, 0)
        expected = {"NDHB": (54, 85.25, 28), "NDHK": (10, 84.0, 10), "PGR5": (9, 70.0, 9)}
        if any(str(gene).startswith("G") for gene in pred):
            flags.append("q8_used_gene_id")
        if any(gene not in expected for gene in pred):
            flags.append("q8_leaked_unmatched_gene")
        if not set(expected).issubset(set(pred)):
            flags.append("q8_dropped_gene")
        for gene, (total_alt, avg_qual, max_alt) in expected.items():
            if gene in pred:
                if pred[gene][1] != total_alt or pred[gene][3] != max_alt:
                    flags.append("q8_wrong_alt_total")
                if not numeric_close(pred[gene][2], avg_qual):
                    flags.append("q8_wrong_avg_qual")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass2.query9":
        pred = rows_by_pair(pred_rows, 0, 1)
        expected = {
            ("control", "chloroplast_NDH_complex"): (3, 0.167, 2),
            ("drought", "cyclic_electron_flow"): (1, 0.5, 1),
            ("high_light", "chloroplast_NDH_complex"): (2, 0.7, 1),
        }
        if set(pred) != set(expected):
            flags.append("q9_wrong_group_set")
        if any(key not in expected for key in pred):
            flags.append("q9_leaked_incomplete_pathway")
        for key, (call_count, mean_vaf, distinct_samples) in expected.items():
            if key in pred:
                if pred[key][2] != call_count or pred[key][4] != distinct_samples:
                    flags.append("q9_wrong_counts")
                if not numeric_close(pred[key][3], mean_vaf):
                    flags.append("q9_wrong_vaf")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass2.query10":
        pred = rows_by_index(pred_rows, 0)
        expected = {
            "S1": (2, 2, 0),
            "S2": (3, 2, 1),
            "S3": (2, 1, 1),
            "S4": (1, 1, 0),
            "S5": (0, 0, 0),
        }
        if "S5" not in pred:
            flags.append("q10_missing_s5")
        for sample, (total, complete, incomplete) in expected.items():
            if sample in pred:
                if pred[sample][2] != total:
                    flags.append("q10_wrong_total_calls")
                if pred[sample][3] != complete or pred[sample][4] != incomplete:
                    flags.append("q10_wrong_chain_counts")
        flags = list(dict.fromkeys(flags))

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
    case_ids = sorted({r["case_id"] for r in rows}, key=case_sort_key)
    for model, items in by_model.items():
        exact_attempts = sum(as_bool(r["exact_match"]) for r in items)
        exact_query_coverage_any = sum(any(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) for case_id in case_ids)
        stable_exact_queries = sum(sum(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) == 3 for case_id in case_ids)
        partial_exact_queries = sum(0 < sum(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) < 3 for case_id in case_ids)
        stable_fail_queries = sum(sum(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) == 0 for case_id in case_ids)
        modes = Counter(r["_failure_mode"] for r in items)
        model_summary.append(
            {
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
                "dominant_non_exact_failure_mode": dominant_non_exact_mode(modes),
            }
        )

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
            top_issues.append(
                {
                    "issue_code": issue,
                    "issue_label": ISSUE_LABELS[issue],
                    "attempts_with_issue": count,
                    "attempt_pct": count / len(items),
                    "example_models": ", ".join(sorted(issue_models[issue])[:4]),
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
                "dominant_non_exact_failure_mode": dominant_non_exact_mode(modes),
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
                "dominant_non_exact_failure_mode": dominant_non_exact_mode(modes),
                "stable_outcome": "stable_exact" if exact_attempts == 3 else ("partial_exact" if exact_attempts > 0 else "stable_fail"),
            }
        )

    return model_summary, case_summary, model_query_rows


def compute_family_scores(model_query_rows: list[dict], case_meta: dict) -> list[dict]:
    family_lookup = {row["case_id"]: case_meta[row["case_id"]]["metadata"]["failure_family_primary"] for row in model_query_rows}
    acc = defaultdict(list)
    for row in model_query_rows:
        acc[(row["model"], family_lookup[row["case_id"]])].append(row)

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
        structural_cases = ["pass2.query1", "pass2.query2", "pass2.query3", "pass2.query6", "pass2.query10"]
        analytical_cases = ["pass2.query4", "pass2.query5", "pass2.query7", "pass2.query8", "pass2.query9"]
        structural_score = mean(matrix[model][case]["mean_score"] for case in structural_cases)
        analytical_score = mean(matrix[model][case]["mean_score"] for case in analytical_cases)

        if item["exact_attempts"] >= 10 or item["exact_query_coverage_any"] >= 4:
            group = "Broad pass leader"
            reason = "Converted exact answers across four query types and kept high partial credit on the zero-exact aggregation tasks."
        elif item["exact_attempts"] >= 6 and item["mean_score"] >= 0.70:
            group = "Strong exact converters"
            reason = "Solved the easier outer-join cases reliably but did not convert the VAF, pathway, or high-impact aggregates."
        elif item["mean_score"] >= 0.60 or item["exact_attempts"] > 0:
            group = "Partial-credit joiners"
            reason = "Frequently found much of the row set, but row-count, chain-null, or aggregate-grain mistakes prevented exact conversion."
        else:
            group = "Brittle / low-coverage"
            reason = "Low exact coverage plus repeated row-count, chain traversal, or numeric aggregation failures."

        groups.append(
            {
                "model": model,
                "display_model": item["display_model"],
                "group": group,
                "group_reason": reason,
                "structural_score": structural_score,
                "analytical_score": analytical_score,
                "exact_attempts": item["exact_attempts"],
                "stable_exact_queries": item["stable_exact_queries"],
                "partial_exact_queries": item["partial_exact_queries"],
                "stable_fail_queries": item["stable_fail_queries"],
                "mean_score": item["mean_score"],
            }
        )

    group_order = {
        "Broad pass leader": 0,
        "Strong exact converters": 1,
        "Partial-credit joiners": 2,
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

    family_order = ["snowflake_traversal", "outer_join_coverage", "aggregation_numeric", "decision_support"]
    family_short = {
        "snowflake_traversal": "Snowflake\ntraversal",
        "outer_join_coverage": "Outer\ncoverage",
        "aggregation_numeric": "Numeric\nagg",
        "decision_support": "Decision\nsupport",
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
        "AIBioBench Pass 2, Latest Run: Snowflake Joins, Aggregates, and Failure Shape",
        fontsize=24,
        fontweight="bold",
        color=TEXT,
    )

    ax1 = fig.add_subplot(gs[0, 0])
    style_axis(ax1)
    y = list(range(len(model_summary)))
    exacts = [m["exact_attempts"] for m in model_summary]
    colors = [BLUE_PALE if x >= 10 else BLUE_LIGHT if x >= 6 else BLUE_MID if x >= 2 else BLUE_DARK for x in exacts]
    bars = ax1.barh(y, exacts, color=colors)
    ax1.set_yticks(y, model_labels)
    ax1.invert_yaxis()
    ax1.set_xlim(0, 30)
    ax1.set_xlabel("Exact attempts out of 30")
    ax1.set_title("Exact Match Conversion by Model", fontweight="bold")
    ax1.grid(axis="x", color=GRID, linewidth=1)
    for bar, item in zip(bars, model_summary):
        ax1.text(
            min(bar.get_width() + 0.35, 29.4),
            bar.get_y() + bar.get_height() / 2,
            f"{item['exact_attempts']}/30  |  {item['exact_query_coverage_any']}/10 queries",
            va="center",
            color=TEXT,
            fontsize=9,
        )

    score_cmap = LinearSegmentedColormap.from_list("score_blues", [BLUE_DARK, BLUE, BLUE_LIGHT, BLUE_PALE])
    ax2 = fig.add_subplot(gs[0, 1])
    style_axis(ax2)
    im1 = ax2.imshow(exact_matrix, aspect="auto", cmap=score_cmap, vmin=0, vmax=1)
    ax2.set_xticks(range(len(cases)), case_labels)
    ax2.set_yticks(range(len(models)), model_labels)
    ax2.set_title("Exact Rate by Model and Query (3 repeats)", fontweight="bold")
    for i in range(len(models)):
        for j in range(len(cases)):
            val = exact_matrix[i][j]
            ax2.text(j, i, f"{val:.0%}", ha="center", va="center", color=PAGE_BG if val >= 0.67 else TEXT, fontsize=8, fontweight="bold" if val > 0 else "normal")
    cbar1 = fig.colorbar(im1, ax=ax2, fraction=0.028, pad=0.02)
    cbar1.ax.tick_params(labelsize=8, colors=TEXT)
    cbar1.outline.set_edgecolor(GRID)

    ax3 = fig.add_subplot(gs[1, 0])
    style_axis(ax3)
    im2 = ax3.imshow(score_matrix, aspect="auto", cmap=score_cmap, vmin=0, vmax=1)
    ax3.set_xticks(range(len(cases)), case_labels)
    ax3.set_yticks(range(len(models)), model_labels)
    ax3.set_title("Mean Score by Model and Query", fontweight="bold")
    for i in range(len(models)):
        for j in range(len(cases)):
            val = score_matrix[i][j]
            ax3.text(j, i, f"{val:.2f}", ha="center", va="center", color=PAGE_BG if val >= 0.83 else TEXT, fontsize=8, fontweight="bold" if val >= 0.95 else "normal")
    cbar2 = fig.colorbar(im2, ax=ax3, fraction=0.028, pad=0.02)
    cbar2.ax.tick_params(labelsize=8, colors=TEXT)
    cbar2.outline.set_edgecolor(GRID)

    ax4 = fig.add_subplot(gs[1, 1])
    style_axis(ax4)
    mode_order = [
        ("exact", "Exact", BLUE_PALE),
        ("order_only", "Right rows, wrong order", BLUE_LIGHT),
        ("type_only", "Type only", BLUE_MID),
        ("column_error", "Column/schema error", FAIL_PALE),
        ("same_count_wrong_values", "Same count, wrong values", FAIL_LIGHT),
        ("row_count_mismatch", "Wrong row count", BLUE_DARK),
        ("invalid_json_or_error", "Invalid JSON/error", TEXT),
    ]
    bottoms = [0] * len(cases)
    for mode, label, color in mode_order:
        vals = [sum(1 for row in model_query_rows if row["case_id"] == case and row["dominant_failure_mode"] == mode) for case in cases]
        ax4.bar(range(len(cases)), vals, bottom=bottoms, label=label, color=color, edgecolor=PANEL_BG)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax4.set_xticks(range(len(cases)), [c.split(".")[-1].upper() for c in cases])
    ax4.set_ylim(0, len(models))
    ax4.set_ylabel("Models")
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
                ax5.text(j, i, f"{val:.2f}", ha="center", va="center", color=PAGE_BG if val >= 0.83 else TEXT, fontsize=8)
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
    ax6.set_ylabel("Rate / score")
    ax6.set_title("Which Pass-2 Questions Broke the Models", fontweight="bold")
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
    fig.suptitle("AIBioBench Pass 2: Model Grouping by Structural vs Analytical Performance", fontsize=22, fontweight="bold", color=TEXT)

    ax1 = fig.add_subplot(gs[0, 0])
    style_axis(ax1)
    for item in groups:
        color = MODEL_GROUP_COLORS[item["group"]]
        ax1.scatter(item["structural_score"], item["analytical_score"], s=120 + item["exact_attempts"] * 28, color=color, edgecolors=BLUE_PALE, linewidth=1.2, alpha=0.95)
        ax1.annotate(wrap_display_name(item["display_model"]), (item["structural_score"], item["analytical_score"]), xytext=(7, 6), textcoords="offset points", color=TEXT, fontsize=9)
    ax1.set_xlabel("Structural snowflake tasks mean score\n(Q1, Q2, Q3, Q6, Q10)")
    ax1.set_ylabel("Analytical aggregate tasks mean score\n(Q4, Q5, Q7, Q8, Q9)")
    ax1.set_xlim(0, 1.03)
    ax1.set_ylim(0, 1.03)
    ax1.set_title("Pass-2 separation comes from full-chain exactness and aggregate grain", fontweight="bold")
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
        ax2.text(9.95, idx, item["group"], ha="right", va="center", color=TEXT, fontsize=8)
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
    exact_zero = [case["query"] for case in case_summary if case["exact_attempts"] == 0]
    exact_queries = [case["query"] for case in case_summary if case["exact_attempts"] > 0]
    model_count = len(model_summary)
    total_attempts = sum(case["total_attempts"] for case in case_summary)
    exact_zero_text = ", ".join(exact_zero) if exact_zero else "none"
    exact_query_text = ", ".join(exact_queries) if exact_queries else "none"
    lines = [
        "# AIBioBench Pass 2 Analysis",
        "",
        f"Run analyzed: `{results_dir.name}`",
        "",
        f"Pass 2 contains ten medium SQL tasks, each repeated three times across {model_count} models. Compared with pass 1, the task pressure shifts from basic joins to full snowflake traversal, full outer join coverage, VAF arithmetic, and sample-preserving coverage counts.",
        "",
        "## Headline Findings",
        "",
        f"- **{model_summary[0]['display_model']}** led pass 2 with {model_summary[0]['exact_attempts']}/30 exact attempts and exact coverage on {model_summary[0]['exact_query_coverage_any']}/10 questions.",
        f"- Exact matches were sparse: only {sum(case['exact_attempts'] for case in case_summary)}/{total_attempts} attempts were exact. Exact answers appeared on **{exact_query_text}**; zero-exact questions were **{exact_zero_text}**.",
        "- The suite mostly broke models on chain completeness, aggregate grain, and preserving the right side of outer joins.",
        "- High partial scores still occurred on Q2/Q10, but exact conversion failed when null handling or complete-vs-incomplete chain counts were off.",
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
    for group in ["Broad pass leader", "Strong exact converters", "Partial-credit joiners", "Brittle / low-coverage"]:
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
            f"| {item['display_model']} | {item['exact_attempts']}/30 | {item['exact_query_coverage_any']}/10 | {item['stable_exact_queries']}/10 | "
            f"{item['mean_score']:.3f} | {item['mean_aligned_cell_accuracy']:.3f} | {item['dominant_non_exact_failure_mode']} |"
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
            f"- **{case['query']} {case['short_name']}**: {case['exact_attempts']}/{case['total_attempts']} exact, dominant non-exact failure mode `{case['dominant_non_exact_failure_mode']}`. Primary family: `{case['primary_failure_family']}`."
        )
        for issue in case["top_issues"]:
            lines.append(
                f"Issue: {issue['attempts_with_issue']}/{case['total_attempts']} attempts. {issue['issue_label']} Example models: {issue['example_models']}."
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: pass2_analysis.py <results_dir>", file=sys.stderr)
        return 2

    results_dir = Path(sys.argv[1]).resolve()
    if not (results_dir / "detailed_results.csv").exists():
        print(f"missing detailed_results.csv in {results_dir}", file=sys.stderr)
        return 1

    repo_root = results_dir.parent.parent
    if not (repo_root / "benchmark_cases.jsonl").exists():
        print(f"missing benchmark_cases.jsonl in repo root inferred from {results_dir}", file=sys.stderr)
        return 1

    out_dir = results_dir / "pass2_analysis"
    out_dir.mkdir(exist_ok=True)

    case_meta, _gold = load_metadata(repo_root)
    rows = load_rows(results_dir)
    model_summary, case_summary, model_query_rows = build_summaries(rows, case_meta)
    family_scores = compute_family_scores(model_query_rows, case_meta)
    model_groups = assign_model_groups(model_summary, model_query_rows)
    failure_point_rows = build_failure_point_rows(case_summary)

    write_csv(
        out_dir / "pass2_model_summary.csv",
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
        out_dir / "pass2_case_summary.csv",
        [{key: value for key, value in row.items() if key not in {"top_issues"}} for row in case_summary],
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
        out_dir / "pass2_model_query_matrix.csv",
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
    write_csv(out_dir / "pass2_family_scores.csv", family_scores, ["model", "display_model", "family", "mean_score", "mean_exact_rate"])
    write_csv(
        out_dir / "pass2_model_groups.csv",
        model_groups,
        [
            "model",
            "display_model",
            "group",
            "group_reason",
            "structural_score",
            "analytical_score",
            "exact_attempts",
            "stable_exact_queries",
            "partial_exact_queries",
            "stable_fail_queries",
            "mean_score",
        ],
    )
    write_csv(
        out_dir / "pass2_query_failure_points.csv",
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

    render_visual_report(model_summary, case_summary, model_query_rows, family_scores, out_dir / "pass2_visual_report")
    render_model_groups(model_groups, out_dir / "pass2_model_groups")
    write_notes(out_dir / "pass2_analysis_notes.md", model_summary, case_summary, model_groups, results_dir)

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
