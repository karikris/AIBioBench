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

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import pass4_analysis as base


PASSES = ("1", "2", "3")
PASS_LABELS = {"1": "Pass 1", "2": "Pass 2", "3": "Pass 3", "total": "Total"}
SCOPE_TITLE = "Passes 1-3"
SCOPE_DESCRIPTION = "Passes 1, 2, and 3 only; 30 SQL tasks per model and 3 repeats per task."
RUNTIME_SCOPE_LABEL = "across Passes 1-3"
RUN_LABELS = ("v2", "v3", "v4")
RUN_COLORS = {"v2": base.BLUE_DARK, "v3": base.BLUE, "v4": base.BLUE_PALE}
RUN_MARKERS = {"v2": "o", "v3": "^", "v4": "s"}
DEFAULT_OUTPUT_PREFIX = "pass123_v2_v3_v4"

FAILURE_MODES = (
    "exact",
    "same_count_wrong_values",
    "row_count_mismatch",
    "order_only",
    "type_only",
    "column_error",
    "invalid_json_or_error",
)
QUALITY_COMPONENTS = (
    ("mean_row_set_correctness", "Row-set"),
    ("mean_numeric_correctness", "Numeric"),
    ("mean_sort_correctness", "Sort"),
)
SUMMARY_KEYS = [
    "attempts",
    "exact_attempts",
    "exact_attempt_rate",
    "mean_score",
    "mean_row_set_correctness",
    "mean_numeric_correctness",
    "mean_sort_correctness",
    "mean_aligned_cell_accuracy",
    "total_wall_s",
    "avg_query_wall_s",
    "avg_gen_tps",
    "avg_cpu_gpu_ratio",
    "dominant_failure_mode",
    "dominant_non_exact_failure_mode",
]
DELTA_METRICS = (
    "exact_attempts",
    "exact_attempt_rate",
    "mean_score",
    "mean_row_set_correctness",
    "mean_numeric_correctness",
    "mean_sort_correctness",
    "mean_aligned_cell_accuracy",
    "total_wall_s",
    "avg_query_wall_s",
    "avg_gen_tps",
    "avg_cpu_gpu_ratio",
)
QUALITY_DELTA_METRICS = (
    "exact_attempts",
    "exact_attempt_rate",
    "mean_score",
    "mean_row_set_correctness",
    "mean_numeric_correctness",
    "mean_sort_correctness",
    "mean_aligned_cell_accuracy",
)
DELTA_PAIRS = (("v3", "v2"), ("v4", "v3"), ("v4", "v2"))


def case_sort_key(case_id: str) -> tuple[int, int]:
    left, right = case_id.split(".query")
    return int(left.replace("pass", "")), int(right)


def query_label(case_id: str) -> str:
    pass_no, query_no = case_sort_key(case_id)
    return f"P{pass_no} Q{query_no}"


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
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["pass"] not in PASSES:
                continue
            row["_run"] = run_label
            row["_failure_mode"] = base.classify_failure(row)
            meta = case_meta.get(row["case_id"], {})
            row["_family"] = row.get("failure_family_primary_case") or meta.get("metadata", {}).get("failure_family_primary", "")
            row["_display_model"] = base.canonical_model_name(row["model"])
            rows.append(row)
    return rows


def avg(values) -> float:
    values = list(values)
    return mean(values) if values else 0.0


def cpu_gpu_ratio(row: dict) -> float | None:
    cpu = base.as_float(row.get("ollama_cpu_avg", "0"))
    if cpu <= 0:
        cpu = base.as_float(row.get("system_cpu_avg", "0"))
    if cpu <= 0:
        return None
    gpu = base.as_float(row.get("gpu_util_pct_avg", "0"))
    if gpu <= 0:
        gpu = base.as_float(row.get("gpu_mem_util_pct_avg", "0"))
    if gpu <= 0:
        gpu = 1.0
    return cpu / gpu


def summarize_items(items: list[dict]) -> dict:
    modes = Counter(r["_failure_mode"] for r in items)
    attempts = len(items)
    exact_attempts = sum(base.as_bool(r["exact_match"]) for r in items)
    cpu_gpu_ratios = [ratio for r in items if (ratio := cpu_gpu_ratio(r)) is not None]
    return {
        "attempts": attempts,
        "exact_attempts": exact_attempts,
        "exact_attempt_rate": exact_attempts / attempts if attempts else 0.0,
        "mean_score": avg(base.as_float(r["score"]) for r in items),
        "mean_aligned_cell_accuracy": avg(base.as_float(r["aligned_cell_accuracy"]) for r in items),
        "mean_row_set_correctness": avg(base.as_float(r["row_set_correctness_score"]) for r in items),
        "mean_numeric_correctness": avg(base.as_float(r["numeric_correctness_score"]) for r in items),
        "mean_sort_correctness": avg(base.as_float(r["sort_order_correctness_score"]) for r in items),
        "total_wall_s": sum(base.as_float(r["client_wall_s"]) for r in items),
        "avg_query_wall_s": avg(base.as_float(r["client_wall_s"]) for r in items),
        "avg_gen_tps": avg(base.as_float(r["server_gen_tps"]) for r in items),
        "avg_cpu_gpu_ratio": avg(cpu_gpu_ratios),
        "dominant_failure_mode": modes.most_common(1)[0][0] if modes else "",
        "dominant_non_exact_failure_mode": base.dominant_non_exact_mode(modes) if modes else "none",
        **{mode: modes[mode] for mode in FAILURE_MODES},
    }


