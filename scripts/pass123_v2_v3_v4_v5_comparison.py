#!/usr/bin/env python3
import csv
import json
import math
import os
import sys
import textwrap
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
warnings.filterwarnings("ignore", message="Unable to import Axes3D.*")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LinearSegmentedColormap

import pass4_analysis as base


RUNS = ("v2", "v3", "v4", "v5")
RUN_PAIRS = (("v3", "v2"), ("v4", "v3"), ("v5", "v4"), ("v5", "v2"))
EXPECTED_REPEATS = 3
EXPECTED_QUERIES_PER_PASS = 10
EXPECTED_ATTEMPTS_PER_MODEL_PASS = EXPECTED_REPEATS * EXPECTED_QUERIES_PER_PASS
PASSES = ("1", "2", "3")
PASS_LABELS = {pass_no: f"Pass {pass_no}" for pass_no in PASSES}
EXPECTED_QUERY_RUN_CELLS = 0
EXPECTED_ATTEMPTS_PER_MODEL_ALL_RUNS = 0
EXPECTED_ATTEMPTS_PER_MODEL_RUN = 0
TOTAL_QUERY_COUNT = 0
SCOPE_TITLE = ""
SCOPE_COMPACT = ""
SCOPE_DESCRIPTION = ""
DEFAULT_PREFIX = ""
DEFAULT_OUTPUT_DIR_NAME = ""

RUN_COLORS = {
    "v2": base.BLUE_DARK,
    "v3": base.BLUE,
    "v4": base.BLUE_LIGHT,
    "v5": base.BLUE_PALE,
}
RUN_MARKERS = {"v2": "o", "v3": "^", "v4": "s", "v5": "D"}
PASS_COLORS = {
    "1": base.BLUE_PALE,
    "2": base.BLUE_LIGHT,
    "3": base.BLUE_MID,
    "4": base.BLUE,
    "5": base.BLUE_DARK,
}
FAILURE_MODES = (
    "exact",
    "same_count_wrong_values",
    "row_count_mismatch",
    "order_only",
    "type_only",
    "column_error",
    "invalid_json_or_error",
)
FAILURE_MODE_LABELS = {
    "exact": "Exact",
    "same_count_wrong_values": "Same count,\nwrong values",
    "row_count_mismatch": "Wrong row\ncount",
    "order_only": "Order only",
    "type_only": "Type only",
    "column_error": "Column/schema",
    "invalid_json_or_error": "Invalid JSON/error",
}
FAILURE_MODE_COLORS = {
    "exact": base.BLUE_PALE,
    "same_count_wrong_values": base.FAIL_LIGHT,
    "row_count_mismatch": base.BLUE_DARK,
    "order_only": base.BLUE_LIGHT,
    "type_only": base.BLUE_MID,
    "column_error": base.FAIL_PALE,
    "invalid_json_or_error": base.TEXT,
}
COMPONENTS = (
    ("mean_score", "Weighted\nscore"),
    ("mean_row_set_correctness", "Row-set"),
    ("mean_numeric_correctness", "Numeric"),
    ("mean_sort_correctness", "Sort"),
    ("mean_aligned_cell_accuracy", "Cell"),
)
CORRECTNESS_COMPONENT_KEYS = (
    "mean_row_set_correctness",
    "mean_numeric_correctness",
    "mean_sort_correctness",
    "mean_aligned_cell_accuracy",
)


def configure_scope(scope: str = "pass123") -> None:
    global PASSES
    global PASS_LABELS
    global EXPECTED_QUERY_RUN_CELLS
    global EXPECTED_ATTEMPTS_PER_MODEL_ALL_RUNS
    global EXPECTED_ATTEMPTS_PER_MODEL_RUN
    global TOTAL_QUERY_COUNT
    global SCOPE_TITLE
    global SCOPE_COMPACT
    global SCOPE_DESCRIPTION
    global DEFAULT_PREFIX
    global DEFAULT_OUTPUT_DIR_NAME

    if scope in {"all", "all_passes", "pass12345", "pass1-5", "1-5"}:
        PASSES = ("1", "2", "3", "4", "5")
        SCOPE_TITLE = "Pass 1+2+3+4+5"
        SCOPE_COMPACT = "pass12345"
        SCOPE_DESCRIPTION = "passes 1, 2, 3, 4, and 5 only; 50 tasks per model per run with 3 repeats per task"
        DEFAULT_PREFIX = "pass12345_v2_v3_v4_v5"
        DEFAULT_OUTPUT_DIR_NAME = "pass12345_v2_v3_v4_v5_comparison_analysis"
    elif scope in {"pass123", "1-3", "pass1-3"}:
        PASSES = ("1", "2", "3")
        SCOPE_TITLE = "Pass 1+2+3"
        SCOPE_COMPACT = "pass123"
        SCOPE_DESCRIPTION = "passes 1, 2, and 3 only; 30 SQL tasks per model per run with 3 repeats per task"
        DEFAULT_PREFIX = "pass123_v2_v3_v4_v5"
        DEFAULT_OUTPUT_DIR_NAME = "pass123_v2_v3_v4_v5_comparison_analysis"
    else:
        raise ValueError(f"unknown comparison scope: {scope}")

    PASS_LABELS = {pass_no: f"Pass {pass_no}" for pass_no in PASSES}
    TOTAL_QUERY_COUNT = len(PASSES) * EXPECTED_QUERIES_PER_PASS
    EXPECTED_QUERY_RUN_CELLS = len(RUNS) * TOTAL_QUERY_COUNT
    EXPECTED_ATTEMPTS_PER_MODEL_ALL_RUNS = EXPECTED_QUERY_RUN_CELLS * EXPECTED_REPEATS
    EXPECTED_ATTEMPTS_PER_MODEL_RUN = TOTAL_QUERY_COUNT * EXPECTED_REPEATS


configure_scope("pass123")


def case_sort_key(case_id: str) -> tuple[int, int]:
    left, right = case_id.split(".query")
    return int(left.replace("pass", "")), int(right)


def query_label(case_id: str) -> str:
    pass_no, query_no = case_sort_key(case_id)
    return f"P{pass_no}Q{query_no}"


def pass_of_case(case_id: str) -> str:
    return str(case_sort_key(case_id)[0])


