#!/usr/bin/env python3
import csv
import json
import os
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
warnings.filterwarnings("ignore", message="Unable to import Axes3D.*")

import pass4_analysis as base
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


QUERY_LABELS = {
    "pass5.query1": "Q1\nsample\nfeatures",
    "pass5.query2": "Q2\nweighted\nVAF",
    "pass5.query3": "Q3\ncondition\ngene stats",
    "pass5.query4": "Q4\nstress\ncontrol",
    "pass5.query5": "Q5\npathway\nburden",
    "pass5.query6": "Q6\nz-score\nranking",
    "pass5.query7": "Q7\ncondition\nCV",
    "pass5.query8": "Q8\nsample\npressure",
    "pass5.query9": "Q9\nsignal\nranking",
    "pass5.query10": "Q10\nmarker\nshares",
}

QUERY_SHORT_NAMES = {
    "pass5.query1": "Sample expression features",
    "pass5.query2": "Expression-weighted VAF",
    "pass5.query3": "Condition-gene statistics",
    "pass5.query4": "Stress-control log2 delta",
    "pass5.query5": "Pathway-tissue burden",
    "pass5.query6": "Sample expression z-scores",
    "pass5.query7": "Condition CV summary",
    "pass5.query8": "Sample variant pressure",
    "pass5.query9": "Condition-gene signal ranking",
    "pass5.query10": "Marker composition shares",
}

MODEL_GROUP_COLORS = {
    "Top partial-credit operators": base.BLUE_PALE,
    "Upper-middle partial-credit operators": base.BLUE_LIGHT,
    "Row-set fragile partial-credit": base.BLUE_MID,
    "Brittle / low-coverage": base.BLUE_DARK,
}

ISSUE_LABELS = {
    "q1_wrong_sample_set": "Returned the wrong sample set for sample_dim-only feature engineering.",
    "q1_wrong_tissue": "Mismapped sample tissue labels.",
    "q1_wrong_log2_transform": "Miscomputed one or more log2(expr + 1) marker features.",
    "q1_wrong_ratio": "Miscomputed ndh_module_ratio.",
    "q1_wrong_sort": "Returned sample features in the wrong order.",
    "q2_wrong_call_set": "Returned the wrong complete-chain matched call set.",
    "q2_leaked_incomplete_or_orphan": "Leaked incomplete-chain, orphan, or non-gold calls into the weighted VAF table.",
    "q2_wrong_expr_mapping": "Mapped matched_expr_count or log2_matched_expr incorrectly.",
    "q2_wrong_vaf": "Miscomputed VAF.",
    "q2_wrong_weighted_vaf": "Miscomputed expr_weighted_vaf.",
    "q2_wrong_sort": "Returned weighted VAF rows in the wrong order.",
    "q3_wrong_group_set": "Returned the wrong condition-gene group set.",
    "q3_leaked_incomplete_or_orphan": "Leaked incomplete-chain, orphan, or non-gold groups into condition-gene statistics.",
    "q3_wrong_count": "Miscomputed n_calls.",
    "q3_wrong_mean_or_median": "Miscomputed mean or median matched expression.",
    "q3_wrong_pop_std": "Miscomputed population standard deviation.",
    "q3_wrong_sort": "Returned condition-gene statistics in the wrong order.",
    "q4_wrong_gene_set": "Returned the wrong marker-gene set.",
    "q4_wrong_stress_or_control_mean": "Miscomputed stress/control mean log2 expression.",
    "q4_wrong_delta": "Miscomputed stress-minus-control delta.",
    "q4_wrong_sort": "Returned stress-control rows in the wrong order.",
    "q5_wrong_group_set": "Returned the wrong pathway-tissue group set.",
    "q5_leaked_ref_or_incomplete": "Leaked reference, incomplete-chain, or orphan rows into pathway burden.",
    "q5_wrong_count": "Miscomputed non_reference_calls.",
    "q5_wrong_vaf": "Miscomputed mean_vaf.",
    "q5_wrong_log2_expr": "Miscomputed mean_log2_matched_expr.",
    "q5_wrong_burden": "Miscomputed burden_score.",
    "q5_wrong_sort": "Returned pathway burden rows in the wrong order.",
    "q6_wrong_sample_set": "Returned the wrong sample set for z-score ranking.",
    "q6_wrong_zscore": "Miscomputed marker z-scores, usually from ddof or denominator errors.",
    "q6_wrong_z_mean": "Miscomputed photosynthesis_expr_z_mean.",
    "q6_wrong_sort": "Returned z-score rows in the wrong order.",
    "q7_wrong_condition_set": "Returned the wrong condition set.",
    "q7_wrong_gene_count": "Miscomputed distinct_genes_observed.",
    "q7_wrong_mean_expr": "Miscomputed mean_matched_expr.",
    "q7_wrong_cv": "Miscomputed cv_matched_expr.",
    "q7_wrong_vaf": "Miscomputed mean_vaf.",
    "q7_wrong_sort": "Returned condition CV rows in the wrong order.",
    "q8_wrong_sample_set": "Returned the wrong sample set for the preserving sample-level burden table.",
    "q8_missing_zero_call_sample": "Dropped one or more zero-call sample_dim rows.",
    "q8_included_orphan_sample": "Included orphan sample rows such as S999.",
    "q8_wrong_counts": "Miscomputed non-reference or high/moderate call counts.",
    "q8_wrong_marker_expr": "Miscomputed total_marker_expr or log2_total_marker_expr.",
    "q8_wrong_pressure": "Miscomputed photosynthesis_variant_pressure.",
    "q8_wrong_sort": "Returned sample pressure rows in the wrong order.",
    "q9_wrong_group_set": "Returned the wrong condition-gene signal group set.",
    "q9_leaked_ref_or_incomplete": "Leaked reference, incomplete-chain, or orphan groups into signal ranking.",
    "q9_wrong_count": "Miscomputed non_reference_calls.",
    "q9_wrong_vaf": "Miscomputed mean_vaf.",
    "q9_wrong_log2_expr": "Miscomputed mean_log2_matched_expr.",
    "q9_wrong_signal": "Miscomputed expression_weighted_signal.",
    "q9_wrong_sort": "Returned signal rows in the wrong order.",
    "q10_wrong_sample_set": "Returned the wrong sample set for marker composition shares.",
    "q10_wrong_condition": "Mismapped sample condition labels.",
    "q10_wrong_shares": "Miscomputed one or more marker composition shares.",
    "q10_wrong_imbalance": "Miscomputed marker_imbalance.",
    "q10_wrong_sort": "Returned marker-share rows in the wrong order.",
}