def add_prefixed(out: dict, prefix: str, summary: dict, keys: list[str]) -> None:
    for key in keys:
        out[f"{prefix}_{key}"] = summary.get(key, 0)


def add_deltas(row: dict, metrics=DELTA_METRICS, modes=True) -> None:
    for end, start in DELTA_PAIRS:
        pair = f"{end}_{start}"
        for metric in metrics:
            row[f"delta_{pair}_{metric}"] = float(row[f"{end}_{metric}"]) - float(row[f"{start}_{metric}"])
        if modes:
            for mode in FAILURE_MODES:
                row[f"delta_{pair}_{mode}"] = int(row[f"{end}_{mode}"]) - int(row[f"{start}_{mode}"])


def index_rows(rows: list[dict], key_fields: tuple[str, ...]) -> dict:
    return {tuple(row[field] for field in key_fields): row for row in rows}


def trajectory_label(v2: float, v3: float, v4: float, tolerance: float = 0.002) -> str:
    d32 = v3 - v2
    d43 = v4 - v3
    if abs(d32) <= tolerance and abs(d43) <= tolerance:
        return "stable"
    if d32 > tolerance and d43 > tolerance:
        return "improved twice"
    if d32 < -tolerance and d43 < -tolerance:
        return "declined twice"
    if d32 > tolerance and d43 < -tolerance:
        return "v3 gain then v4 loss"
    if d32 < -tolerance and d43 > tolerance:
        return "v3 loss then v4 recovery"
    if d43 > tolerance:
        return "v4 improvement"
    if d43 < -tolerance:
        return "v4 decline"
    if d32 > tolerance:
        return "v3 improvement held"
    return "v3 decline held"