def safe_mean(values) -> float:
    values = [v for v in values if v is not None and not math.isnan(v)]
    return mean(values) if values else 0.0


def wrap_label(value: str, width: int = 14) -> str:
    return "\n".join(textwrap.wrap(value.replace("_", " "), width=width, break_long_words=False))


def short_model_label(model: str) -> str:
    display = base.canonical_model_name(model)
    replacements = {
        "Gemma 4 31B": "G31",
        "Qwen3.6 27B": "Q3.6-27",
        "Qwen3.6": "Q3.6",
        "Gemma 4 26B": "G26",
        "Qwen3 Coder 30B": "Q3C",
        "Phi-4 Mini": "Phi",
    }
    return replacements.get(display, display)


def load_case_meta(repo_root: Path) -> dict:
    out = {}
    with (repo_root / "benchmark_cases.jsonl").open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if str(row["pass"]) in PASSES:
                out[row["case_id"]] = row
    return out


def load_rows(results_dir: Path, run_label: str, case_meta: dict) -> list[dict]:
    path = results_dir / "detailed_results.csv"
    if not path.exists():
        raise FileNotFoundError(path)

    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["pass"] not in PASSES:
                continue
            meta = case_meta.get(row["case_id"], {})
            metadata = meta.get("metadata", {})
            row["_run"] = run_label
            row["_display_model"] = base.canonical_model_name(row["model"])
            row["_failure_mode"] = base.classify_failure(row)
            row["_family"] = (
                row.get("failure_family_primary_case")
                or row.get("result_primary_failure_family")
                or metadata.get("failure_family_primary", "")
                or "unclassified"
            )
            row["_query_label"] = query_label(row["case_id"])
            rows.append(row)
    return rows


def cpu_gpu_ratio(row: dict) -> float | None:
    cpu = base.as_float(row.get("ollama_cpu_avg", "0"))
    if cpu <= 0:
        cpu = base.as_float(row.get("system_cpu_avg", "0"))
    gpu = base.as_float(row.get("gpu_util_pct_avg", "0"))
    if gpu <= 0:
        gpu = base.as_float(row.get("gpu_mem_util_pct_avg", "0"))
    if cpu <= 0:
        return None
    return cpu / (gpu if gpu > 0 else 1.0)


def summarize_attempts(items: list[dict]) -> dict:
    modes = Counter(r["_failure_mode"] for r in items)
    attempts = len(items)
    exact_attempts = sum(base.as_bool(r.get("exact_match", "")) for r in items)
    ratios = [ratio for r in items if (ratio := cpu_gpu_ratio(r)) is not None]
    return {
        "attempts": attempts,
        "exact_attempts": exact_attempts,
        "exact_attempt_rate": exact_attempts / attempts if attempts else 0.0,
        "mean_score": safe_mean(base.as_float(r.get("score", "0")) for r in items),
        "mean_row_set_correctness": safe_mean(base.as_float(r.get("row_set_correctness_score", "0")) for r in items),
        "mean_numeric_correctness": safe_mean(base.as_float(r.get("numeric_correctness_score", "0")) for r in items),
        "mean_sort_correctness": safe_mean(base.as_float(r.get("sort_order_correctness_score", "0")) for r in items),
        "mean_aligned_cell_accuracy": safe_mean(base.as_float(r.get("aligned_cell_accuracy", "0")) for r in items),
        "total_wall_s": sum(base.as_float(r.get("client_wall_s", "0")) for r in items),
        "avg_query_wall_s": safe_mean(base.as_float(r.get("client_wall_s", "0")) for r in items),
        "avg_gen_tps": safe_mean(base.as_float(r.get("server_gen_tps", "0")) for r in items),
        "avg_cpu_gpu_ratio": safe_mean(ratios),
        "dominant_failure_mode": modes.most_common(1)[0][0] if modes else "",
        "dominant_non_exact_failure_mode": base.dominant_non_exact_mode(modes) if modes else "",
        **{mode: modes[mode] for mode in FAILURE_MODES},
    }


def summarize_cells(cells: list[dict]) -> dict:
    attempts = sum(c["attempts"] for c in cells)
    exact_attempts = sum(c["exact_attempts"] for c in cells)
    return {
        "cells": len(cells),
        "attempts": attempts,
        "exact_attempts": exact_attempts,
        "exact_attempt_rate": exact_attempts / attempts if attempts else 0.0,
        "mean_score": safe_mean(c["mean_score"] for c in cells if c["attempts"]),
        "mean_row_set_correctness": safe_mean(c["mean_row_set_correctness"] for c in cells if c["attempts"]),
        "mean_numeric_correctness": safe_mean(c["mean_numeric_correctness"] for c in cells if c["attempts"]),
        "mean_sort_correctness": safe_mean(c["mean_sort_correctness"] for c in cells if c["attempts"]),
        "mean_aligned_cell_accuracy": safe_mean(c["mean_aligned_cell_accuracy"] for c in cells if c["attempts"]),
        "total_wall_s": sum(c["total_wall_s"] for c in cells),
        "avg_query_wall_s": safe_mean(c["avg_query_wall_s"] for c in cells if c["attempts"]),
        "avg_gen_tps": safe_mean(c["avg_gen_tps"] for c in cells if c["attempts"]),
        "avg_cpu_gpu_ratio": safe_mean(c["avg_cpu_gpu_ratio"] for c in cells if c["attempts"]),
    }


def add_summary_fields(row: dict, summary: dict, prefix: str | None = None) -> None:
    for key, value in summary.items():
        out_key = f"{prefix}_{key}" if prefix else key
        row[out_key] = value