def case_sort_key(case_id: str) -> int:
    return int(case_id.split("query")[1])


def query_name(case_id: str) -> str:
    return f"Q{case_sort_key(case_id)}"


def normalize_key(value):
    if isinstance(value, bool):
        return value
    coerced = base.coerce_numeric_strings(value)
    if isinstance(coerced, float) and coerced.is_integer():
        return int(coerced)
    return coerced


def rows_by_norm_index(rows, index=0):
    out = {}
    for row in rows:
        if isinstance(row, list) and len(row) > index:
            out[normalize_key(row[index])] = row
    return out


def rows_by_pair(rows, first=0, second=1):
    out = {}
    for row in rows:
        if isinstance(row, list) and len(row) > max(first, second):
            out[(row[first], row[second])] = row
    return out


def keys_in_order(rows, index=0):
    return [normalize_key(row[index]) for row in rows if isinstance(row, list) and len(row) > index]


def pair_keys_in_order(rows, first=0, second=1):
    return [(row[first], row[second]) for row in rows if isinstance(row, list) and len(row) > max(first, second)]


def load_metadata(repo_root: Path):
    case_meta = {}
    with (repo_root / "benchmark_cases.jsonl").open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            if item["case_id"].startswith("pass5."):
                case_meta[item["case_id"]] = item
    gold = {}
    with (repo_root / "gold_answers.jsonl").open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            if item["case_id"].startswith("pass5."):
                gold[item["case_id"]] = item
    return case_meta, gold