def build_comparisons(rows_by_run: dict[str, list[dict]], case_meta: dict) -> dict[str, list[dict]]:
    all_models = sorted(
        {r["model"] for rows in rows_by_run.values() for r in rows},
        key=lambda m: base.canonical_model_name(m),
    )

    pass_rows = []
    for scope in (*PASSES, "total"):
        row = {"scope": scope, "scope_label": PASS_LABELS[scope]}
        for run in RUN_LABELS:
            items = rows_by_run[run] if scope == "total" else [r for r in rows_by_run[run] if r["pass"] == scope]
            summary = summarize_items(items)
            add_prefixed(row, run, summary, SUMMARY_KEYS)
            for mode in FAILURE_MODES:
                row[f"{run}_{mode}"] = summary[mode]
        add_deltas(row)
        row["trajectory"] = trajectory_label(row["v2_mean_score"], row["v3_mean_score"], row["v4_mean_score"])
        pass_rows.append(row)

    model_rows = []
    model_pass_rows = []
    model_query_rows = []
    all_cases = sorted({r["case_id"] for rows in rows_by_run.values() for r in rows}, key=case_sort_key)

    for model in all_models:
        display = base.canonical_model_name(model)
        total_row = {"model": model, "display_model": display, "scope": "total", "scope_label": "Total"}
        for run in RUN_LABELS:
            items = [r for r in rows_by_run[run] if r["model"] == model]
            summary = summarize_items(items)
            add_prefixed(total_row, run, summary, SUMMARY_KEYS)
            for mode in FAILURE_MODES:
                total_row[f"{run}_{mode}"] = summary[mode]
        add_deltas(total_row)
        total_row["trajectory"] = trajectory_label(total_row["v2_mean_score"], total_row["v3_mean_score"], total_row["v4_mean_score"])
        model_rows.append(total_row)

        for pass_no in PASSES:
            pass_row = {"model": model, "display_model": display, "scope": pass_no, "scope_label": PASS_LABELS[pass_no]}
            for run in RUN_LABELS:
                items = [r for r in rows_by_run[run] if r["model"] == model and r["pass"] == pass_no]
                summary = summarize_items(items)
                add_prefixed(pass_row, run, summary, SUMMARY_KEYS)
                for mode in FAILURE_MODES:
                    pass_row[f"{run}_{mode}"] = summary[mode]
            add_deltas(pass_row)
            pass_row["trajectory"] = trajectory_label(pass_row["v2_mean_score"], pass_row["v3_mean_score"], pass_row["v4_mean_score"])
            model_pass_rows.append(pass_row)

        for case_id in all_cases:
            query_row = {"model": model, "display_model": display, "case_id": case_id, "query": query_label(case_id)}
            for run in RUN_LABELS:
                items = [r for r in rows_by_run[run] if r["model"] == model and r["case_id"] == case_id]
                summary = summarize_items(items)
                add_prefixed(
                    query_row,
                    run,
                    summary,
                    [
                        "attempts",
                        "exact_attempts",
                        "exact_attempt_rate",
                        "mean_score",
                        "mean_aligned_cell_accuracy",
                        "mean_row_set_correctness",
                        "mean_numeric_correctness",
                        "mean_sort_correctness",
                        "dominant_non_exact_failure_mode",
                    ],
                )
                for mode in FAILURE_MODES:
                    query_row[f"{run}_{mode}"] = summary[mode]
            add_deltas(query_row, metrics=QUALITY_DELTA_METRICS)
            query_row["trajectory"] = trajectory_label(query_row["v2_mean_score"], query_row["v3_mean_score"], query_row["v4_mean_score"])
            model_query_rows.append(query_row)

    model_rows.sort(key=lambda r: (-r["delta_v4_v2_mean_score"], -r["v4_mean_score"], r["display_model"]))
    model_pass_rows.sort(key=lambda r: (r["display_model"], int(r["scope"])))

    failure_mode_rows = []
    for scope in (*PASSES, "total"):
        for mode in FAILURE_MODES:
            row = {"scope": scope, "scope_label": PASS_LABELS[scope], "failure_mode": mode}
            for run in RUN_LABELS:
                items = rows_by_run[run] if scope == "total" else [r for r in rows_by_run[run] if r["pass"] == scope]
                count = sum(1 for r in items if r["_failure_mode"] == mode)
                row[f"{run}_count"] = count
                row[f"{run}_share"] = count / len(items) if items else 0.0
            for end, start in DELTA_PAIRS:
                pair = f"{end}_{start}"
                row[f"delta_{pair}_count"] = int(row[f"{end}_count"]) - int(row[f"{start}_count"])
                row[f"delta_{pair}_share"] = row[f"{end}_share"] - row[f"{start}_share"]
            failure_mode_rows.append(row)

    family_rows = []
    for scope in (*PASSES, "total"):
        families = sorted(
            {
                r["_family"]
                for run in RUN_LABELS
                for r in rows_by_run[run]
                if scope == "total" or r["pass"] == scope
            }
        )
        for family in families:
            row = {"scope": scope, "scope_label": PASS_LABELS[scope], "failure_family": family}
            for run in RUN_LABELS:
                items = [
                    r
                    for r in rows_by_run[run]
                    if r["_family"] == family and (scope == "total" or r["pass"] == scope)
                ]
                summary = summarize_items(items)
                add_prefixed(
                    row,
                    run,
                    summary,
                    [
                        "attempts",
                        "exact_attempts",
                        "exact_attempt_rate",
                        "mean_score",
                        "mean_aligned_cell_accuracy",
                        "mean_row_set_correctness",
                        "mean_numeric_correctness",
                        "mean_sort_correctness",
                        "dominant_failure_mode",
                        "dominant_non_exact_failure_mode",
                    ],
                )
                for mode in FAILURE_MODES:
                    row[f"{run}_{mode}"] = summary[mode]
            add_deltas(row, metrics=QUALITY_DELTA_METRICS)
            row["trajectory"] = trajectory_label(row["v2_mean_score"], row["v3_mean_score"], row["v4_mean_score"])
            family_rows.append(row)

    query_rows = []
    for case_id in all_cases:
        meta = case_meta.get(case_id, {})
        all_items = [r for run in RUN_LABELS for r in rows_by_run[run] if r["case_id"] == case_id]
        first = all_items[0]
        row = {
            "case_id": case_id,
            "query": query_label(case_id),
            "pass": first.get("pass", str(meta.get("pass", ""))),
            "query_no": first.get("query", meta.get("query", "")),
            "failure_family": first.get("failure_family_primary_case") or meta.get("metadata", {}).get("failure_family_primary", ""),
        }
        for run in RUN_LABELS:
            items = [r for r in rows_by_run[run] if r["case_id"] == case_id]
            summary = summarize_items(items)
            add_prefixed(
                row,
                run,
                summary,
                [
                    "attempts",
                    "exact_attempts",
                    "exact_attempt_rate",
                    "mean_score",
                    "mean_aligned_cell_accuracy",
                    "mean_row_set_correctness",
                    "mean_numeric_correctness",
                    "mean_sort_correctness",
                    "dominant_failure_mode",
                    "dominant_non_exact_failure_mode",
                ],
            )
            for mode in FAILURE_MODES:
                row[f"{run}_{mode}"] = summary[mode]
        add_deltas(row, metrics=QUALITY_DELTA_METRICS)
        row["trajectory"] = trajectory_label(row["v2_mean_score"], row["v3_mean_score"], row["v4_mean_score"])
        query_rows.append(row)

    speed_score_rows = []
    for row in model_rows:
        for run in RUN_LABELS:
            speed_score_rows.append(
                {
                    "run": run,
                    "model": row["model"],
                    "display_model": row["display_model"],
                    "mean_score": row[f"{run}_mean_score"],
                    "exact_attempts": row[f"{run}_exact_attempts"],
                    "total_wall_s": row[f"{run}_total_wall_s"],
                    "total_wall_min": row[f"{run}_total_wall_s"] / 60.0,
                    "total_wall_hours": row[f"{run}_total_wall_s"] / 3600.0,
                    "avg_query_wall_s": row[f"{run}_avg_query_wall_s"],
                    "avg_gen_tps": row[f"{run}_avg_gen_tps"],
                    "avg_cpu_gpu_ratio": row[f"{run}_avg_cpu_gpu_ratio"],
                }
            )

    trajectory_rows = []
    for scope_name, rows in (("model", model_rows), ("query", query_rows), ("model_query", model_query_rows), ("failure_family", family_rows)):
        counts = Counter(row["trajectory"] for row in rows if row.get("scope", "total") == "total" or scope_name != "failure_family")
        for label, count in sorted(counts.items()):
            trajectory_rows.append({"scope": scope_name, "trajectory": label, "count": count})

    return {
        "pass_comparison": pass_rows,
        "model_comparison": model_rows,
        "model_pass_comparison": model_pass_rows,
        "model_query_comparison": model_query_rows,
        "failure_mode_comparison": failure_mode_rows,
        "failure_family_comparison": family_rows,
        "query_comparison": query_rows,
        "speed_score_comparison": speed_score_rows,
        "trajectory_summary": trajectory_rows,
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
    ax.tick_params(colors=base.TEXT, labelsize=9)
    ax.xaxis.label.set_color(base.TEXT)
    ax.yaxis.label.set_color(base.TEXT)
    ax.title.set_color(base.TEXT)
    for spine in ax.spines.values():
        spine.set_color(base.GRID)


def render_score_comparison(comparisons: dict[str, list[dict]], out_base: Path) -> None:
    pass_rows = comparisons["pass_comparison"]
    model_rows = comparisons["model_comparison"]
    model_pass_rows = comparisons["model_pass_comparison"]

    fig = plt.figure(figsize=(22, 16), facecolor=base.PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[0.95, 1.1])
    fig.suptitle(
        f"{SCOPE_TITLE} v2 vs v3 vs v4: Mean Score and Model-Level Movement",
        color=base.TEXT,
        fontsize=22,
        fontweight="bold",
    )

    ax1 = fig.add_subplot(gs[0, 0])
    scopes = [r["scope"] for r in pass_rows]
    labels = [r["scope_label"] for r in pass_rows]
    x = list(range(len(scopes)))
    width = 0.24
    offsets = {"v2": -width, "v3": 0, "v4": width}
    for run in RUN_LABELS:
        values = [r[f"{run}_mean_score"] for r in pass_rows]
        ax1.bar([i + offsets[run] for i in x], values, width=width, color=RUN_COLORS[run], label=run, edgecolor=base.PANEL_BG)
    for i, row in enumerate(pass_rows):
        y = [row[f"{run}_mean_score"] for run in RUN_LABELS]
        ax1.plot([i + offsets[run] for run in RUN_LABELS], y, color=base.BLUE_PALE, linewidth=1.2, alpha=0.75)
        ax1.text(i, max(y) + 0.02, f"v4-v2 {row['delta_v4_v2_mean_score']:+.3f}", color=base.BLUE_PALE, ha="center", fontsize=8, fontweight="bold")
    ax1.set_xticks(x, labels)
    ax1.set_ylim(0.35, 0.95)
    ax1.set_ylabel("Mean score")
    ax1.set_title("Mean Score by Pass and Total", fontweight="bold")
    ax1.legend(frameon=False, labelcolor=base.TEXT, loc="upper right")
    ax1.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax1)

    ax2 = fig.add_subplot(gs[0, 1])
    ordered = sorted(model_rows, key=lambda r: r["delta_v4_v2_mean_score"])
    y = list(range(len(ordered)))
    deltas = [r["delta_v4_v2_mean_score"] for r in ordered]
    colors = [base.BLUE_PALE if v >= 0 else base.BLUE_DARK for v in deltas]
    ax2.barh(y, deltas, color=colors, edgecolor=base.PANEL_BG)
    ax2.axvline(0, color=base.BLUE_LIGHT, linewidth=1.2)
    ax2.set_yticks(y, [base.wrap_display_name(r["display_model"]) for r in ordered])
    ax2.set_xlabel("v4 - v2 mean score")
    ax2.set_title("Model-by-Model Net Improvement", fontweight="bold")
    for idx, row in enumerate(ordered):
        ax2.text(
            row["delta_v4_v2_mean_score"] + (0.004 if row["delta_v4_v2_mean_score"] >= 0 else -0.004),
            idx,
            f"{row['delta_v4_v2_mean_score']:+.3f}",
            color=base.TEXT,
            va="center",
            ha="left" if row["delta_v4_v2_mean_score"] >= 0 else "right",
            fontsize=8,
        )
    ax2.grid(axis="x", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax2)

    ax3 = fig.add_subplot(gs[1, :])
    order_models = [r["model"] for r in sorted(model_rows, key=lambda r: (-r["v4_mean_score"], r["display_model"]))]
    labels = [base.wrap_display_name(base.canonical_model_name(m)) for m in order_models]
    scopes = [*PASSES, "total"]
    matrix = []
    mp_index = index_rows(model_pass_rows, ("model", "scope"))
    model_index = {r["model"]: r for r in model_rows}
    for model in order_models:
        row = []
        for scope in scopes:
            source = model_index[model] if scope == "total" else mp_index[(model, scope)]
            row.append(source["delta_v4_v2_mean_score"])
        matrix.append(row)
    cmap = LinearSegmentedColormap.from_list("delta_blues", [base.BLUE_DARK, base.BLUE, base.BLUE_LIGHT, base.BLUE_PALE])
    max_abs = max(abs(v) for row in matrix for v in row) or 0.01
    im = ax3.imshow(matrix, aspect="auto", cmap=cmap, vmin=-max_abs, vmax=max_abs)
    ax3.set_yticks(range(len(order_models)), labels)
    ax3.set_xticks(range(len(scopes)), [PASS_LABELS[p] for p in scopes])
    ax3.set_title("v4 - v2 Mean Score Delta Heatmap by Model and Pass", fontweight="bold")
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            ax3.text(j, i, f"{val:+.2f}", ha="center", va="center", color=base.PAGE_BG if val > 0.045 else base.TEXT, fontsize=8)
    cbar = fig.colorbar(im, ax=ax3, fraction=0.018, pad=0.015)
    cbar.ax.tick_params(labelsize=8, colors=base.TEXT)
    cbar.set_label("v4 - v2", color=base.TEXT)
    style_axis(ax3)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def render_quality_failure_comparison(comparisons: dict[str, list[dict]], out_base: Path) -> None:
    pass_rows = comparisons["pass_comparison"]
    model_rows = comparisons["model_comparison"]
    family_rows = [r for r in comparisons["failure_family_comparison"] if r["scope"] == "total"]
    mode_rows = comparisons["failure_mode_comparison"]

    fig = plt.figure(figsize=(22, 16), facecolor=base.PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(2, 2)
    fig.suptitle(
        f"{SCOPE_TITLE} v2 vs v3 vs v4: Row, Numeric, Sort, and Failure Group Changes",
        color=base.TEXT,
        fontsize=22,
        fontweight="bold",
    )

    ax1 = fig.add_subplot(gs[0, 0])
    scopes = [r["scope"] for r in pass_rows]
    x_base = list(range(len(scopes)))
    offsets = [-0.24, 0.0, 0.24]
    colors = [base.BLUE_PALE, base.BLUE_LIGHT, base.BLUE_MID]
    for (metric, label), offset, color in zip(QUALITY_COMPONENTS, offsets, colors):
        vals = [r[f"delta_v4_v2_{metric}"] for r in pass_rows]
        xs = [x + offset for x in x_base]
        ax1.bar(xs, vals, width=0.22, color=color, label=label, edgecolor=base.PANEL_BG)
    ax1.axhline(0, color=base.BLUE_LIGHT, linewidth=1.0)
    ax1.set_xticks(x_base, [PASS_LABELS[s] for s in scopes])
    ax1.set_ylabel("v4 - v2")
    ax1.set_title("Quality Component Net Deltas by Pass and Total", fontweight="bold")
    ax1.legend(frameon=False, labelcolor=base.TEXT, loc="upper right")
    ax1.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax1)

    ax2 = fig.add_subplot(gs[0, 1])
    ordered = sorted(model_rows, key=lambda r: (-r["v4_mean_score"], r["display_model"]))
    matrix = [
        [row["delta_v4_v2_mean_row_set_correctness"], row["delta_v4_v2_mean_numeric_correctness"], row["delta_v4_v2_mean_sort_correctness"]]
        for row in ordered
    ]
    max_abs = max(abs(v) for row in matrix for v in row) or 0.01
    cmap = LinearSegmentedColormap.from_list("component_delta_blues", [base.BLUE_DARK, base.BLUE, base.BLUE_LIGHT, base.BLUE_PALE])
    im = ax2.imshow(matrix, aspect="auto", cmap=cmap, vmin=-max_abs, vmax=max_abs)
    ax2.set_yticks(range(len(ordered)), [base.wrap_display_name(r["display_model"]) for r in ordered])
    ax2.set_xticks(range(3), ["Row", "Numeric", "Sort"])
    ax2.set_title("Model-Level Component Net Deltas", fontweight="bold")
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            ax2.text(j, i, f"{val:+.2f}", ha="center", va="center", color=base.PAGE_BG if val > 0.045 else base.TEXT, fontsize=8)
    cbar = fig.colorbar(im, ax=ax2, fraction=0.03, pad=0.02)
    cbar.ax.tick_params(labelsize=8, colors=base.TEXT)
    cbar.set_label("v4 - v2", color=base.TEXT)
    style_axis(ax2)

    ax3 = fig.add_subplot(gs[1, 0])
    plotted_modes = [
        ("exact", "Exact"),
        ("same_count_wrong_values", "Same count, wrong values"),
        ("row_count_mismatch", "Wrong row count"),
        ("order_only", "Order only"),
        ("column_error", "Column/invalid"),
    ]
    x = list(range(len(plotted_modes)))
    width = 0.24
    total_rows = [r for r in mode_rows if r["scope"] == "total"]
    mode_lookup = {r["failure_mode"]: r for r in total_rows}
    for run in RUN_LABELS:
        vals = []
        for mode, _label in plotted_modes:
            if mode == "column_error":
                vals.append(mode_lookup["column_error"][f"{run}_count"] + mode_lookup["invalid_json_or_error"][f"{run}_count"])
            else:
                vals.append(mode_lookup[mode][f"{run}_count"])
        ax3.bar([i + offsets[RUN_LABELS.index(run)] for i in x], vals, width=width, color=RUN_COLORS[run], label=run, edgecolor=base.PANEL_BG)
    ax3.set_xticks(x, [label for _mode, label in plotted_modes], rotation=20, ha="right")
    ax3.set_ylabel("Attempts")
    ax3.set_title("Total Failure Mode Counts by Run", fontweight="bold")
    ax3.legend(frameon=False, labelcolor=base.TEXT, fontsize=8, loc="upper left")
    ax3.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax3)

    ax4 = fig.add_subplot(gs[1, 1])
    family_plot = sorted(family_rows, key=lambda r: r["delta_v4_v2_mean_score"])
    y = list(range(len(family_plot)))
    vals = [r["delta_v4_v2_mean_score"] for r in family_plot]
    colors = [base.BLUE_PALE if v >= 0 else base.BLUE_DARK for v in vals]
    ax4.barh(y, vals, color=colors, edgecolor=base.PANEL_BG)
    ax4.axvline(0, color=base.BLUE_LIGHT, linewidth=1.0)
    ax4.set_yticks(y, [r["failure_family"].replace("_", "\n") for r in family_plot])
    ax4.set_xlabel("v4 - v2 mean score")
    ax4.set_title("Failure Family Mean Score Net Changes", fontweight="bold")
    ax4.grid(axis="x", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax4)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def render_speed_score_comparison(comparisons: dict[str, list[dict]], out_base: Path) -> None:
    model_rows = comparisons["model_comparison"]

    fig = plt.figure(figsize=(22, 10), facecolor=base.PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(1, 2)
    fig.suptitle(
        f"{SCOPE_TITLE} v2 vs v3 vs v4: Mean Score Against Runtime and Generation Speed",
        color=base.TEXT,
        fontsize=21,
        fontweight="bold",
    )

    ax1 = fig.add_subplot(gs[0, 0])
    for row in model_rows:
        xs = [row[f"{run}_total_wall_s"] / 3600.0 for run in RUN_LABELS]
        ys = [row[f"{run}_mean_score"] for run in RUN_LABELS]
        ax1.plot(xs, ys, color=base.BLUE, linewidth=0.8, alpha=0.35)
        for run, x, y in zip(RUN_LABELS, xs, ys):
            ax1.scatter(x, y, s=90, marker=RUN_MARKERS[run], color=RUN_COLORS[run], edgecolors=base.BLUE_LIGHT, linewidth=0.8, alpha=0.95)
        ax1.text(xs[-1] + 0.02, ys[-1], row["display_model"], color=base.TEXT, fontsize=7, va="center")
    ax1.set_xlabel(f"Total wall time {RUNTIME_SCOPE_LABEL} (hours)")
    ax1.set_ylabel("Mean score")
    ax1.set_title("Mean Score vs Total Runtime per Model", fontweight="bold")
    ax1.grid(color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax1)

    ax2 = fig.add_subplot(gs[0, 1])
    for row in model_rows:
        xs = [row[f"{run}_avg_gen_tps"] for run in RUN_LABELS]
        ys = [row[f"{run}_mean_score"] for run in RUN_LABELS]
        ax2.plot(xs, ys, color=base.BLUE, linewidth=0.8, alpha=0.35)
        for run, x, y in zip(RUN_LABELS, xs, ys):
            ax2.scatter(x, y, s=90, marker=RUN_MARKERS[run], color=RUN_COLORS[run], edgecolors=base.BLUE_LIGHT, linewidth=0.8, alpha=0.95)
        ax2.text(xs[-1] + 0.10, ys[-1], row["display_model"], color=base.TEXT, fontsize=7, va="center")
    ax2.set_xlabel("Average generation speed (server_gen_tps)")
    ax2.set_ylabel("Mean score")
    ax2.set_title("Mean Score vs Average Generation Speed", fontweight="bold")
    ax2.grid(color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax2)

    for ax in (ax1, ax2):
        for run in RUN_LABELS:
            ax.scatter([], [], marker=RUN_MARKERS[run], color=RUN_COLORS[run], edgecolors=base.BLUE_LIGHT, label=run)
        ax.legend(frameon=False, labelcolor=base.TEXT, loc="lower right")

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def render_cpu_gpu_time_scatter(comparisons: dict[str, list[dict]], out_base: Path) -> None:
    model_rows = comparisons["model_comparison"]

    fig = plt.figure(figsize=(18, 11), facecolor=base.PAGE_BG, constrained_layout=True)
    ax = fig.add_subplot(1, 1, 1)
    fig.suptitle(
        f"{SCOPE_TITLE} v2 vs v3 vs v4: CPU/GPU Ratio vs Average Query Time",
        color=base.TEXT,
        fontsize=21,
        fontweight="bold",
    )

    for row in model_rows:
        xs = [row[f"{run}_avg_cpu_gpu_ratio"] for run in RUN_LABELS]
        ys = [row[f"{run}_avg_query_wall_s"] for run in RUN_LABELS]
        if all(x > 0 for x in xs):
            ax.plot(xs, ys, color=base.BLUE, linewidth=0.9, alpha=0.35)
        for run, x, y in zip(RUN_LABELS, xs, ys):
            ax.scatter(x, y, s=120, marker=RUN_MARKERS[run], color=RUN_COLORS[run], edgecolors=base.BLUE_LIGHT, linewidth=0.9, alpha=0.95)
        ax.text(xs[-1] * 1.04 if xs[-1] > 0 else 0.05, ys[-1], row["display_model"], color=base.TEXT, fontsize=8, va="center")

    ax.set_xscale("log")
    ax.set_xlabel("Average CPU/GPU utilization ratio (log scale)")
    ax.set_ylabel("Average query wall time (seconds)")
    ax.set_title("CPU uses ollama CPU with system CPU fallback; GPU uses core utilization with memory-utilization fallback", fontweight="bold")
    ax.grid(color=base.GRID, linewidth=0.8, alpha=0.75, which="both")
    style_axis(ax)
    for run in RUN_LABELS:
        ax.scatter([], [], marker=RUN_MARKERS[run], color=RUN_COLORS[run], edgecolors=base.BLUE_LIGHT, label=run)
    ax.legend(frameon=False, labelcolor=base.TEXT, loc="upper left")

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def render_query_delta_comparison(comparisons: dict[str, list[dict]], out_base: Path) -> None:
    query_rows = comparisons["query_comparison"]
    fig = plt.figure(figsize=(22, 13), facecolor=base.PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.1, 0.9])

    ax1 = fig.add_subplot(gs[0, 0])
    x = list(range(len(query_rows)))
    for run in RUN_LABELS:
        vals = [r[f"{run}_mean_score"] for r in query_rows]
        ax1.plot(x, vals, marker=RUN_MARKERS[run], color=RUN_COLORS[run], linewidth=2.0, markersize=5, label=run)
    ax1.set_xticks(x, [r["query"] for r in query_rows], rotation=70, ha="right")
    ax1.set_ylabel("Mean score")
    ax1.set_title(f"Query-Level Mean Score Trajectory Across {SCOPE_TITLE}", color=base.TEXT, fontsize=18, fontweight="bold")
    ax1.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    ax1.legend(frameon=False, labelcolor=base.TEXT, loc="lower left")
    style_axis(ax1)

    ax2 = fig.add_subplot(gs[1, 0])
    vals = [r["delta_v4_v2_mean_score"] for r in query_rows]
    colors = [base.BLUE_PALE if v >= 0 else base.BLUE_DARK for v in vals]
    ax2.bar(x, vals, color=colors, edgecolor=base.PANEL_BG)
    ax2.axhline(0, color=base.BLUE_LIGHT, linewidth=1.0)
    ax2.set_xticks(x, [r["query"] for r in query_rows], rotation=70, ha="right")
    ax2.set_ylabel("v4 - v2 mean score")
    ax2.set_title("Query-Level Net Delta", color=base.TEXT, fontsize=16, fontweight="bold")
    ax2.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax2)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def write_report(path: Path, comparisons: dict[str, list[dict]], dirs_by_run: dict[str, Path]) -> None:
    pass_rows = comparisons["pass_comparison"]
    model_rows = comparisons["model_comparison"]
    query_rows = comparisons["query_comparison"]
    family_total = [r for r in comparisons["failure_family_comparison"] if r["scope"] == "total"]
    trajectory_rows = comparisons["trajectory_summary"]

    total = next(r for r in pass_rows if r["scope"] == "total")
    top_v4_v2 = sorted(model_rows, key=lambda r: -r["delta_v4_v2_mean_score"])[:6]
    bottom_v4_v2 = sorted(model_rows, key=lambda r: r["delta_v4_v2_mean_score"])[:6]
    top_v4_v3 = sorted(model_rows, key=lambda r: -r["delta_v4_v3_mean_score"])[:6]
    family_improvers = sorted(family_total, key=lambda r: -r["delta_v4_v2_mean_score"])[:5]
    family_decliners = sorted(family_total, key=lambda r: r["delta_v4_v2_mean_score"])[:5]
    query_improvers = sorted(query_rows, key=lambda r: -r["delta_v4_v2_mean_score"])[:8]
    query_decliners = sorted(query_rows, key=lambda r: r["delta_v4_v2_mean_score"])[:8]

    lines = [
        f"# {SCOPE_TITLE} v2 vs v3 vs v4 Comparison",
        "",
        f"v2 source: `{dirs_by_run['v2'].name}`",
        f"v3 source: `{dirs_by_run['v3'].name}`",
        f"v4 source: `{dirs_by_run['v4'].name}`",
        "",
        f"Scope: {SCOPE_DESCRIPTION}",
        "",
        "## Headline",
        "",
        f"- Total mean score moved v2 {total['v2_mean_score']:.3f} -> v3 {total['v3_mean_score']:.3f} -> v4 {total['v4_mean_score']:.3f}.",
        f"- Net v4-v2 mean score change: {total['delta_v4_v2_mean_score']:+.3f}; v4-v3 change: {total['delta_v4_v3_mean_score']:+.3f}.",
        f"- Exact attempts moved v2 {int(total['v2_exact_attempts'])}/{int(total['v2_attempts'])} -> v3 {int(total['v3_exact_attempts'])}/{int(total['v3_attempts'])} -> v4 {int(total['v4_exact_attempts'])}/{int(total['v4_attempts'])}.",
        f"- Net component deltas v4-v2: row {total['delta_v4_v2_mean_row_set_correctness']:+.3f}, numeric {total['delta_v4_v2_mean_numeric_correctness']:+.3f}, sort {total['delta_v4_v2_mean_sort_correctness']:+.3f}.",
        f"- Dominant non-exact failure mode moved v2 `{total['v2_dominant_non_exact_failure_mode']}` -> v3 `{total['v3_dominant_non_exact_failure_mode']}` -> v4 `{total['v4_dominant_non_exact_failure_mode']}`.",
        f"- Total wall time moved v2 {total['v2_total_wall_s'] / 3600:.2f}h -> v3 {total['v3_total_wall_s'] / 3600:.2f}h -> v4 {total['v4_total_wall_s'] / 3600:.2f}h.",
        "",
        "## Pass Comparison",
        "",
        "| Scope | v2 Mean | v3 Mean | v4 Mean | v3-v2 | v4-v3 | v4-v2 | v2 Exact | v3 Exact | v4 Exact |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in pass_rows:
        lines.append(
            f"| {row['scope_label']} | {row['v2_mean_score']:.3f} | {row['v3_mean_score']:.3f} | {row['v4_mean_score']:.3f} | "
            f"{row['delta_v3_v2_mean_score']:+.3f} | {row['delta_v4_v3_mean_score']:+.3f} | {row['delta_v4_v2_mean_score']:+.3f} | "
            f"{int(row['v2_exact_attempts'])} | {int(row['v3_exact_attempts'])} | {int(row['v4_exact_attempts'])} |"
        )

    lines.extend(
        [
            "",
            "## Model Trajectory",
            "",
            "| Model | v2 Mean | v3 Mean | v4 Mean | v4-v2 | v4-v3 | v2 Exact | v3 Exact | v4 Exact | Trajectory |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in sorted(model_rows, key=lambda r: -r["delta_v4_v2_mean_score"]):
        lines.append(
            f"| {row['display_model']} | {row['v2_mean_score']:.3f} | {row['v3_mean_score']:.3f} | {row['v4_mean_score']:.3f} | "
            f"{row['delta_v4_v2_mean_score']:+.3f} | {row['delta_v4_v3_mean_score']:+.3f} | "
            f"{int(row['v2_exact_attempts'])} | {int(row['v3_exact_attempts'])} | {int(row['v4_exact_attempts'])} | {row['trajectory']} |"
        )

    lines.extend(["", "## Largest Net Model Gains v4-v2", ""])
    for row in top_v4_v2:
        lines.append(f"- {row['display_model']}: {row['delta_v4_v2_mean_score']:+.3f} mean score.")
    lines.extend(["", "## Smallest Net Model Gains v4-v2", ""])
    for row in bottom_v4_v2:
        lines.append(f"- {row['display_model']}: {row['delta_v4_v2_mean_score']:+.3f} mean score.")
    lines.extend(["", "## Largest v4-v3 Model Gains", ""])
    for row in top_v4_v3:
        lines.append(f"- {row['display_model']}: {row['delta_v4_v3_mean_score']:+.3f} mean score.")

    lines.extend(["", "## Query Movement", ""])
    lines.append("**Largest query gains v4-v2:**")
    for row in query_improvers:
        lines.append(f"- {row['query']} `{row['case_id']}`: {row['delta_v4_v2_mean_score']:+.3f} mean score.")
    lines.extend(["", "**Largest query losses v4-v2:**"])
    for row in query_decliners:
        lines.append(f"- {row['query']} `{row['case_id']}`: {row['delta_v4_v2_mean_score']:+.3f} mean score.")

    lines.extend(["", "## Failure Family Changes", "", "**Largest positive v4-v2 family deltas:**"])
    for row in family_improvers:
        lines.append(f"- {row['failure_family']}: {row['delta_v4_v2_mean_score']:+.3f} mean score.")
    lines.extend(["", "**Smallest positive v4-v2 family deltas:**"])
    for row in family_decliners:
        lines.append(f"- {row['failure_family']}: {row['delta_v4_v2_mean_score']:+.3f} mean score.")

    lines.extend(["", "## Trajectory Counts", "", "| Scope | Trajectory | Count |", "|---|---|---:|"])
    for row in trajectory_rows:
        lines.append(f"| {row['scope']} | {row['trajectory']} | {row['count']} |")

    lines.extend(
        [
            "",
            "## Interpretation Notes",
            "",
            "- v2 is the short-standard baseline, v3 changes standard instructions, and v4 keeps the shorter standards while adding task-specific guardrails.",
            "- The v4-v2 delta is the best net prompt-engineering view; v4-v3 separates whether the v4 task-specific approach improved or reversed the v3 standard-instruction effect.",
            "- Runtime and generation-speed panels provide execution context only; they are not treated as correctness metrics.",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_comparison(v2_dir: Path, v3_dir: Path, v4_dir: Path, out_dir: Path, output_prefix: str = DEFAULT_OUTPUT_PREFIX) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir.mkdir(parents=True, exist_ok=True)

    case_meta = load_case_meta(repo_root)
    dirs_by_run = {"v2": v2_dir, "v3": v3_dir, "v4": v4_dir}
    rows_by_run = {run: load_rows(path, run, case_meta) for run, path in dirs_by_run.items()}
    comparisons = build_comparisons(rows_by_run, case_meta)

    for name, rows in comparisons.items():
        write_csv(out_dir / f"{output_prefix}_{name}.csv", rows)

    render_score_comparison(comparisons, out_dir / f"{output_prefix}_score_comparison")
    render_quality_failure_comparison(comparisons, out_dir / f"{output_prefix}_quality_failure_comparison")
    render_speed_score_comparison(comparisons, out_dir / f"{output_prefix}_speed_score_comparison")
    render_cpu_gpu_time_scatter(comparisons, out_dir / f"{output_prefix}_cpu_gpu_time_scatter")
    render_query_delta_comparison(comparisons, out_dir / f"{output_prefix}_query_delta_comparison")
    write_report(out_dir / f"{output_prefix}_comparison_report.md", comparisons, dirs_by_run)

    return out_dir


def main() -> int:
    if len(sys.argv) not in {4, 5}:
        print("usage: pass123_v2_v3_v4_comparison.py <v2_results_dir> <v3_results_dir> <v4_results_dir> [out_dir]", file=sys.stderr)
        return 2
    v2_dir = Path(sys.argv[1]).resolve()
    v3_dir = Path(sys.argv[2]).resolve()
    v4_dir = Path(sys.argv[3]).resolve()
    out_dir = Path(sys.argv[4]).resolve() if len(sys.argv) == 5 else v4_dir / "pass123_v2_v3_v4_comparison_analysis"
    run_comparison(v2_dir, v3_dir, v4_dir, out_dir, DEFAULT_OUTPUT_PREFIX)

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
