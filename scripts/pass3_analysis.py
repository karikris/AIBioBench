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
    "pass3.query1": "Q1\njoin-status\naudit",
    "pass3.query2": "Q2\ntissue-gene\nVAF agg",
    "pass3.query3": "Q3\ngene\ncoverage",
    "pass3.query4": "Q4\nhigh-impact\nsummary",
    "pass3.query5": "Q5\ngenotype\nclasses",
    "pass3.query6": "Q6\ntissue-gene\nranking",
    "pass3.query7": "Q7\nanti-join\naudit",
    "pass3.query8": "Q8\nrole\ndecision",
    "pass3.query9": "Q9\nfailure-family\naudit",
    "pass3.query10": "Q10\ndecision\npriority",
}

QUERY_SHORT_NAMES = {
    "pass3.query1": "Join-status classification",
    "pass3.query2": "Tissue-gene VAF aggregate",
    "pass3.query3": "Gene coverage audit",
    "pass3.query4": "High-impact condition summary",
    "pass3.query5": "Sample genotype classes",
    "pass3.query6": "Tissue-gene dense ranking",
    "pass3.query7": "Unused dimension anti-join",
    "pass3.query8": "Gene-role decision summary",
    "pass3.query9": "Failure-family audit",
    "pass3.query10": "Decision-priority candidate table",
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
    "Single-skill exact converters": BLUE_LIGHT,
    "Partial-credit operators": BLUE_MID,
    "Brittle / low-coverage": BLUE_DARK,
}