def build_analysis(rows_by_run: dict[str, list[dict]], case_meta: dict) -> dict:
    all_rows = [row for rows in rows_by_run.values() for row in rows]
    models = sorted({r["model"] for r in all_rows}, key=lambda m: base.canonical_model_name(m))
    cases = sorted({r["case_id"] for r in all_rows}, key=case_sort_key)

    by_model_run_case = defaultdict(list)
    by_model_run_pass = defaultdict(list)
    by_model_run = defaultdict(list)
    by_model_pass = defaultdict(list)
    by_model_case = defaultdict(list)
    by_model_family = defaultdict(list)
    by_model = defaultdict(list)
    by_pass = defaultdict(list)
    by_case = defaultdict(list)
    by_family = defaultdict(list)

    for row in all_rows:
        model = row["model"]
        run = row["_run"]
        case_id = row["case_id"]
        pass_no = row["pass"]
        family = row["_family"]
        by_model_run_case[(model, run, case_id)].append(row)
        by_model_run_pass[(model, run, pass_no)].append(row)
        by_model_run[(model, run)].append(row)
        by_model_pass[(model, pass_no)].append(row)
        by_model_case[(model, case_id)].append(row)
        by_model_family[(model, family)].append(row)
        by_model[model].append(row)
        by_pass[pass_no].append(row)
        by_case[case_id].append(row)
        by_family[family].append(row)

    cell_rows = []
    cell_lookup = {}
    for model in models:
        for run in RUNS:
            for case_id in cases:
                items = by_model_run_case[(model, run, case_id)]
                summary = summarize_attempts(items)
                row = {
                    "model": model,
                    "display_model": base.canonical_model_name(model),
                    "run": run,
                    "case_id": case_id,
                    "query": query_label(case_id),
                    "pass": pass_of_case(case_id),
                    "family": items[0]["_family"] if items else case_meta[case_id].get("metadata", {}).get("failure_family_primary", ""),
                }
                add_summary_fields(row, summary)
                row["stable_exact"] = int(summary["attempts"] == EXPECTED_REPEATS and summary["exact_attempts"] == EXPECTED_REPEATS)
                row["unstable_exact"] = int(0 < summary["exact_attempts"] < summary["attempts"])
                row["stable_fail"] = int(summary["attempts"] > 0 and summary["exact_attempts"] == 0)
                row["missing_cell"] = int(summary["attempts"] == 0)
                cell_rows.append(row)
                cell_lookup[(model, run, case_id)] = row

    model_rows = []
    model_run_rows = []
    model_pass_rows = []
    model_run_pass_rows = []
    model_query_rows = []
    family_rows = []
    query_rows = []

    for model in models:
        display = base.canonical_model_name(model)
        model_cells = [c for c in cell_rows if c["model"] == model]
        summary = summarize_cells(model_cells)
        attempts_summary = summarize_attempts(by_model[model])
        row = {"model": model, "display_model": display}
        add_summary_fields(row, summary)
        row["stable_exact_cells"] = sum(c["stable_exact"] for c in model_cells)
        row["unstable_exact_cells"] = sum(c["unstable_exact"] for c in model_cells)
        row["stable_fail_cells"] = sum(c["stable_fail"] for c in model_cells)
        row["missing_cells"] = sum(c["missing_cell"] for c in model_cells)
        row["query_coverage_any_exact"] = sum(
            any(c["exact_attempts"] > 0 for c in model_cells if c["case_id"] == case_id) for case_id in cases
        )
        row["expected_attempts"] = EXPECTED_ATTEMPTS_PER_MODEL_ALL_RUNS
        row["attempt_coverage"] = summary["attempts"] / row["expected_attempts"] if row["expected_attempts"] else 0.0
        row["dominant_non_exact_failure_mode"] = attempts_summary["dominant_non_exact_failure_mode"]
        model_rows.append(row)

        for run in RUNS:
            run_cells = [c for c in model_cells if c["run"] == run]
            run_summary = summarize_cells(run_cells)
            run_row = {"model": model, "display_model": display, "run": run}
            add_summary_fields(run_row, run_summary)
            run_row["stable_exact_cells"] = sum(c["stable_exact"] for c in run_cells)
            run_row["unstable_exact_cells"] = sum(c["unstable_exact"] for c in run_cells)
            run_row["stable_fail_cells"] = sum(c["stable_fail"] for c in run_cells)
            model_run_rows.append(run_row)

        for pass_no in PASSES:
            pass_cells = [c for c in model_cells if c["pass"] == pass_no]
            pass_summary = summarize_cells(pass_cells)
            pass_row = {"model": model, "display_model": display, "pass": pass_no}
            add_summary_fields(pass_row, pass_summary)
            model_pass_rows.append(pass_row)

        for run in RUNS:
            for pass_no in PASSES:
                items = by_model_run_pass[(model, run, pass_no)]
                summary = summarize_attempts(items)
                run_pass_row = {
                    "model": model,
                    "display_model": display,
                    "run": run,
                    "pass": pass_no,
                    "expected_attempts": EXPECTED_ATTEMPTS_PER_MODEL_PASS,
                    "attempt_coverage": summary["attempts"] / EXPECTED_ATTEMPTS_PER_MODEL_PASS,
                }
                add_summary_fields(run_pass_row, summary)
                model_run_pass_rows.append(run_pass_row)

        for case_id in cases:
            case_cells = [c for c in model_cells if c["case_id"] == case_id]
            case_summary = summarize_cells(case_cells)
            case_row = {
                "model": model,
                "display_model": display,
                "case_id": case_id,
                "query": query_label(case_id),
                "pass": pass_of_case(case_id),
            }
            add_summary_fields(case_row, case_summary)
            model_query_rows.append(case_row)

    families = []
    for case_id in cases:
        family = case_meta[case_id].get("metadata", {}).get("failure_family_primary", "")
        if family and family not in families:
            families.append(family)
    for family in sorted(set(r["_family"] for r in all_rows)):
        if family and family not in families:
            families.append(family)

    for model in models:
        display = base.canonical_model_name(model)
        for family in families:
            items = by_model_family[(model, family)]
            summary = summarize_attempts(items)
            row = {"model": model, "display_model": display, "family": family}
            add_summary_fields(row, summary)
            family_rows.append(row)

    for case_id in cases:
        items = by_case[case_id]
        summary = summarize_attempts(items)
        row = {
            "case_id": case_id,
            "query": query_label(case_id),
            "pass": pass_of_case(case_id),
            "family": case_meta[case_id].get("metadata", {}).get("failure_family_primary", items[0]["_family"] if items else ""),
        }
        add_summary_fields(row, summary)
        query_rows.append(row)

    pass_rows = []
    for pass_no in PASSES:
        summary = summarize_attempts(by_pass[pass_no])
        row = {"pass": pass_no, "pass_label": PASS_LABELS[pass_no]}
        add_summary_fields(row, summary)
        pass_rows.append(row)

    query_legend = []
    for case_id in cases:
        meta = case_meta[case_id]
        metadata = meta.get("metadata", {})
        prompt = " ".join(str(meta.get("prompt", "")).split())
        query_legend.append(
            {
                "query": query_label(case_id),
                "case_id": case_id,
                "pass": pass_of_case(case_id),
                "query_no": str(meta.get("query", "")),
                "difficulty": meta.get("difficulty", ""),
                "language": meta.get("language", ""),
                "failure_family_primary": metadata.get("failure_family_primary", ""),
                "failure_families": json.dumps(metadata.get("failure_families", [])),
                "prompt_preview": prompt[:220],
            }
        )

    model_rows.sort(key=lambda r: (-r["mean_score"], -r["exact_attempt_rate"], r["display_model"]))
    order = {r["model"]: idx for idx, r in enumerate(model_rows)}
    model_run_rows.sort(key=lambda r: (order[r["model"]], RUNS.index(r["run"])))
    model_pass_rows.sort(key=lambda r: (order[r["model"]], int(r["pass"])))
    model_query_rows.sort(key=lambda r: (order[r["model"]], case_sort_key(r["case_id"])))
    family_rows.sort(key=lambda r: (order[r["model"]], families.index(r["family"]) if r["family"] in families else 999))
    query_rows.sort(key=lambda r: case_sort_key(r["case_id"]))

    return {
        "models": models,
        "model_order": [r["model"] for r in model_rows],
        "cases": cases,
        "families": families,
        "all_rows": all_rows,
        "cell_rows": cell_rows,
        "model_rows": model_rows,
        "model_run_rows": model_run_rows,
        "model_pass_rows": model_pass_rows,
        "model_run_pass_rows": model_run_pass_rows,
        "model_query_rows": model_query_rows,
        "family_rows": family_rows,
        "query_rows": query_rows,
        "pass_rows": pass_rows,
        "query_legend": query_legend,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def style_axis(ax) -> None:
    ax.set_facecolor(base.PANEL_BG)
    ax.tick_params(colors=base.TEXT, labelsize=8)
    ax.xaxis.label.set_color(base.TEXT)
    ax.yaxis.label.set_color(base.TEXT)
    ax.title.set_color(base.TEXT)
    for spine in ax.spines.values():
        spine.set_color(base.GRID)


def set_legend_text_color(legend) -> None:
    if legend is None:
        return
    for text in legend.get_texts():
        text.set_color(base.TEXT)


def score_cmap():
    return LinearSegmentedColormap.from_list("score_blues", [base.BLUE_DARK, base.BLUE, base.BLUE_LIGHT, base.BLUE_PALE])


def delta_cmap():
    return LinearSegmentedColormap.from_list("delta_blues", [base.BLUE_DARK, base.BLUE, base.BLUE_LIGHT, base.BLUE_PALE])


def make_colorbar(fig, im, ax, label: str = ""):
    cbar = fig.colorbar(im, ax=ax, fraction=0.026, pad=0.015)
    cbar.ax.tick_params(labelsize=7, colors=base.TEXT)
    cbar.outline.set_edgecolor(base.GRID)
    if label:
        cbar.set_label(label, color=base.TEXT)
    return cbar


def render_page1(data: dict):
    model_rows = data["model_rows"]
    model_order = data["model_order"]
    model_labels = [base.wrap_display_name(base.canonical_model_name(m)) for m in model_order]
    model_lookup = {r["model"]: r for r in model_rows}
    run_pass_lookup = {(r["model"], r["run"], r["pass"]): r for r in data["model_run_pass_rows"]}
    run_lookup = {(r["model"], r["run"]): r for r in data["model_run_rows"]}
    pass_lookup = {(r["model"], r["pass"]): r for r in data["model_pass_rows"]}

    fig = plt.figure(figsize=(23, 16), facecolor=base.PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(3, 4, height_ratios=[1.0, 1.05, 1.0])
    fig.suptitle(
        f"{SCOPE_TITLE}, Runs v2-v5: Who is Good, Stable, and Improving?",
        fontsize=23,
        fontweight="bold",
        color=base.TEXT,
    )

    ax1 = fig.add_subplot(gs[0, 0:2])
    coverage_matrix = []
    coverage_text = []
    col_labels = []
    for pass_no in PASSES:
        for run in RUNS:
            col_labels.append(f"{run}\nP{pass_no}")
    for model in model_order:
        row = []
        text_row = []
        for pass_no in PASSES:
            for run in RUNS:
                item = run_pass_lookup[(model, run, pass_no)]
                row.append(item["attempt_coverage"])
                text_row.append(f"{int(item['exact_attempts'])}/{int(item['attempts'])}")
        coverage_matrix.append(row)
        coverage_text.append(text_row)
    im = ax1.imshow(coverage_matrix, aspect="auto", cmap=score_cmap(), vmin=0, vmax=1)
    ax1.set_xticks(range(len(col_labels)), col_labels)
    ax1.set_yticks(range(len(model_order)), model_labels)
    ax1.set_title(
        f"1. Benchmark Coverage Audit\n{len(PASSES)} pass blocks; within each block columns are v2-v5; text = exact / observed",
        fontweight="bold",
    )
    for i, row in enumerate(coverage_text):
        for j, value in enumerate(row):
            ax1.text(j, i, value, ha="center", va="center", color=base.PAGE_BG if coverage_matrix[i][j] >= 0.95 else base.TEXT, fontsize=7)
    for boundary in [idx * len(RUNS) - 0.5 for idx in range(1, len(PASSES))]:
        ax1.axvline(boundary, color=base.GRID, linewidth=1.3)
    for idx, pass_no in enumerate(PASSES):
        center = idx * len(RUNS) + (len(RUNS) - 1) / 2
        ax1.text(
            center,
            -0.30,
            PASS_LABELS[pass_no],
            transform=ax1.get_xaxis_transform(),
            ha="center",
            va="top",
            color=base.BLUE_PALE,
            fontsize=8,
            fontweight="bold",
            clip_on=False,
        )
    make_colorbar(fig, im, ax1, "coverage")
    style_axis(ax1)

    ax2 = fig.add_subplot(gs[0, 2:4])
    ordered = model_rows
    y = list(range(len(ordered)))
    bars = ax2.barh(y, [r["mean_score"] for r in ordered], color=base.BLUE_LIGHT, edgecolor=base.PANEL_BG, label="Macro weighted score")
    ax2.scatter([r["exact_attempt_rate"] for r in ordered], y, s=88, color=base.BLUE_PALE, edgecolors=base.PAGE_BG, linewidth=0.9, label="Exact attempt rate")
    ax2.set_yticks(y, [base.wrap_display_name(r["display_model"]) for r in ordered])
    ax2.invert_yaxis()
    ax2.set_xlim(0, 1.02)
    ax2.set_xlabel("Score / rate")
    ax2.set_title("2. Overall Model Leaderboard\nranked by macro weighted mean_score; exactness shown as dot", fontweight="bold")
    for idx, row in enumerate(ordered):
        ax2.text(
            min(row["mean_score"] + 0.015, 0.99),
            idx,
            f"{int(row['exact_attempts'])}/{int(row['attempts'])} exact | stable {int(row['stable_exact_cells'])}/{EXPECTED_QUERY_RUN_CELLS} | covered {int(row['query_coverage_any_exact'])}/{TOTAL_QUERY_COUNT}",
            va="center",
            color=base.TEXT,
            fontsize=7,
        )
    ax2.grid(axis="x", color=base.GRID, linewidth=0.8, alpha=0.75)
    set_legend_text_color(ax2.legend(frameon=False, loc="lower right", fontsize=8))
    style_axis(ax2)

    ax3 = fig.add_subplot(gs[1, 0:2])
    exact_rates = [r["exact_attempt_rate"] for r in model_rows]
    scores = [r["mean_score"] for r in model_rows]
    med_exact = median(exact_rates)
    med_score = median(scores)
    v5_rank_order = sorted(model_order, key=lambda m: (-run_lookup[(m, "v5")]["mean_score"], base.canonical_model_name(m)))
    rank_color_lookup = {
        model: [base.BLUE_PALE, base.BLUE_LIGHT, base.BLUE_MID, base.BLUE, base.FAIL_LIGHT, base.BLUE_DARK][idx]
        for idx, model in enumerate(v5_rank_order)
    }
    for row in model_rows:
        size = 100 + row["stable_exact_cells"] * 8
        ax3.scatter(row["exact_attempt_rate"], row["mean_score"], s=size, color=rank_color_lookup[row["model"]], edgecolors=base.PAGE_BG, linewidth=0.9, alpha=0.95)
        ax3.annotate(row["display_model"], (row["exact_attempt_rate"], row["mean_score"]), xytext=(6, 5), textcoords="offset points", color=base.TEXT, fontsize=8)
    ax3.axvline(med_exact, color=base.BLUE_LIGHT, linewidth=1.0, alpha=0.8)
    ax3.axhline(med_score, color=base.BLUE_LIGHT, linewidth=1.0, alpha=0.8)
    ax3.set_xlim(max(0, min(exact_rates) - 0.035), min(1, max(exact_rates) + 0.08))
    ax3.set_ylim(max(0, min(scores) - 0.06), min(1, max(scores) + 0.05))
    ax3.set_xlabel("Exact attempt rate")
    ax3.set_ylabel("Macro weighted mean_score")
    ax3.set_title("3. Score-vs-Exact Conversion Quadrant\nmedian lines expose near-miss models", fontweight="bold")
    ax3.text(0.03, 0.95, "High score + low exact = near-miss conversion", transform=ax3.transAxes, color=base.BLUE_PALE, fontsize=8, va="top")
    ax3.grid(color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax3)

    ax4 = fig.add_subplot(gs[1, 2:4])
    x = list(range(len(RUNS)))
    for model in model_order:
        ys = [run_lookup[(model, run)]["mean_score"] for run in RUNS]
        ax4.plot(x, ys, color=rank_color_lookup[model], linewidth=2.2, marker="o", markersize=5, alpha=0.9)
        for idx, run in enumerate(RUNS):
            exact = int(run_lookup[(model, run)]["exact_attempts"])
            ax4.text(idx, ys[idx] + 0.006, str(exact), color=base.TEXT, fontsize=7, ha="center")
        ax4.text(x[-1] + 0.06, ys[-1], base.canonical_model_name(model), color=base.TEXT, fontsize=8, va="center")
    ax4.set_xticks(x, RUNS)
    ax4.set_xlim(-0.1, len(RUNS) - 0.45)
    ax4.set_ylabel("Macro weighted mean_score")
    ax4.set_title(
        f"4. Run-to-Run Model Trajectory\npoint labels = exact attempts out of {EXPECTED_ATTEMPTS_PER_MODEL_RUN}",
        fontweight="bold",
    )
    ax4.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax4)

    ax5 = fig.add_subplot(gs[2, 0:2])
    degradation = [[pass_lookup[(model, pass_no)]["mean_score"] for pass_no in PASSES] for model in model_order]
    per_pass_expected_all_runs = len(RUNS) * EXPECTED_ATTEMPTS_PER_MODEL_PASS
    degradation_text = [[f"{int(pass_lookup[(model, pass_no)]['exact_attempts'])}/{per_pass_expected_all_runs}" for pass_no in PASSES] for model in model_order]
    im = ax5.imshow(degradation, aspect="auto", cmap=score_cmap(), vmin=0, vmax=1)
    ax5.set_xticks(range(len(PASSES)), [PASS_LABELS[p] for p in PASSES])
    ax5.set_yticks(range(len(model_order)), model_labels)
    ax5.set_title(
        f"5. Model x Pass Degradation Heatmap\nmean across v2-v5; text = exact attempts out of {per_pass_expected_all_runs}",
        fontweight="bold",
    )
    for i in range(len(model_order)):
        for j in range(len(PASSES)):
            val = degradation[i][j]
            ax5.text(j, i, degradation_text[i][j], ha="center", va="center", color=base.PAGE_BG if val >= 0.82 else base.TEXT, fontsize=8)
    make_colorbar(fig, im, ax5, "weighted score")
    style_axis(ax5)

    ax6 = fig.add_subplot(gs[2, 2:4])
    stable = [model_lookup[m]["stable_exact_cells"] for m in model_order]
    unstable = [model_lookup[m]["unstable_exact_cells"] for m in model_order]
    fail = [model_lookup[m]["stable_fail_cells"] for m in model_order]
    missing = [model_lookup[m]["missing_cells"] for m in model_order]
    bottoms = [0] * len(model_order)
    segments = [
        ("3/3 stable exact", stable, base.BLUE_PALE),
        ("1/3 or 2/3 unstable exact", unstable, base.BLUE_LIGHT),
        ("0/3 stable fail", fail, base.BLUE_DARK),
        ("missing", missing, base.FAIL_PALE),
    ]
    for label, values, color in segments:
        ax6.barh(range(len(model_order)), values, left=bottoms, color=color, edgecolor=base.PANEL_BG, label=label)
        for idx, value in enumerate(values):
            if value >= 5:
                ax6.text(bottoms[idx] + value / 2, idx, str(int(value)), ha="center", va="center", color=base.PAGE_BG if color in {base.BLUE_PALE, base.BLUE_LIGHT, base.FAIL_PALE} else base.TEXT, fontsize=8)
        bottoms = [b + v for b, v in zip(bottoms, values)]
    ax6.set_yticks(range(len(model_order)), model_labels)
    ax6.invert_yaxis()
    ax6.set_xlim(0, EXPECTED_QUERY_RUN_CELLS)
    ax6.set_xlabel("Model-query-run cells out of 120")
    ax6.set_title("6. Repeatability Fingerprint\nsame query repeated 3 times in each run", fontweight="bold")
    ax6.grid(axis="x", color=base.GRID, linewidth=0.8, alpha=0.75)
    set_legend_text_color(ax6.legend(frameon=False, loc="lower right", fontsize=8))
    style_axis(ax6)

    return fig


def median(values: list[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def render_page2(data: dict):
    model_order = data["model_order"]
    model_labels = [base.wrap_display_name(base.canonical_model_name(m)) for m in model_order]
    cases = data["cases"]
    families = data["families"]
    model_query_lookup = {(r["model"], r["case_id"]): r for r in data["model_query_rows"]}
    family_lookup = {(r["model"], r["family"]): r for r in data["family_rows"]}
    query_lookup = {r["case_id"]: r for r in data["query_rows"]}
    pass_lookup = {(r["model"], r["pass"]): r for r in data["model_pass_rows"]}
    run_pass_lookup = {(r["model"], r["run"], r["pass"]): r for r in data["model_run_pass_rows"]}
    run_lookup = {(r["model"], r["run"]): r for r in data["model_run_rows"]}

    page_height = 20 if len(PASSES) <= 3 else 23
    page_width = 23 if len(PASSES) <= 3 else 26
    fig = plt.figure(figsize=(page_width, page_height), facecolor=base.PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(4, 4, height_ratios=[1.0, 1.2, 1.05, 1.05])
    fig.suptitle(
        f"{SCOPE_TITLE}, Runs v2-v5: Where and Why Do Models Fail?",
        fontsize=23,
        fontweight="bold",
        color=base.TEXT,
    )

    ax7 = fig.add_subplot(gs[0, :])
    matrix = [[model_query_lookup[(model, case_id)]["mean_score"] for case_id in cases] for model in model_order]
    im = ax7.imshow(matrix, aspect="auto", cmap=score_cmap(), vmin=0, vmax=1)
    ax7.set_xticks(range(len(cases)), [query_label(c) for c in cases], rotation=55, ha="right")
    ax7.set_yticks(range(len(model_order)), model_labels)
    ax7.set_title(
        f"7. Full {TOTAL_QUERY_COUNT}-Query Model x Query Heatmap\ncell colour = macro weighted score across v2-v5; text = exact attempts out of 12",
        fontweight="bold",
    )
    for i, model in enumerate(model_order):
        for j, case_id in enumerate(cases):
            item = model_query_lookup[(model, case_id)]
            val = item["mean_score"]
            ax7.text(j, i, str(int(item["exact_attempts"])), ha="center", va="center", color=base.PAGE_BG if val >= 0.82 else base.TEXT, fontsize=7)
    for boundary in [idx * EXPECTED_QUERIES_PER_PASS - 0.5 for idx in range(1, len(PASSES))]:
        ax7.axvline(boundary, color=base.GRID, linewidth=1.6)
    for idx, pass_no in enumerate(PASSES):
        center = idx * EXPECTED_QUERIES_PER_PASS + (EXPECTED_QUERIES_PER_PASS - 1) / 2
        ax7.text(
            center,
            -0.34,
            PASS_LABELS[pass_no],
            transform=ax7.get_xaxis_transform(),
            ha="center",
            va="top",
            color=base.BLUE_PALE,
            fontsize=8,
            fontweight="bold",
            clip_on=False,
        )
    make_colorbar(fig, im, ax7, "weighted score")
    style_axis(ax7)

    ax8 = fig.add_subplot(gs[1, 0:2])
    query_sorted = sorted(data["query_rows"], key=lambda r: (r["mean_score"], r["exact_attempt_rate"], r["query"]))
    y = list(range(len(query_sorted)))
    for idx, row in enumerate(query_sorted):
        color = PASS_COLORS.get(row["pass"], base.BLUE_LIGHT)
        ax8.hlines(idx, 0, row["mean_score"], color=color, linewidth=2.0, alpha=0.75)
        ax8.scatter(row["mean_score"], idx, s=55, color=color, edgecolors=base.PAGE_BG, label=PASS_LABELS[row["pass"]] if PASS_LABELS[row["pass"]] not in ax8.get_legend_handles_labels()[1] else None)
        ax8.scatter(row["exact_attempt_rate"], idx, s=36, color=base.BLUE_PALE, marker="x", linewidth=1.5)
    ax8.set_yticks(y, [r["query"] for r in query_sorted])
    ax8.tick_params(axis="y", labelsize=6 if TOTAL_QUERY_COUNT > 30 else 7)
    ax8.set_xlim(0, 1.02)
    ax8.set_xlabel("Weighted score / exact rate")
    ax8.set_title("8. Query Difficulty Ranking\ncompact query IDs; family/detail live in query legend CSV", fontweight="bold")
    ax8.grid(axis="x", color=base.GRID, linewidth=0.8, alpha=0.75)
    set_legend_text_color(ax8.legend(frameon=False, loc="lower right", fontsize=8))
    style_axis(ax8)

    ax9 = fig.add_subplot(gs[1, 2:4])
    family_matrix = [[family_lookup[(model, family)]["mean_score"] for family in families] for model in model_order]
    im = ax9.imshow(family_matrix, aspect="auto", cmap=score_cmap(), vmin=0, vmax=1)
    ax9.set_xticks(range(len(families)), [wrap_label(f, 13) for f in families], rotation=0)
    ax9.set_yticks(range(len(model_order)), model_labels)
    ax9.set_title("9. Exposure-Normalised Failure-Family Heatmap\ncell value = mean weighted score within family", fontweight="bold")
    for i in range(len(model_order)):
        for j in range(len(families)):
            val = family_matrix[i][j]
            if val > 0:
                ax9.text(j, i, f"{val:.2f}", ha="center", va="center", color=base.PAGE_BG if val >= 0.82 else base.TEXT, fontsize=7)
    make_colorbar(fig, im, ax9, "weighted score")
    style_axis(ax9)

    ax10 = fig.add_subplot(gs[2, 0:2])
    mode_by_pass = {}
    for pass_no in PASSES:
        rows = [r for r in data["all_rows"] if r["pass"] == pass_no]
        total = len(rows)
        counts = Counter(r["_failure_mode"] for r in rows)
        mode_by_pass[pass_no] = {mode: counts[mode] / total if total else 0.0 for mode in FAILURE_MODES}
    bottoms = [0.0] * len(PASSES)
    for mode in FAILURE_MODES:
        vals = [mode_by_pass[p][mode] for p in PASSES]
        ax10.bar(range(len(PASSES)), vals, bottom=bottoms, color=FAILURE_MODE_COLORS[mode], edgecolor=base.PANEL_BG, label=FAILURE_MODE_LABELS[mode])
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax10.set_xticks(range(len(PASSES)), [PASS_LABELS[p] for p in PASSES])
    ax10.set_ylim(0, 1)
    ax10.set_ylabel("Share of attempts")
    ax10.set_title("10. Failure Mode Composition by Pass\nnormalised across v2-v5 and all models", fontweight="bold")
    ax10.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    set_legend_text_color(ax10.legend(frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=7))
    style_axis(ax10)

    ax11 = fig.add_subplot(gs[2, 2:4])
    component_rows = []
    component_labels = []
    for model in model_order:
        for pass_no in PASSES:
            row = pass_lookup[(model, pass_no)]
            component_rows.append([row[key] for key, _ in COMPONENTS])
            component_labels.append(f"{short_model_label(model)} P{pass_no}")
    im = ax11.imshow(component_rows, aspect="auto", cmap=score_cmap(), vmin=0, vmax=1)
    ax11.set_xticks(range(len(COMPONENTS)), [label for _, label in COMPONENTS])
    ax11.set_yticks(range(len(component_labels)), component_labels)
    ax11.set_title("11. Component Bottleneck Matrix\nasterisk marks the weakest correctness component per model-pass", fontweight="bold")
    for i, row in enumerate(component_rows):
        correctness_values = row[1:]
        min_index = correctness_values.index(min(correctness_values)) + 1
        for j, val in enumerate(row):
            suffix = "*" if j == min_index else ""
            ax11.text(j, i, f"{val:.2f}{suffix}", ha="center", va="center", color=base.PAGE_BG if val >= 0.82 else base.TEXT, fontsize=7)
    make_colorbar(fig, im, ax11, "component score")
    style_axis(ax11)

    ax12 = fig.add_subplot(gs[3, :])
    delta_columns = []
    delta_values = []
    delta_exact_text = []
    for model in model_order:
        row_values = []
        row_text = []
        for end, start in RUN_PAIRS:
            for pass_no in (*PASSES, "total"):
                delta_columns.append((end, start, pass_no)) if model == model_order[0] else None
                if pass_no == "total":
                    end_row = run_lookup[(model, end)]
                    start_row = run_lookup[(model, start)]
                else:
                    end_row = run_pass_lookup[(model, end, pass_no)]
                    start_row = run_pass_lookup[(model, start, pass_no)]
                row_values.append(end_row["mean_score"] - start_row["mean_score"])
                row_text.append(int(end_row["exact_attempts"] - start_row["exact_attempts"]))
        delta_values.append(row_values)
        delta_exact_text.append(row_text)
    max_abs = max(abs(v) for row in delta_values for v in row) or 0.01
    im = ax12.imshow(delta_values, aspect="auto", cmap=delta_cmap(), vmin=-max_abs, vmax=max_abs)
    col_labels = [f"{end}-{start}\n{('Total' if p == 'total' else 'P' + p)}" for end, start, p in delta_columns]
    ax12.set_xticks(range(len(col_labels)), col_labels)
    ax12.set_yticks(range(len(model_order)), model_labels)
    ax12.set_title("12. Run Delta Heatmap\ncolour = weighted score delta; text = exact-attempt delta", fontweight="bold")
    for i in range(len(model_order)):
        for j, val in enumerate(delta_values[i]):
            ax12.text(j, i, f"{delta_exact_text[i][j]:+d}", ha="center", va="center", color=base.PAGE_BG if val > max_abs * 0.45 else base.TEXT, fontsize=7)
    for boundary in (3.5, 7.5, 11.5):
        ax12.axvline(boundary, color=base.GRID, linewidth=1.4)
    make_colorbar(fig, im, ax12, "score delta")
    style_axis(ax12)

    return fig


def write_report(path: Path, data: dict, dirs_by_run: dict[str, Path]) -> None:
    model_rows = data["model_rows"]
    model_run_lookup = {(r["model"], r["run"]): r for r in data["model_run_rows"]}
    query_sorted = sorted(data["query_rows"], key=lambda r: (r["mean_score"], r["exact_attempt_rate"]))
    total_attempts = sum(r["attempts"] for r in model_rows)
    total_exact = sum(r["exact_attempts"] for r in model_rows)
    best = model_rows[0]
    worst = model_rows[-1]
    lines = [
        f"# {SCOPE_TITLE} v2-v5 Comparison",
        "",
        f"Scope: runs v2, v3, v4, and v5; {SCOPE_DESCRIPTION}.",
        "",
        "## Sources",
        "",
    ]
    for run in RUNS:
        lines.append(f"- {run}: `{dirs_by_run[run]}`")

    lines.extend(
        [
            "",
            "## Headline",
            "",
            f"- Coverage is balanced for this comparison: {len(model_rows)} models, {len(RUNS)} runs, {len(PASSES)} passes, {total_attempts} observed attempts.",
            f"- Exactness remains strict and sparse: {total_exact}/{total_attempts} exact attempts overall.",
            f"- Top macro weighted model across v2-v5 is {best['display_model']} at {best['mean_score']:.3f}; lowest is {worst['display_model']} at {worst['mean_score']:.3f}.",
            f"- Hardest aggregate query is {query_sorted[0]['query']} ({query_sorted[0]['family']}) with weighted score {query_sorted[0]['mean_score']:.3f} and exact rate {query_sorted[0]['exact_attempt_rate']:.1%}.",
            "",
            "## Hidden Factors Checked",
            "",
            "- Attempt coverage is shown first because missing runs, dropped models, or failed repeats would make score deltas misleading.",
            "- Leaderboards are ranked by the existing weighted `score`/`mean_score`, not by numeric correctness alone and not by an unweighted component average.",
            "- Exactness is treated as a conversion outcome; high weighted score with low exact rate is interpreted as a near-miss class, not as a total capability failure.",
            "- Repeatability is counted at model-query-run level because each query has three repeats. A 3/3 exact cell is different from a 1/3 or 2/3 cell.",
            "- Failure-family results are exposure-normalised by mean score within the family, not raw counts, so common families do not dominate just because they appear more often.",
            "- Run deltas are separated into v3-v2, v4-v3, v5-v4, and v5-v2 so prompt-engineering effects are not collapsed into one average.",
            "",
            "## Model Summary",
            "",
            "| Model | Macro weighted score | Exact attempts | Exact rate | Stable exact cells | Unstable exact cells | Query coverage | v2 score | v3 score | v4 score | v5 score |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in model_rows:
        run_scores = [model_run_lookup[(row["model"], run)]["mean_score"] for run in RUNS]
        lines.append(
            f"| {row['display_model']} | {row['mean_score']:.3f} | {int(row['exact_attempts'])}/{int(row['attempts'])} | {row['exact_attempt_rate']:.1%} | "
            f"{int(row['stable_exact_cells'])} | {int(row['unstable_exact_cells'])} | {int(row['query_coverage_any_exact'])}/{TOTAL_QUERY_COUNT} | "
            f"{run_scores[0]:.3f} | {run_scores[1]:.3f} | {run_scores[2]:.3f} | {run_scores[3]:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Query Difficulty Bottom 10",
            "",
            "| Query | Family | Weighted score | Exact attempts | Exact rate | Dominant non-exact mode |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for row in query_sorted[:10]:
        lines.append(
            f"| {row['query']} | {row['family']} | {row['mean_score']:.3f} | {int(row['exact_attempts'])}/{int(row['attempts'])} | {row['exact_attempt_rate']:.1%} | {row['dominant_non_exact_failure_mode']} |"
        )

    lines.extend(
        [
            "",
            "## Query Legend",
            "",
            "| Query | Case ID | Primary family | Prompt preview |",
            "|---|---|---|---|",
        ]
    )
    for row in data["query_legend"]:
        prompt = row["prompt_preview"].replace("|", "\\|")
        lines.append(f"| {row['query']} | `{row['case_id']}` | {row['failure_family_primary']} | {prompt} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_figures(fig1, fig2, out_dir: Path, prefix: str) -> None:
    page1_base = out_dir / f"{prefix}_visual_report_page1"
    page2_base = out_dir / f"{prefix}_visual_report_page2"
    fig1.savefig(page1_base.with_suffix(".png"), dpi=220, facecolor=fig1.get_facecolor())
    fig1.savefig(page1_base.with_suffix(".svg"), facecolor=fig1.get_facecolor())
    fig2.savefig(page2_base.with_suffix(".png"), dpi=220, facecolor=fig2.get_facecolor())
    fig2.savefig(page2_base.with_suffix(".svg"), facecolor=fig2.get_facecolor())
    with PdfPages(out_dir / f"{prefix}_two_page_visual_report.pdf") as pdf:
        pdf.savefig(fig1, facecolor=fig1.get_facecolor())
        pdf.savefig(fig2, facecolor=fig2.get_facecolor())
    plt.close(fig1)
    plt.close(fig2)


def run_comparison(dirs_by_run: dict[str, Path], out_dir: Path, prefix: str = DEFAULT_PREFIX) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir.mkdir(parents=True, exist_ok=True)
    case_meta = load_case_meta(repo_root)
    rows_by_run = {run: load_rows(path, run, case_meta) for run, path in dirs_by_run.items()}
    data = build_analysis(rows_by_run, case_meta)

    for name in (
        "cell_rows",
        "model_rows",
        "model_run_rows",
        "model_pass_rows",
        "model_run_pass_rows",
        "model_query_rows",
        "family_rows",
        "query_rows",
        "pass_rows",
        "query_legend",
    ):
        write_csv(out_dir / f"{prefix}_{name}.csv", data[name])

    fig1 = render_page1(data)
    fig2 = render_page2(data)
    save_figures(fig1, fig2, out_dir, prefix)
    write_report(out_dir / f"{prefix}_comparison_report.md", data, dirs_by_run)
    return out_dir


def default_dirs(repo_root: Path) -> dict[str, Path]:
    return {run: repo_root / "results" / f"photosynthesis_snowflake_{run}" for run in RUNS}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    args = sys.argv[1:]
    scope = "pass123"
    if args and args[0] in {"--all-passes", "--pass12345", "--scope=all", "all"}:
        scope = "all"
        args = args[1:]
    elif args and args[0] in {"--pass123", "--scope=pass123", "pass123"}:
        scope = "pass123"
        args = args[1:]

    try:
        configure_scope(scope)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if len(args) == 0:
        dirs = default_dirs(repo_root)
        out_dir = dirs["v5"] / DEFAULT_OUTPUT_DIR_NAME
    elif len(args) == 5:
        dirs = {run: Path(arg).resolve() for run, arg in zip(RUNS, args[:4])}
        out_dir = Path(args[4]).resolve()
    else:
        print(
            "usage: pass123_v2_v3_v4_v5_comparison.py [--all-passes] [<v2_results_dir> <v3_results_dir> <v4_results_dir> <v5_results_dir> <out_dir>]",
            file=sys.stderr,
        )
        return 2
    run_comparison(dirs, out_dir, DEFAULT_PREFIX)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