def load_rows(results_dir: Path) -> list[dict]:
    rows = []
    with (results_dir / "detailed_results.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["pass"] != "5":
                continue
            row["_failure_mode"] = base.classify_failure(row)
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


def order_matches(rows, expected_keys, index=0) -> bool:
    return keys_in_order(rows, index) == expected_keys


def pair_order_matches(rows, expected_keys, first=0, second=1) -> bool:
    return pair_keys_in_order(rows, first, second) == expected_keys


def detect_issue_flags(case_id: str, pred_rows: list, gold_rows: list, row: dict) -> list[str]:
    flags = []
    pred_rows = base.coerce_numeric_strings(pred_rows)
    gold_rows = base.coerce_numeric_strings(gold_rows)

    if case_id == "pass5.query1":
        pred = rows_by_norm_index(pred_rows, 0)
        expected = {
            "S1": ("mature_leaf", 10.23, 9.646, 7.238, 0.628),
            "S2": ("mature_leaf", 8.234, 8.969, 6.508, 0.438),
            "S3": ("young_leaf", 9.815, 9.453, 6.794, 0.591),
            "S4": ("young_leaf", 6.658, 8.647, 5.672, 0.273),
            "S5": ("root", 4.392, 4.954, 2.585, 0.455),
        }
        row_set_ok = set(pred) == set(expected)
        if not row_set_ok:
            flags.append("q1_wrong_sample_set")
        if row_set_ok and not order_matches(pred_rows, list(expected)):
            flags.append("q1_wrong_sort")
        for sample, (tissue, ndhb, pgr5, ndhk, ratio) in expected.items():
            if sample not in pred:
                continue
            prow = pred[sample]
            if base.cell(prow, 1) != tissue:
                flags.append("q1_wrong_tissue")
            if not base.numeric_close(base.cell(prow, 2), ndhb) or not base.numeric_close(base.cell(prow, 3), pgr5) or not base.numeric_close(base.cell(prow, 4), ndhk):
                flags.append("q1_wrong_log2_transform")
            if not base.numeric_close(base.cell(prow, 5), ratio):
                flags.append("q1_wrong_ratio")

    elif case_id == "pass5.query2":
        pred = rows_by_norm_index(pred_rows, 0)
        expected_order = [1, 2, 3, 4, 5, 7]
        expected = {
            1: ("NDHB", 1200, 10.23, 0.4, 4.092),
            2: ("NDHB", 1200, 10.23, 1.0, 10.23),
            3: ("NDHB", 300, 8.234, 0.0, 0.0),
            4: ("NDHK", 90, 6.508, 0.5, 3.254),
            5: ("PGR5", 700, 9.453, 0.5, 4.727),
            7: ("NDHK", 50, 5.672, 0.0, 0.0),
        }
        row_set_ok = set(pred) == set(expected)
        if not row_set_ok:
            flags.append("q2_wrong_call_set")
        if any(call_id not in expected for call_id in pred):
            flags.append("q2_leaked_incomplete_or_orphan")
        if row_set_ok and keys_in_order(pred_rows, 0) != expected_order:
            flags.append("q2_wrong_sort")
        for call_id, (gene, expr, logv, vaf, weighted) in expected.items():
            if call_id not in pred:
                continue
            prow = pred[call_id]
            if base.cell(prow, 1) != gene:
                flags.append("q2_wrong_expr_mapping")
            if not base.numeric_close(base.cell(prow, 2), expr) or not base.numeric_close(base.cell(prow, 3), logv):
                flags.append("q2_wrong_expr_mapping")
            if not base.numeric_close(base.cell(prow, 4), vaf):
                flags.append("q2_wrong_vaf")
            if not base.numeric_close(base.cell(prow, 5), weighted):
                flags.append("q2_wrong_weighted_vaf")

    elif case_id == "pass5.query3":
        pred = rows_by_pair(pred_rows, 0, 1)
        expected_order = [("control", "NDHB"), ("control", "NDHK"), ("drought", "PGR5"), ("high_light", "NDHB")]
        expected = {
            ("control", "NDHB"): (1, 300.0, 300.0, 0.0),
            ("control", "NDHK"): (2, 70.0, 70.0, 20.0),
            ("drought", "PGR5"): (1, 700.0, 700.0, 0.0),
            ("high_light", "NDHB"): (2, 1200.0, 1200.0, 0.0),
        }
        row_set_ok = set(pred) == set(expected)
        if not row_set_ok:
            flags.append("q3_wrong_group_set")
        if any(key not in expected for key in pred):
            flags.append("q3_leaked_incomplete_or_orphan")
        if row_set_ok and not pair_order_matches(pred_rows, expected_order):
            flags.append("q3_wrong_sort")
        for key, (count, mean_expr, median_expr, std_expr) in expected.items():
            if key not in pred:
                continue
            prow = pred[key]
            if not base.value_matches(base.cell(prow, 2), count):
                flags.append("q3_wrong_count")
            if not base.numeric_close(base.cell(prow, 3), mean_expr) or not base.numeric_close(base.cell(prow, 4), median_expr):
                flags.append("q3_wrong_mean_or_median")
            if not base.numeric_close(base.cell(prow, 5), std_expr):
                flags.append("q3_wrong_pop_std")

    elif case_id == "pass5.query4":
        pred = rows_by_norm_index(pred_rows, 0)
        expected_order = ["NDHB", "NDHK", "PGR5"]
        expected = {
            "NDHB": (8.146, 7.446, 0.7),
            "NDHK": (5.539, 6.09, -0.551),
            "PGR5": (8.018, 8.808, -0.79),
        }
        row_set_ok = set(pred) == set(expected)
        if not row_set_ok:
            flags.append("q4_wrong_gene_set")
        if row_set_ok and not order_matches(pred_rows, expected_order):
            flags.append("q4_wrong_sort")
        for gene, (stress, control, delta) in expected.items():
            if gene not in pred:
                continue
            prow = pred[gene]
            if not base.numeric_close(base.cell(prow, 1), stress) or not base.numeric_close(base.cell(prow, 2), control):
                flags.append("q4_wrong_stress_or_control_mean")
            if not base.numeric_close(base.cell(prow, 3), delta):
                flags.append("q4_wrong_delta")

    elif case_id == "pass5.query5":
        pred = rows_by_pair(pred_rows, 0, 1)
        expected_order = [("chloroplast_NDH_complex", "mature_leaf"), ("cyclic_electron_flow", "young_leaf")]
        expected = {
            ("chloroplast_NDH_complex", "mature_leaf"): (3, 0.633, 8.989, 17.576),
            ("cyclic_electron_flow", "young_leaf"): (1, 0.5, 9.453, 4.727),
        }
        row_set_ok = set(pred) == set(expected)
        if not row_set_ok:
            flags.append("q5_wrong_group_set")
        if any(key not in expected for key in pred):
            flags.append("q5_leaked_ref_or_incomplete")
        if row_set_ok and not pair_order_matches(pred_rows, expected_order):
            flags.append("q5_wrong_sort")
        for key, (count, vaf, log_expr, burden) in expected.items():
            if key not in pred:
                continue
            prow = pred[key]
            if not base.value_matches(base.cell(prow, 2), count):
                flags.append("q5_wrong_count")
            if not base.numeric_close(base.cell(prow, 3), vaf):
                flags.append("q5_wrong_vaf")
            if not base.numeric_close(base.cell(prow, 4), log_expr):
                flags.append("q5_wrong_log2_expr")
            if not base.numeric_close(base.cell(prow, 5), burden):
                flags.append("q5_wrong_burden")

    elif case_id == "pass5.query6":
        pred = rows_by_norm_index(pred_rows, 0)
        expected_order = ["S1", "S3", "S2", "S4", "S5"]
        expected = {
            "S1": (1.497, 1.17, 1.384, 1.351),
            "S3": (0.852, 0.798, 0.582, 0.744),
            "S2": (-0.439, 0.052, 0.181, -0.069),
            "S4": (-0.869, -0.321, -0.622, -0.604),
            "S5": (-1.041, -1.7, -1.525, -1.422),
        }
        row_set_ok = set(pred) == set(expected)
        if not row_set_ok:
            flags.append("q6_wrong_sample_set")
        if row_set_ok and not order_matches(pred_rows, expected_order):
            flags.append("q6_wrong_sort")
        for sample, (z_ndhb, z_pgr5, z_ndhk, z_mean) in expected.items():
            if sample not in pred:
                continue
            prow = pred[sample]
            if not base.numeric_close(base.cell(prow, 1), z_ndhb) or not base.numeric_close(base.cell(prow, 2), z_pgr5) or not base.numeric_close(base.cell(prow, 3), z_ndhk):
                flags.append("q6_wrong_zscore")
            if not base.numeric_close(base.cell(prow, 4), z_mean):
                flags.append("q6_wrong_z_mean")

    elif case_id == "pass5.query7":
        pred = rows_by_norm_index(pred_rows, 0)
        expected_order = ["control", "drought", "high_light"]
        expected = {
            "control": (2, 146.667, 0.748, 0.167),
            "drought": (1, 700.0, 0.0, 0.5),
            "high_light": (1, 1200.0, 0.0, 0.7),
        }
        row_set_ok = set(pred) == set(expected)
        if not row_set_ok:
            flags.append("q7_wrong_condition_set")
        if row_set_ok and not order_matches(pred_rows, expected_order):
            flags.append("q7_wrong_sort")
        for condition, (gene_count, mean_expr, cv, vaf) in expected.items():
            if condition not in pred:
                continue
            prow = pred[condition]
            if not base.value_matches(base.cell(prow, 1), gene_count):
                flags.append("q7_wrong_gene_count")
            if not base.numeric_close(base.cell(prow, 2), mean_expr):
                flags.append("q7_wrong_mean_expr")
            if not base.numeric_close(base.cell(prow, 3), cv):
                flags.append("q7_wrong_cv")
            if not base.numeric_close(base.cell(prow, 4), vaf):
                flags.append("q7_wrong_vaf")

    elif case_id == "pass5.query8":
        pred = rows_by_norm_index(pred_rows, 0)
        expected_order = ["S1", "S2", "S3", "S4", "S5"]
        expected = {
            "S1": ("mature_leaf", 2, 2, 2150, 11.071, 22.142),
            "S2": ("mature_leaf", 1, 1, 890, 9.799, 9.799),
            "S3": ("young_leaf", 1, 0, 1710, 10.741, 0.0),
            "S4": ("young_leaf", 0, 0, 550, 9.106, 0.0),
            "S5": ("root", 0, 0, 55, 5.807, 0.0),
        }
        row_set_ok = set(pred) == set(expected)
        if not row_set_ok:
            flags.append("q8_wrong_sample_set")
        if not set(expected).issubset(set(pred)):
            flags.append("q8_missing_zero_call_sample")
        if "S999" in pred:
            flags.append("q8_included_orphan_sample")
        if row_set_ok and not order_matches(pred_rows, expected_order):
            flags.append("q8_wrong_sort")
        for sample, (tissue, nonref, hi_mod, total_expr, log_total, pressure) in expected.items():
            if sample not in pred:
                continue
            prow = pred[sample]
            if base.cell(prow, 1) != tissue:
                flags.append("q8_wrong_sample_set")
            if not base.value_matches(base.cell(prow, 2), nonref) or not base.value_matches(base.cell(prow, 3), hi_mod):
                flags.append("q8_wrong_counts")
            if not base.numeric_close(base.cell(prow, 4), total_expr) or not base.numeric_close(base.cell(prow, 5), log_total):
                flags.append("q8_wrong_marker_expr")
            if not base.numeric_close(base.cell(prow, 6), pressure):
                flags.append("q8_wrong_pressure")

    elif case_id == "pass5.query9":
        pred = rows_by_pair(pred_rows, 0, 1)
        expected_order = [("high_light", "NDHB"), ("drought", "PGR5"), ("control", "NDHK")]
        expected = {
            ("high_light", "NDHB"): (2, 0.7, 10.23, 7.161),
            ("drought", "PGR5"): (1, 0.5, 9.453, 4.727),
            ("control", "NDHK"): (1, 0.5, 6.508, 3.254),
        }
        row_set_ok = set(pred) == set(expected)
        if not row_set_ok:
            flags.append("q9_wrong_group_set")
        if any(key not in expected for key in pred):
            flags.append("q9_leaked_ref_or_incomplete")
        if row_set_ok and not pair_order_matches(pred_rows, expected_order):
            flags.append("q9_wrong_sort")
        for key, (count, vaf, log_expr, signal) in expected.items():
            if key not in pred:
                continue
            prow = pred[key]
            if not base.value_matches(base.cell(prow, 2), count):
                flags.append("q9_wrong_count")
            if not base.numeric_close(base.cell(prow, 3), vaf):
                flags.append("q9_wrong_vaf")
            if not base.numeric_close(base.cell(prow, 4), log_expr):
                flags.append("q9_wrong_log2_expr")
            if not base.numeric_close(base.cell(prow, 5), signal):
                flags.append("q9_wrong_signal")

    elif case_id == "pass5.query10":
        pred = rows_by_norm_index(pred_rows, 0)
        expected_order = ["S4", "S1", "S3", "S2", "S5"]
        expected = {
            "S4": ("control", 0.182, 0.727, 0.091, 0.636),
            "S1": ("high_light", 0.558, 0.372, 0.07, 0.488),
            "S3": ("drought", 0.526, 0.409, 0.064, 0.462),
            "S2": ("control", 0.337, 0.562, 0.101, 0.461),
            "S5": ("high_light", 0.364, 0.545, 0.091, 0.455),
        }
        row_set_ok = set(pred) == set(expected)
        if not row_set_ok:
            flags.append("q10_wrong_sample_set")
        if row_set_ok and not order_matches(pred_rows, expected_order):
            flags.append("q10_wrong_sort")
        for sample, (condition, ndhb, pgr5, ndhk, imbalance) in expected.items():
            if sample not in pred:
                continue
            prow = pred[sample]
            if base.cell(prow, 1) != condition:
                flags.append("q10_wrong_condition")
            if not base.numeric_close(base.cell(prow, 2), ndhb) or not base.numeric_close(base.cell(prow, 3), pgr5) or not base.numeric_close(base.cell(prow, 4), ndhk):
                flags.append("q10_wrong_shares")
            if not base.numeric_close(base.cell(prow, 5), imbalance):
                flags.append("q10_wrong_imbalance")

    return list(dict.fromkeys(flags))


def build_summaries(rows: list[dict], case_meta: dict):
    by_model = defaultdict(list)
    by_case = defaultdict(list)
    by_model_case = defaultdict(list)
    for row in rows:
        row["_issue_flags"] = detect_issue_flags(row["case_id"], row["_pred_rows"], row["_gold_rows"], row)
        by_model[row["model"]].append(row)
        by_case[row["case_id"]].append(row)
        by_model_case[(row["model"], row["case_id"])].append(row)

    case_ids = sorted({r["case_id"] for r in rows}, key=case_sort_key)
    model_summary = []
    for model, items in by_model.items():
        exact_attempts = sum(base.as_bool(r["exact_match"]) for r in items)
        modes = Counter(r["_failure_mode"] for r in items)
        model_summary.append(
            {
                "model": model,
                "display_model": base.canonical_model_name(model),
                "attempts": len(items),
                "exact_attempts": exact_attempts,
                "exact_attempt_rate": exact_attempts / len(items),
                "exact_query_coverage_any": sum(any(base.as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) for case_id in case_ids),
                "stable_exact_queries": sum(sum(base.as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) == 3 for case_id in case_ids),
                "partial_exact_queries": sum(0 < sum(base.as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) < 3 for case_id in case_ids),
                "stable_fail_queries": sum(sum(base.as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) == 0 for case_id in case_ids),
                "mean_score": mean(base.as_float(r["score"]) for r in items),
                "mean_aligned_cell_accuracy": mean(base.as_float(r["aligned_cell_accuracy"]) for r in items),
                "mean_row_set_correctness": mean(base.as_float(r["row_set_correctness_score"]) for r in items),
                "mean_numeric_correctness": mean(base.as_float(r["numeric_correctness_score"]) for r in items),
                "mean_sort_correctness": mean(base.as_float(r["sort_order_correctness_score"]) for r in items),
                "row_count_mismatch_rate": mean(not base.as_bool(r["row_count_match"]) for r in items),
                "mean_wall_s": mean(base.as_float(r["client_wall_s"]) for r in items),
                "mean_gen_tps": mean(base.as_float(r["server_gen_tps"]) for r in items),
                "exact": modes["exact"],
                "order_only": modes["order_only"],
                "type_only": modes["type_only"],
                "same_count_wrong_values": modes["same_count_wrong_values"],
                "row_count_mismatch": modes["row_count_mismatch"],
                "column_error": modes["column_error"],
                "invalid_json_or_error": modes["invalid_json_or_error"],
                "dominant_failure_mode": modes.most_common(1)[0][0],
                "dominant_non_exact_failure_mode": base.dominant_non_exact_mode(modes),
            }
        )
    model_summary.sort(key=lambda r: (-r["mean_score"], -r["mean_aligned_cell_accuracy"], r["model"]))

    case_summary = []
    for case_id in case_ids:
        items = by_case[case_id]
        modes = Counter(r["_failure_mode"] for r in items)
        case_summary.append(
            {
                "case_id": case_id,
                "query": query_name(case_id),
                "short_name": QUERY_SHORT_NAMES[case_id],
                "prompt": case_meta[case_id]["prompt"],
                "run_benchmark_id": items[0].get("benchmark_id", ""),
                "metadata_benchmark_id": case_meta[case_id].get("benchmark_id", ""),
                "metadata_matches_run": items[0].get("benchmark_id", "") == case_meta[case_id].get("benchmark_id", ""),
                "primary_failure_family": case_meta[case_id]["metadata"]["failure_family_primary"],
                "total_attempts": len(items),
                "exact_attempts": sum(base.as_bool(r["exact_match"]) for r in items),
                "exact_attempt_rate": mean(base.as_bool(r["exact_match"]) for r in items),
                "exact_models_any": sum(any(base.as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) for model in by_model),
                "exact_models_stable": sum(sum(base.as_bool(r["exact_match"]) for r in by_model_case[(model, case_id)]) == 3 for model in by_model),
                "mean_score": mean(base.as_float(r["score"]) for r in items),
                "mean_aligned_cell_accuracy": mean(base.as_float(r["aligned_cell_accuracy"]) for r in items),
                "row_count_mismatch_attempts": modes["row_count_mismatch"],
                "same_count_wrong_attempts": modes["same_count_wrong_values"],
                "order_only_attempts": modes["order_only"],
                "type_only_attempts": modes["type_only"],
                "column_error_attempts": modes["column_error"],
                "invalid_json_or_error_attempts": modes["invalid_json_or_error"],
                "dominant_failure_mode": modes.most_common(1)[0][0],
                "dominant_non_exact_failure_mode": base.dominant_non_exact_mode(modes),
            }
        )

    model_query_rows = []
    for model in sorted(by_model, key=lambda m: next(x["display_model"] for x in model_summary if x["model"] == m)):
        for case_id in case_ids:
            items = by_model_case[(model, case_id)]
            flag_counts = Counter(flag for r in items for flag in r["_issue_flags"])
            model_query_rows.append(
                {
                    "model": model,
                    "display_model": base.canonical_model_name(model),
                    "case_id": case_id,
                    "query": query_name(case_id),
                    "exact_attempts": sum(base.as_bool(r["exact_match"]) for r in items),
                    "mean_score": mean(base.as_float(r["score"]) for r in items),
                    "mean_aligned_cell_accuracy": mean(base.as_float(r["aligned_cell_accuracy"]) for r in items),
                    "mean_row_set_correctness": mean(base.as_float(r["row_set_correctness_score"]) for r in items),
                    "dominant_failure_mode": Counter(r["_failure_mode"] for r in items).most_common(1)[0][0],
                    "dominant_non_exact_failure_mode": base.dominant_non_exact_mode(Counter(r["_failure_mode"] for r in items)),
                    "top_issue": flag_counts.most_common(1)[0][0] if flag_counts else "",
                    "top_issue_count": flag_counts.most_common(1)[0][1] if flag_counts else 0,
                }
            )
    return model_summary, case_summary, model_query_rows


def build_family_scores(model_query_rows: list[dict], case_meta: dict):
    grouped = defaultdict(list)
    for row in model_query_rows:
        family = case_meta[row["case_id"]]["metadata"]["failure_family_primary"]
        grouped[(row["model"], row["display_model"], family)].append(row)
    family_rows = []
    for (model, display_model, family), items in grouped.items():
        family_rows.append(
            {
                "model": model,
                "display_model": display_model,
                "family": family,
                "mean_score": mean(r["mean_score"] for r in items),
                "mean_aligned_cell_accuracy": mean(r["mean_aligned_cell_accuracy"] for r in items),
                "exact_attempts": sum(r["exact_attempts"] for r in items),
                "queries": len(items),
            }
        )
    family_rows.sort(key=lambda r: (r["family"], -r["mean_score"], r["display_model"]))
    return family_rows


def build_query_failure_rows(rows: list[dict]):
    out = []
    by_case = defaultdict(list)
    for row in rows:
        by_case[row["case_id"]].append(row)
    for case_id in sorted(by_case, key=case_sort_key):
        counts = Counter(flag for row in by_case[case_id] for flag in row["_issue_flags"])
        for flag, count in counts.most_common():
            examples = []
            for row in by_case[case_id]:
                if flag in row["_issue_flags"]:
                    name = base.canonical_model_name(row["model"])
                    if name not in examples:
                        examples.append(name)
                if len(examples) == 4:
                    break
            out.append(
                {
                    "case_id": case_id,
                    "query": query_name(case_id),
                    "short_name": QUERY_SHORT_NAMES[case_id],
                    "issue_code": flag,
                    "issue_label": ISSUE_LABELS[flag],
                    "attempts_with_issue": count,
                    "attempt_pct": count / len(by_case[case_id]),
                    "example_models": ", ".join(examples),
                }
            )
    return out


def group_models(model_summary: list[dict], family_rows: list[dict]):
    family_lookup = defaultdict(dict)
    for row in family_rows:
        family_lookup[row["model"]][row["family"]] = row["mean_score"]

    grouped = []
    for row in model_summary:
        score = row["mean_score"]
        if score >= 0.60:
            group = "Top partial-credit operators"
            reason = "No exact pass-5 conversions, but best row-set recovery and strongest partial credit on expression/statistical transforms."
        elif score >= 0.55:
            group = "Upper-middle partial-credit operators"
            reason = "Reasonable partial credit, but failures cluster around numeric formulas, population statistics, and ranking order."
        elif score >= 0.49:
            group = "Row-set fragile partial-credit"
            reason = "Some useful table shape recovery, but row-set leakage and expression-derived values remain unstable."
        else:
            group = "Brittle / low-coverage"
            reason = "Low partial credit with frequent row-set mismatch and weak numeric derivations."
        grouped.append(
            {
                "model": row["model"],
                "display_model": row["display_model"],
                "group": group,
                "group_reason": reason,
                "expression_transform_score": family_lookup[row["model"]].get("expression_transform", 0.0),
                "statistical_summary_score": family_lookup[row["model"]].get("statistical_summary", 0.0),
                "decision_support_score": family_lookup[row["model"]].get("decision_support", 0.0),
                "ranking_and_priority_score": family_lookup[row["model"]].get("ranking_and_priority", 0.0),
                "repeatability_probe_score": family_lookup[row["model"]].get("repeatability_probe", 0.0),
                "exact_attempts": row["exact_attempts"],
                "stable_exact_queries": row["stable_exact_queries"],
                "partial_exact_queries": row["partial_exact_queries"],
                "stable_fail_queries": row["stable_fail_queries"],
                "mean_score": row["mean_score"],
            }
        )
    return grouped


def style_dark_axis(ax):
    ax.set_facecolor(base.PANEL_BG)
    ax.tick_params(colors=base.TEXT)
    for spine in ax.spines.values():
        spine.set_color(base.GRID)
    ax.title.set_color(base.TEXT)
    ax.xaxis.label.set_color(base.TEXT)
    ax.yaxis.label.set_color(base.TEXT)


def render_visual_report(model_summary, case_summary, model_query_rows, rows, out_base: Path) -> None:
    models = [m["model"] for m in model_summary]
    model_labels = [base.wrap_display_name(m["display_model"]) for m in model_summary]
    cases = [c["case_id"] for c in case_summary]
    case_labels = [QUERY_LABELS[c] for c in cases]
    total_attempts_per_query = max(c["total_attempts"] for c in case_summary)
    mq = {(r["model"], r["case_id"]): r for r in model_query_rows}
    score_matrix = [[mq[(model, case)]["mean_score"] for case in cases] for model in models]
    cell_matrix = [[mq[(model, case)]["mean_aligned_cell_accuracy"] for case in cases] for model in models]
    total_exact = sum(c["exact_attempts"] for c in case_summary)

    fig = plt.figure(figsize=(21, 16), facecolor=base.PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.35, 1.0])
    fig.suptitle(
        "AIBioBench Pass 5: Extreme-Hard Expression Transforms and Statistical Decision Signals",
        fontsize=23,
        fontweight="bold",
        color=base.TEXT,
    )

    ax1 = fig.add_subplot(gs[0, 0])
    y = list(range(len(model_summary)))
    scores = [m["mean_score"] for m in model_summary]
    bar_colors = [base.BLUE_PALE if s >= 0.60 else base.BLUE_LIGHT if s >= 0.55 else base.BLUE_MID if s >= 0.49 else base.BLUE_DARK for s in scores]
    bars = ax1.barh(y, scores, color=bar_colors)
    ax1.set_yticks(y, model_labels)
    ax1.invert_yaxis()
    ax1.set_xlim(0, 1.0)
    ax1.set_xlabel("Mean score across 30 attempts")
    ax1.set_title(f"Model Partial-Credit Performance ({total_exact} Exact Attempts Overall)", fontweight="bold")
    ax1.grid(axis="x", color=base.GRID, linewidth=0.8, alpha=0.75)
    for bar, item in zip(bars, model_summary):
        ax1.text(bar.get_width() + 0.012, bar.get_y() + bar.get_height() / 2, f"{item['mean_score']:.3f}", va="center", color=base.TEXT, fontsize=10)
    style_dark_axis(ax1)

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.scatter(
        [m["mean_row_set_correctness"] for m in model_summary],
        [m["mean_numeric_correctness"] for m in model_summary],
        s=[140 + 360 * m["mean_score"] for m in model_summary],
        color=base.BLUE_LIGHT,
        edgecolors=base.BLUE_PALE,
        linewidth=1.2,
        alpha=0.82,
    )
    for m in model_summary:
        ax2.annotate(m["display_model"].replace(" ", "\n", 1), (m["mean_row_set_correctness"], m["mean_numeric_correctness"]), xytext=(6, 5), textcoords="offset points", fontsize=8, color=base.TEXT)
    ax2.set_xlabel("Mean row-set correctness")
    ax2.set_ylabel("Mean numeric correctness")
    ax2.set_title("Row Recovery vs Numeric Derivation", fontweight="bold")
    ax2.set_xlim(0.45, 1.0)
    ax2.set_ylim(0.15, 0.75)
    ax2.grid(color=base.GRID, linewidth=0.8, alpha=0.75)
    style_dark_axis(ax2)

    ax3 = fig.add_subplot(gs[1, 0])
    score_cmap = LinearSegmentedColormap.from_list("professional_blues_score", [base.BLUE_DARK, base.BLUE, base.BLUE_LIGHT, base.BLUE_PALE])
    im = ax3.imshow(score_matrix, aspect="auto", cmap=score_cmap, vmin=0, vmax=1)
    ax3.set_xticks(range(len(cases)), case_labels)
    ax3.set_yticks(range(len(models)), model_labels)
    ax3.set_title("Mean Score Heatmap by Model and Query", fontweight="bold")
    for i in range(len(models)):
        for j in range(len(cases)):
            val = score_matrix[i][j]
            ax3.text(j, i, f"{val:.2f}", ha="center", va="center", color=base.PAGE_BG if val > 0.63 else base.TEXT, fontsize=8)
    cbar = fig.colorbar(im, ax=ax3, fraction=0.025, pad=0.02)
    cbar.ax.tick_params(labelsize=8, colors=base.TEXT)
    style_dark_axis(ax3)

    ax4 = fig.add_subplot(gs[1, 1])
    cell_cmap = LinearSegmentedColormap.from_list("professional_blues_cell", [base.BLUE_DARK, base.BLUE, base.BLUE_LIGHT, base.BLUE_PALE])
    im2 = ax4.imshow(cell_matrix, aspect="auto", cmap=cell_cmap, vmin=0, vmax=1)
    ax4.set_xticks(range(len(cases)), case_labels)
    ax4.set_yticks(range(len(models)), model_labels)
    ax4.set_title("Aligned Cell Accuracy: Correct Values Within Rows", fontweight="bold")
    for i in range(len(models)):
        for j in range(len(cases)):
            val = cell_matrix[i][j]
            ax4.text(j, i, f"{val:.0%}", ha="center", va="center", color=base.PAGE_BG if val > 0.55 else base.TEXT, fontsize=8)
    cbar2 = fig.colorbar(im2, ax=ax4, fraction=0.025, pad=0.02)
    cbar2.ax.tick_params(labelsize=8, colors=base.TEXT)
    style_dark_axis(ax4)

    ax5 = fig.add_subplot(gs[2, 0])
    mode_order = [
        ("same_count_wrong_values", "Same count, wrong values", base.BLUE_PALE),
        ("row_count_mismatch", "Wrong row count", base.BLUE_LIGHT),
        ("order_only", "Correct rows, wrong order", base.BLUE),
        ("type_only", "Type only", base.BLUE_MID),
        ("column_error", "Column/schema error", base.FAIL_PALE),
        ("invalid_json_or_error", "Invalid JSON/error", base.TEXT),
    ]
    bottoms = [0] * len(cases)
    for mode, label, color in mode_order:
        vals = [sum(1 for r in rows if r["case_id"] == case and r["_failure_mode"] == mode) for case in cases]
        ax5.bar(range(len(cases)), vals, bottom=bottoms, label=label, color=color, edgecolor=base.PANEL_BG)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax5.set_xticks(range(len(cases)), [query_name(c) for c in cases])
    ax5.set_ylim(0, total_attempts_per_query)
    ax5.set_ylabel("Attempts")
    ax5.set_title(f"Failure Mode by Query ({total_attempts_per_query} Attempts Each)", fontweight="bold")
    ax5.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=9, labelcolor=base.TEXT)
    ax5.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_dark_axis(ax5)

    ax6 = fig.add_subplot(gs[2, 1])
    query_scores = [c["mean_score"] for c in case_summary]
    query_cells = [c["mean_aligned_cell_accuracy"] for c in case_summary]
    ax6.plot(range(len(cases)), query_scores, color=base.BLUE_PALE, linewidth=2.8, marker="o", markersize=8, label="Mean score")
    ax6.plot(range(len(cases)), query_cells, color=base.BLUE_MID, linewidth=2.2, marker="s", markersize=7, label="Mean cell accuracy")
    ax6.fill_between(range(len(cases)), query_scores, color=base.BLUE_LIGHT, alpha=0.18)
    for idx, case in enumerate(case_summary):
        ax6.text(idx, min(query_scores[idx] + 0.04, 1.02), f"{case['exact_attempts']}/{case['total_attempts']}", ha="center", color=base.TEXT, fontsize=9)
    ax6.set_xticks(range(len(cases)), [query_name(c) for c in cases])
    ax6.set_ylim(0, 1.05)
    ax6.set_ylabel("Score")
    ax6.set_title("Query Solvability: Exact Counts vs Partial Credit", fontweight="bold")
    ax6.legend(frameon=False, loc="upper right", labelcolor=base.TEXT)
    ax6.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_dark_axis(ax6)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def render_model_groups(model_groups, out_base: Path) -> None:
    total_exact = sum(row["exact_attempts"] for row in model_groups)
    fig = plt.figure(figsize=(18, 10), facecolor=base.PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.2, 1.0])
    fig.suptitle("Pass 5 Model Grouping by Failure Pattern and Partial-Credit Strength", fontsize=20, fontweight="bold", color=base.TEXT)

    ax1 = fig.add_subplot(gs[0, 0])
    ordered = sorted(model_groups, key=lambda r: (-r["mean_score"], r["display_model"]))
    y = list(range(len(ordered)))
    colors = [MODEL_GROUP_COLORS[r["group"]] for r in ordered]
    bars = ax1.barh(y, [r["mean_score"] for r in ordered], color=colors)
    ax1.set_yticks(y, [base.wrap_display_name(r["display_model"]) for r in ordered])
    ax1.invert_yaxis()
    ax1.set_xlim(0, 0.82)
    ax1.set_xlabel("Mean score")
    ax1.set_title("Model Groups", fontweight="bold")
    ax1.grid(axis="x", color=base.GRID, linewidth=0.8, alpha=0.75)
    for bar, row in zip(bars, ordered):
        ax1.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2, row["group"], va="center", color=base.TEXT, fontsize=9)
    style_dark_axis(ax1)

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis("off")
    ax2.set_facecolor(base.PANEL_BG)
    y_pos = 0.96
    for group in MODEL_GROUP_COLORS:
        members = [r["display_model"] for r in ordered if r["group"] == group]
        if not members:
            continue
        ax2.text(0.02, y_pos, group, transform=ax2.transAxes, color=MODEL_GROUP_COLORS[group], fontsize=14, fontweight="bold", va="top")
        y_pos -= 0.055
        reason = next(r["group_reason"] for r in ordered if r["group"] == group)
        ax2.text(0.04, y_pos, reason, transform=ax2.transAxes, color=base.TEXT, fontsize=10, va="top", wrap=True)
        y_pos -= 0.10
        ax2.text(0.04, y_pos, ", ".join(members), transform=ax2.transAxes, color=base.BLUE_PALE, fontsize=10, va="top", wrap=True)
        y_pos -= 0.13
    grouping_note = (
        "Grouping uses mean score because pass 5 had zero exact matches across all models."
        if total_exact == 0
        else f"Grouping primarily uses mean score; exact matches across all models: {total_exact}."
    )
    ax2.text(0.02, 0.08, grouping_note, transform=ax2.transAxes, color=base.BLUE_LIGHT, fontsize=10, va="bottom", wrap=True)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def write_notes(path: Path, results_dir: Path, model_summary, case_summary, query_failure_rows, model_groups) -> None:
    model_count = len(model_summary)
    total_exact = sum(c["exact_attempts"] for c in case_summary)
    total_attempts = sum(c["total_attempts"] for c in case_summary)
    exact_queries = [c["query"] for c in case_summary if c["exact_attempts"] > 0]
    exact_query_text = ", ".join(exact_queries) if exact_queries else "none"
    exact_finding = (
        f"- No model produced an exact answer on pass 5: exact matches were {total_exact}/{total_attempts}."
        if total_exact == 0
        else f"- Exact matches remained sparse: {total_exact}/{total_attempts} attempts were exact. Exact answers appeared on **{exact_query_text}**."
    )
    lines = [
        "# AIBioBench Pass 5 Analysis",
        "",
        f"Run analyzed: `{results_dir.name}`",
        "",
        f"Pass 5 contains ten extreme-hard Python/pandas tasks, each repeated three times across {model_count} models. The pass stresses expression transforms, complete-chain matched-expression mapping, population statistics, z-scores, coefficients of variation, signal ranking, and sample-level burden scores.",
        "",
        "## Headline Findings",
        "",
        exact_finding,
        f"- {model_summary[0]['display_model']} led on partial credit with mean score {model_summary[0]['mean_score']:.3f}, followed by {model_summary[1]['display_model']} at {model_summary[1]['mean_score']:.3f} and {model_summary[2]['display_model']} at {model_summary[2]['mean_score']:.3f}.",
        "- The strongest query-level scores came from sample-preserving transforms and condition summaries; the weakest were condition-gene signal ranking, pathway burden, and marker composition shares.",
        "- Recurring failure points were wrong numeric derivations after mostly plausible joins: log2 transforms, VAF weighting, population standard deviation, coefficient of variation, and ranking by derived metrics.",
        "",
        "## Model Groups",
        "",
        "| Group | Models | Why they belong there |",
        "|---|---|---|",
    ]
    for group in MODEL_GROUP_COLORS:
        members = [r["display_model"] for r in model_groups if r["group"] == group]
        if members:
            reason = next(r["group_reason"] for r in model_groups if r["group"] == group)
            lines.append(f"| {group} | {', '.join(members)} | {reason} |")

    lines.extend(
        [
            "",
            "## Model Summary",
            "",
            "| Model | Exact Attempts | Queries With Any Exact | Mean Score | Mean Cell Accuracy | Mean Row-Set Correctness | Dominant Non-Exact Failure Mode |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for m in model_summary:
        lines.append(
            f"| {m['display_model']} | {m['exact_attempts']}/{m['attempts']} | {m['exact_query_coverage_any']}/10 | {m['mean_score']:.3f} | {m['mean_aligned_cell_accuracy']:.3f} | {m['mean_row_set_correctness']:.3f} | {m['dominant_non_exact_failure_mode']} |"
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
    by_case = defaultdict(list)
    for row in query_failure_rows:
        by_case[row["case_id"]].append(row)
    for c in case_summary:
        failures = by_case[c["case_id"]][:3]
        failure_text = "; ".join(f"{f['attempts_with_issue']}/{c['total_attempts']}: {f['issue_label']}" for f in failures)
        lines.append(f"| {c['query']} | {c['short_name']} | {c['exact_attempts']}/{c['total_attempts']} | {c['mean_score']:.3f} | {failure_text} |")

    lines.extend(["", "## Short Notes", ""])
    for c in case_summary:
        failures = by_case[c["case_id"]][:3]
        lines.append(f"- **{c['query']} {c['short_name']}**: {c['exact_attempts']}/{c['total_attempts']} exact, dominant non-exact failure mode `{c['dominant_non_exact_failure_mode']}`. Primary family: `{c['primary_failure_family']}`.")
        for failure in failures:
            lines.append(f"Issue: {failure['attempts_with_issue']}/{c['total_attempts']} attempts. {failure['issue_label']} Example models: {failure['example_models']}.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: pass5_analysis.py <results_dir>", file=sys.stderr)
        return 2

    results_dir = Path(sys.argv[1]).resolve()
    repo_root = Path(__file__).resolve().parents[1]
    if not (results_dir / "detailed_results.csv").exists():
        print(f"missing detailed_results.csv in {results_dir}", file=sys.stderr)
        return 1

    out_dir = results_dir / "pass5_analysis"
    out_dir.mkdir(exist_ok=True)

    case_meta, _gold = load_metadata(repo_root)
    rows = load_rows(results_dir)
    if not rows:
        print("no pass-5 rows found", file=sys.stderr)
        return 1

    model_summary, case_summary, model_query_rows = build_summaries(rows, case_meta)
    family_rows = build_family_scores(model_query_rows, case_meta)
    query_failure_rows = build_query_failure_rows(rows)
    model_groups = group_models(model_summary, family_rows)

    base.write_csv(
        out_dir / "pass5_model_summary.csv",
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
    base.write_csv(
        out_dir / "pass5_case_summary.csv",
        case_summary,
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
    base.write_csv(
        out_dir / "pass5_model_query_matrix.csv",
        model_query_rows,
        [
            "model",
            "display_model",
            "case_id",
            "query",
            "exact_attempts",
            "mean_score",
            "mean_aligned_cell_accuracy",
            "mean_row_set_correctness",
            "dominant_failure_mode",
            "dominant_non_exact_failure_mode",
            "top_issue",
            "top_issue_count",
        ],
    )
    base.write_csv(
        out_dir / "pass5_family_scores.csv",
        family_rows,
        ["model", "display_model", "family", "mean_score", "mean_aligned_cell_accuracy", "exact_attempts", "queries"],
    )
    base.write_csv(
        out_dir / "pass5_model_groups.csv",
        model_groups,
        [
            "model",
            "display_model",
            "group",
            "group_reason",
            "expression_transform_score",
            "statistical_summary_score",
            "decision_support_score",
            "ranking_and_priority_score",
            "repeatability_probe_score",
            "exact_attempts",
            "stable_exact_queries",
            "partial_exact_queries",
            "stable_fail_queries",
            "mean_score",
        ],
    )
    base.write_csv(
        out_dir / "pass5_query_failure_points.csv",
        query_failure_rows,
        ["case_id", "query", "short_name", "issue_code", "issue_label", "attempts_with_issue", "attempt_pct", "example_models"],
    )

    render_visual_report(model_summary, case_summary, model_query_rows, rows, out_dir / "pass5_visual_report")
    render_model_groups(model_groups, out_dir / "pass5_model_groups")
    write_notes(out_dir / "pass5_analysis_notes.md", results_dir, model_summary, case_summary, query_failure_rows, model_groups)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