ISSUE_LABELS = {
    "q1_call6_status_wrong": "Misclassified call_id 6 / V5; it should be MISSING_GENE.",
    "q1_call8_status_wrong": "Misclassified call_id 8 / S999; it should be MISSING_SAMPLE.",
    "q1_call9_status_wrong": "Misclassified call_id 9 / V999; it should be MISSING_VARIANT.",
    "q1_complete_chain_status_wrong": "Misclassified one or more complete-chain calls.",
    "q2_wrong_group_set": "Returned the wrong tissue-gene group set for complete-chain matched rows.",
    "q2_leaked_incomplete_or_root": "Leaked incomplete-chain or non-gold tissue/gene groups such as root/NDHT.",
    "q2_wrong_counts_or_alt": "Miscomputed call_count or sum_alt_reads.",
    "q2_wrong_vaf": "Computed avg_vaf from the wrong numerator/denominator or row set.",
    "q2_wrong_max_qual": "Computed max_qual from the wrong rows.",
    "q3_missing_zero_call_gene": "Dropped zero-call genes NDHT or PGR1B from the gene-preserving audit.",
    "q3_wrong_observed_count": "Miscomputed observed_call_count for one or more genes.",
    "q3_wrong_total_alt": "Miscomputed total_alt_reads for one or more genes.",
    "q3_leaked_unknown_gene": "Included a non-gold gene such as G999.",
    "q4_included_non_high_condition": "Included a condition that has no high-impact joined calls, usually drought.",
    "q4_control_bucket_wrong": "Miscomputed the control high-impact bucket.",
    "q4_high_light_bucket_wrong": "Miscomputed the high_light high-impact bucket.",
    "q4_wrong_group_set": "Returned the wrong set of high-impact condition rows.",
    "q5_dropped_preserved_sample": "Dropped a sample from the sample-preserving genotype summary.",
    "q5_included_s999": "Included S999 even though sample_dim is the preserving table.",
    "q5_s2_nonref_wrong": "Miscomputed S2 heterozygous calls or non-reference mean quality.",
    "q5_counted_reference_or_wrong_class": "Counted reference calls or put genotypes into the wrong class.",
    "q6_wrong_group_set": "Returned the wrong tissue-gene group set before ranking.",
    "q6_leaked_root_or_incomplete": "Leaked root, incomplete-chain, or non-gold genes into the ranking.",
    "q6_wrong_totals_or_vaf": "Miscomputed total_alt_reads or avg_vaf.",
    "q6_wrong_rank": "Computed rank_in_tissue incorrectly.",
    "q7_object_type_labels_wrong": "Used dimension-table labels such as gene_dim/sample_dim instead of gene/sample/variant.",
    "q7_g4_reason_wrong": "Assigned the wrong reason to G4; it should be no_fact_calls_through_variants.",
    "q7_missing_expected_object": "Dropped or mislabeled one of G4, G5, S5, or V6 in the anti-join audit.",
    "q7_extra_object": "Included a non-gold unused object such as G999.",
    "q8_wrong_group_set": "Returned the wrong condition-gene_role groups.",
    "q8_leaked_reference_or_incomplete": "Leaked reference calls, incomplete chains, or non-gold roles into the non-reference summary.",
    "q8_wrong_counts": "Miscomputed non_reference_call_count.",
    "q8_wrong_vaf": "Computed mean_vaf from the wrong row set.",
    "q9_missing_condition_group": "Dropped one of UNMATCHED_SAMPLE, control, drought, or high_light.",
    "q9_wrong_complete_counts": "Miscomputed complete_chain_calls by condition group.",
    "q9_wrong_missing_status_counts": "Miscomputed missing_sample, missing_variant, or missing_gene counts.",
    "q10_wrong_gene_set": "Returned the wrong candidate gene set.",
    "q10_leaked_non_gold_gene": "Leaked a non-gold complete-chain candidate such as PGR1B.",
    "q10_wrong_vaf": "Computed avg_vaf from the wrong non-reference row set.",
    "q10_wrong_expression": "Mapped matched expression counts incorrectly.",
    "q10_wrong_decision_score": "Computed decision_score incorrectly from avg_vaf and matched expression.",
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
            if item["case_id"].startswith("pass3."):
                case_meta[item["case_id"]] = item

    gold = {}
    with (repo_root / "gold_answers.jsonl").open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            if item["case_id"].startswith("pass3."):
                gold[item["case_id"]] = item

    return case_meta, gold


def load_rows(results_dir: Path) -> list[dict]:
    rows = []
    with (results_dir / "detailed_results.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["pass"] != "3":
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


def detect_issue_flags(case_id: str, pred_rows: list, gold_rows: list, row: dict) -> list[str]:
    flags = []
    pred_rows = coerce_numeric_strings(pred_rows)
    gold_rows = coerce_numeric_strings(gold_rows)

    if case_id == "pass3.query1":
        pred = rows_by_index(pred_rows, 0)
        expected_status = {1: "COMPLETE_CHAIN", 2: "COMPLETE_CHAIN", 3: "COMPLETE_CHAIN", 4: "COMPLETE_CHAIN", 5: "COMPLETE_CHAIN", 6: "MISSING_GENE", 7: "COMPLETE_CHAIN", 8: "MISSING_SAMPLE", 9: "MISSING_VARIANT"}
        for call_id in [6, 8, 9]:
            pred_row = pred.get(call_id) or pred.get(str(call_id))
            if pred_row is None or pred_row[3] != expected_status[call_id]:
                flags.append({6: "q1_call6_status_wrong", 8: "q1_call8_status_wrong", 9: "q1_call9_status_wrong"}[call_id])
        for call_id in [1, 2, 3, 4, 5, 7]:
            pred_row = pred.get(call_id) or pred.get(str(call_id))
            if pred_row is not None and pred_row[3] != "COMPLETE_CHAIN":
                flags.append("q1_complete_chain_status_wrong")
                break

    elif case_id == "pass3.query2":
        pred = rows_by_pair(pred_rows, 0, 1)
        expected = {
            ("mature_leaf", "NDHB"): (3, 40, 0.467, 99),
            ("mature_leaf", "NDHK"): (1, 10, 0.5, 80),
            ("young_leaf", "NDHK"): (1, 0, 0.0, 88),
            ("young_leaf", "PGR5"): (1, 9, 0.5, 70),
        }
        if set(pred) != set(expected):
            flags.append("q2_wrong_group_set")
        if any(key not in expected for key in pred):
            flags.append("q2_leaked_incomplete_or_root")
        for key, (count, sum_alt, avg_vaf, max_qual) in expected.items():
            if key in pred:
                if pred[key][2] != count or pred[key][3] != sum_alt:
                    flags.append("q2_wrong_counts_or_alt")
                if not numeric_close(pred[key][4], avg_vaf):
                    flags.append("q2_wrong_vaf")
                if pred[key][5] != max_qual:
                    flags.append("q2_wrong_max_qual")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass3.query3":
        pred = rows_by_index(pred_rows, 0)
        expected = {
            "NDHB": ("chloroplast_NDH_complex", 4, 54),
            "NDHK": ("chloroplast_NDH_complex", 2, 10),
            "PGR5": ("cyclic_electron_flow", 1, 9),
            "NDHT": ("chlororespiration", 0, 0),
            "PGR1B": ("PSI_photoprotection", 0, 0),
        }
        if "NDHT" not in pred or "PGR1B" not in pred:
            flags.append("q3_missing_zero_call_gene")
        if any(gene not in expected for gene in pred):
            flags.append("q3_leaked_unknown_gene")
        for gene, (_pathway, count, alt) in expected.items():
            if gene in pred:
                if pred[gene][2] != count:
                    flags.append("q3_wrong_observed_count")
                if not numeric_close(pred[gene][3], alt):
                    flags.append("q3_wrong_total_alt")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass3.query4":
        pred = rows_by_index(pred_rows, 0)
        expected = {"control": (2, 84.0, 5.0), "high_light": (1, 87.0, 28.0)}
        if set(pred) != set(expected):
            flags.append("q4_wrong_group_set")
        if "drought" in pred:
            flags.append("q4_included_non_high_condition")
        if "control" not in pred or pred["control"][1] != 2 or not numeric_close(pred["control"][2], 84.0) or not numeric_close(pred["control"][3], 5.0):
            flags.append("q4_control_bucket_wrong")
        if "high_light" not in pred or pred["high_light"][1] != 1 or not numeric_close(pred["high_light"][2], 87.0) or not numeric_close(pred["high_light"][3], 28.0):
            flags.append("q4_high_light_bucket_wrong")

    elif case_id == "pass3.query5":
        pred = rows_by_index(pred_rows, 0)
        expected = {"S1": (1, 1, 93.0), "S2": (2, 0, 67.5), "S3": (1, 1, 81.0), "S4": (0, 0, None), "S5": (0, 0, None)}
        if not set(expected).issubset(set(pred)):
            flags.append("q5_dropped_preserved_sample")
        if "S999" in pred:
            flags.append("q5_included_s999")
        if "S2" not in pred or pred["S2"][1] != 2 or pred["S2"][2] != 0 or not numeric_close(pred["S2"][3], 67.5):
            flags.append("q5_s2_nonref_wrong")
        for sample, (het, hom, avg) in expected.items():
            if sample in pred and (pred[sample][1] != het or pred[sample][2] != hom or not numeric_close(pred[sample][3], avg)):
                flags.append("q5_counted_reference_or_wrong_class")
                break

    elif case_id == "pass3.query6":
        pred = rows_by_pair(pred_rows, 0, 1)
        expected = {
            ("mature_leaf", "NDHB"): (40, 0.467, 1),
            ("mature_leaf", "NDHK"): (10, 0.5, 2),
            ("young_leaf", "PGR5"): (9, 0.5, 1),
            ("young_leaf", "NDHK"): (0, 0.0, 2),
        }
        if set(pred) != set(expected):
            flags.append("q6_wrong_group_set")
        if any(key not in expected for key in pred):
            flags.append("q6_leaked_root_or_incomplete")
        for key, (total_alt, avg_vaf, rank) in expected.items():
            if key in pred:
                if len(pred[key]) < 5:
                    flags.append("q6_wrong_totals_or_vaf")
                    flags.append("q6_wrong_rank")
                    continue
                if pred[key][2] != total_alt or not numeric_close(pred[key][3], avg_vaf):
                    flags.append("q6_wrong_totals_or_vaf")
                if pred[key][4] != rank:
                    flags.append("q6_wrong_rank")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass3.query7":
        valid_rows = [r for r in pred_rows if isinstance(r, list)]
        pred_pairs = {(r[0], r[1]): r for r in valid_rows if len(r) >= 3}
        expected_pairs = {("gene", "G4"), ("gene", "G5"), ("sample", "S5"), ("variant", "V6")}
        if any(str(r[0]).endswith("_dim") for r in valid_rows if r):
            flags.append("q7_object_type_labels_wrong")
        if not expected_pairs.issubset(set(pred_pairs)):
            flags.append("q7_missing_expected_object")
        if any(r[1] not in {"G4", "G5", "S5", "V6"} for r in valid_rows if len(r) >= 2):
            flags.append("q7_extra_object")
        g4 = pred_pairs.get(("gene", "G4")) or pred_pairs.get(("gene_dim", "G4"))
        if g4 is None or g4[2] != "no_fact_calls_through_variants":
            flags.append("q7_g4_reason_wrong")

    elif case_id == "pass3.query8":
        pred = rows_by_pair(pred_rows, 0, 1)
        expected = {
            ("control", "ndh_membrane_arm"): (1, 0.5),
            ("drought", "pgr_regulator"): (1, 0.5),
            ("high_light", "ndh_membrane_arm"): (2, 0.7),
        }
        if set(pred) != set(expected):
            flags.append("q8_wrong_group_set")
        if any(key not in expected for key in pred):
            flags.append("q8_leaked_reference_or_incomplete")
        for key, (count, mean_vaf) in expected.items():
            if key in pred:
                if pred[key][2] != count:
                    flags.append("q8_wrong_counts")
                if not numeric_close(pred[key][3], mean_vaf):
                    flags.append("q8_wrong_vaf")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass3.query9":
        pred = rows_by_index(pred_rows, 0)
        expected = {
            "UNMATCHED_SAMPLE": (0, 1, 0, 0),
            "control": (3, 0, 1, 0),
            "drought": (1, 0, 0, 1),
            "high_light": (2, 0, 0, 0),
        }
        if not set(expected).issubset(set(pred)):
            flags.append("q9_missing_condition_group")
        for group, (complete, missing_sample, missing_variant, missing_gene) in expected.items():
            if group in pred:
                if pred[group][1] != complete:
                    flags.append("q9_wrong_complete_counts")
                if pred[group][2] != missing_sample or pred[group][3] != missing_variant or pred[group][4] != missing_gene:
                    flags.append("q9_wrong_missing_status_counts")
        flags = list(dict.fromkeys(flags))

    elif case_id == "pass3.query10":
        pred = rows_by_index(pred_rows, 0)
        expected = {"NDHB": (2, 0.7, 1200.0, 840.0), "PGR5": (1, 0.5, 700.0, 350.0), "NDHK": (1, 0.5, 90.0, 45.0)}
        if set(pred) != set(expected):
            flags.append("q10_wrong_gene_set")
        if any(gene not in expected for gene in pred):
            flags.append("q10_leaked_non_gold_gene")
        for gene, (count, avg_vaf, expr, score) in expected.items():
            if gene in pred:
                if pred[gene][1] != count:
                    flags.append("q10_wrong_gene_set")
                if not numeric_close(pred[gene][2], avg_vaf):
                    flags.append("q10_wrong_vaf")
                if not numeric_close(pred[gene][3], expr):
                    flags.append("q10_wrong_expression")
                if not numeric_close(pred[gene][4], score):
                    flags.append("q10_wrong_decision_score")
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

    model_summary.sort(key=lambda r: (-r["exact_attempts"], -r["exact_query_coverage_any"], -r["mean_score"], r["mean_wall_s"], r["display_model"]))

    case_summary = []
    for case_id in sorted(by_case, key=case_sort_key):
        items = by_case[case_id]
        modes = Counter(r["_failure_mode"] for r in items)
        exact_attempts = sum(as_bool(r["exact_match"]) for r in items)
        exact_models_any = sum(any(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) for model in sorted({r["model"] for r in items}))
        exact_models_stable = sum(sum(as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) == 3 for model in sorted({r["model"] for r in items}))
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
        audit_cases = ["pass3.query1", "pass3.query3", "pass3.query7", "pass3.query9"]
        analytical_cases = ["pass3.query2", "pass3.query4", "pass3.query5", "pass3.query6", "pass3.query8", "pass3.query10"]
        audit_score = mean(matrix[model][case]["mean_score"] for case in audit_cases)
        analytical_score = mean(matrix[model][case]["mean_score"] for case in analytical_cases)

        if item["exact_attempts"] >= 8 or item["exact_query_coverage_any"] >= 3:
            group = "Broad pass leader"
            reason = "Only model with stable exact conversions across join-status, genotype, and anti-join audit tasks."
        elif item["exact_attempts"] >= 3:
            group = "Single-skill exact converters"
            reason = "Converted one query reliably, but did not generalize to the aggregate, ranking, or decision-support tasks."
        elif item["mean_score"] >= 0.60:
            group = "Partial-credit operators"
            reason = "Usually found part of the row set, but numeric grain, role grouping, or status classification blocked exact matches."
        else:
            group = "Brittle / low-coverage"
            reason = "No exact conversions plus repeated row-set, audit-label, or numeric calculation failures."

        groups.append(
            {
                "model": model,
                "display_model": item["display_model"],
                "group": group,
                "group_reason": reason,
                "audit_score": audit_score,
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
        "Single-skill exact converters": 1,
        "Partial-credit operators": 2,
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
        "join_key_integrity",
        "aggregation_numeric",
        "orphan_key_audit",
        "outer_join_coverage",
        "ranking_and_priority",
        "decision_support",
        "failure_family_audit",
    ]
    family_short = {
        "join_key_integrity": "Join key\nintegrity",
        "aggregation_numeric": "Numeric\nagg",
        "orphan_key_audit": "Orphan\naudit",
        "outer_join_coverage": "Outer\ncoverage",
        "ranking_and_priority": "Ranking",
        "decision_support": "Decision\nsupport",
        "failure_family_audit": "Failure\nfamily",
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
    fig.suptitle("AIBioBench Pass 3, Latest Run: Hard Audits, Ranking, and Decision Failures", fontsize=24, fontweight="bold", color=TEXT)

    ax1 = fig.add_subplot(gs[0, 0])
    style_axis(ax1)
    y = list(range(len(model_summary)))
    exacts = [m["exact_attempts"] for m in model_summary]
    colors = [BLUE_PALE if x >= 8 else BLUE_LIGHT if x >= 3 else BLUE_MID if x >= 1 else BLUE_DARK for x in exacts]
    bars = ax1.barh(y, exacts, color=colors)
    ax1.set_yticks(y, model_labels)
    ax1.invert_yaxis()
    ax1.set_xlim(0, 30)
    ax1.set_xlabel("Exact attempts out of 30")
    ax1.set_title("Exact Match Conversion by Model", fontweight="bold")
    ax1.grid(axis="x", color=GRID, linewidth=1)
    for bar, item in zip(bars, model_summary):
        ax1.text(min(bar.get_width() + 0.35, 29.4), bar.get_y() + bar.get_height() / 2, f"{item['exact_attempts']}/30  |  {item['exact_query_coverage_any']}/10 queries", va="center", color=TEXT, fontsize=9)

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
    ax6.set_title("Which Pass-3 Questions Broke the Models", fontweight="bold")
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
    fig.suptitle("AIBioBench Pass 3: Model Grouping by Audit vs Analytical Performance", fontsize=22, fontweight="bold", color=TEXT)

    ax1 = fig.add_subplot(gs[0, 0])
    style_axis(ax1)
    for item in groups:
        color = MODEL_GROUP_COLORS[item["group"]]
        ax1.scatter(item["audit_score"], item["analytical_score"], s=120 + item["exact_attempts"] * 28, color=color, edgecolors=BLUE_PALE, linewidth=1.2, alpha=0.95)
        ax1.annotate(wrap_display_name(item["display_model"]), (item["audit_score"], item["analytical_score"]), xytext=(7, 6), textcoords="offset points", color=TEXT, fontsize=9)
    ax1.set_xlabel("Audit tasks mean score\n(Q1, Q3, Q7, Q9)")
    ax1.set_ylabel("Analytical/ranking/decision tasks mean score\n(Q2, Q4, Q5, Q6, Q8, Q10)")
    ax1.set_xlim(0, 1.03)
    ax1.set_ylim(0, 1.03)
    ax1.set_title("Pass-3 exactness requires audit logic plus numeric grain", fontweight="bold")
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
    total_exact = sum(case["exact_attempts"] for case in case_summary)
    model_count = len(model_summary)
    total_attempts = sum(case["total_attempts"] for case in case_summary)
    exact_zero_text = ", ".join(exact_zero) if exact_zero else "none"
    exact_query_text = ", ".join(exact_queries) if exact_queries else "none"
    lines = [
        "# AIBioBench Pass 3 Analysis",
        "",
        f"Run analyzed: `{results_dir.name}`",
        "",
        f"Pass 3 contains ten hard SQL tasks, each repeated three times across {model_count} models. The pressure shifts to join-status classification, orphan audits, dense ranking, complete-chain non-reference filters, and decision-score arithmetic.",
        "",
        "## Headline Findings",
        "",
        f"- **{model_summary[0]['display_model']}** led pass 3 with {model_summary[0]['exact_attempts']}/30 exact attempts and exact coverage on {model_summary[0]['exact_query_coverage_any']}/10 questions.",
        f"- Exact matches were very sparse: only {total_exact}/{total_attempts} attempts were exact. Exact answers appeared on **{exact_query_text}**; zero-exact questions were **{exact_zero_text}**.",
        "- Q1 had high mean score because most models could preserve the row set, but exactness depended on three edge-row status labels.",
        "- The hardest exactness failures were Q2/Q4/Q6/Q8/Q10 numeric-grain tasks and Q7 anti-join label/reason normalization.",
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
    for group in ["Broad pass leader", "Single-skill exact converters", "Partial-credit operators", "Brittle / low-coverage"]:
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
        print("usage: pass3_analysis.py <results_dir>", file=sys.stderr)
        return 2

    results_dir = Path(sys.argv[1]).resolve()
    if not (results_dir / "detailed_results.csv").exists():
        print(f"missing detailed_results.csv in {results_dir}", file=sys.stderr)
        return 1

    repo_root = results_dir.parent.parent
    if not (repo_root / "benchmark_cases.jsonl").exists():
        print(f"missing benchmark_cases.jsonl in repo root inferred from {results_dir}", file=sys.stderr)
        return 1

    out_dir = results_dir / "pass3_analysis"
    out_dir.mkdir(exist_ok=True)

    case_meta, _gold = load_metadata(repo_root)
    rows = load_rows(results_dir)
    model_summary, case_summary, model_query_rows = build_summaries(rows, case_meta)
    family_scores = compute_family_scores(model_query_rows, case_meta)
    model_groups = assign_model_groups(model_summary, model_query_rows)
    failure_point_rows = build_failure_point_rows(case_summary)

    write_csv(
        out_dir / "pass3_model_summary.csv",
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
        out_dir / "pass3_case_summary.csv",
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
        out_dir / "pass3_model_query_matrix.csv",
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
    write_csv(out_dir / "pass3_family_scores.csv", family_scores, ["model", "display_model", "family", "mean_score", "mean_exact_rate"])
    write_csv(
        out_dir / "pass3_model_groups.csv",
        model_groups,
        [
            "model",
            "display_model",
            "group",
            "group_reason",
            "audit_score",
            "analytical_score",
            "exact_attempts",
            "stable_exact_queries",
            "partial_exact_queries",
            "stable_fail_queries",
            "mean_score",
        ],
    )
    write_csv(
        out_dir / "pass3_query_failure_points.csv",
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

    render_visual_report(model_summary, case_summary, model_query_rows, family_scores, out_dir / "pass3_visual_report")
    render_model_groups(model_groups, out_dir / "pass3_model_groups")
    write_notes(out_dir / "pass3_analysis_notes.md", model_summary, case_summary, model_groups, results_dir)

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
