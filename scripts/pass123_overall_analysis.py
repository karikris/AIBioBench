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


PASS_LABELS = {
    "1": "Pass 1\nEasy SQL",
    "2": "Pass 2\nMedium SQL",
    "3": "Pass 3\nHard SQL",
}

PASS_SHORT = {
    "1": "Pass 1",
    "2": "Pass 2",
    "3": "Pass 3",
}

GROUP_COLORS = {
    "Dominant cross-pass leader": base.BLUE_PALE,
    "Strong but difficulty-sensitive exact converters": base.BLUE_LIGHT,
    "Near-miss or niche hard-query operators": base.BLUE_MID,
    "Brittle / low-exactness operators": base.BLUE_DARK,
}


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
            if row["pass"] in {1, 2, 3}:
                out[row["case_id"]] = row
    return out


def load_rows(results_dir: Path) -> list[dict]:
    rows = []
    with (results_dir / "detailed_results.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["pass"] not in {"1", "2", "3"}:
                continue
            row["_failure_mode"] = base.classify_failure(row)
            rows.append(row)
    return rows


def read_pass_failure_points(results_dir: Path) -> list[dict]:
    out = []
    for pass_no in ("1", "2", "3"):
        path = results_dir / f"pass{pass_no}_analysis" / f"pass{pass_no}_query_failure_points.csv"
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["pass"] = pass_no
                out.append(row)
    out.sort(key=lambda r: (*case_sort_key(r["case_id"]), -int(r["attempts_with_issue"])))
    return out


def build_summaries(rows: list[dict], case_meta: dict):
    by_pass = defaultdict(list)
    by_model = defaultdict(list)
    by_case = defaultdict(list)
    by_model_pass = defaultdict(list)
    by_model_case = defaultdict(list)
    for row in rows:
        by_pass[row["pass"]].append(row)
        by_model[row["model"]].append(row)
        by_case[row["case_id"]].append(row)
        by_model_pass[(row["model"], row["pass"])].append(row)
        by_model_case[(row["model"], row["case_id"])].append(row)

    pass_summary = []
    for pass_no in ("1", "2", "3"):
        items = by_pass[pass_no]
        case_ids = sorted({r["case_id"] for r in items}, key=case_sort_key)
        modes = Counter(r["_failure_mode"] for r in items)
        pass_summary.append(
            {
                "pass": pass_no,
                "pass_label": PASS_SHORT[pass_no],
                "attempts": len(items),
                "exact_attempts": sum(base.as_bool(r["exact_match"]) for r in items),
                "exact_attempt_rate": mean(base.as_bool(r["exact_match"]) for r in items),
                "queries_with_any_exact": sum(any(base.as_bool(r["exact_match"]) for r in by_case[c]) for c in case_ids),
                "exact_zero_queries": sum(not any(base.as_bool(r["exact_match"]) for r in by_case[c]) for c in case_ids),
                "mean_score": mean(base.as_float(r["score"]) for r in items),
                "mean_aligned_cell_accuracy": mean(base.as_float(r["aligned_cell_accuracy"]) for r in items),
                "mean_row_set_correctness": mean(base.as_float(r["row_set_correctness_score"]) for r in items),
                "mean_numeric_correctness": mean(base.as_float(r["numeric_correctness_score"]) for r in items),
                "dominant_failure_mode": modes.most_common(1)[0][0],
                "row_count_mismatch": modes["row_count_mismatch"],
                "same_count_wrong_values": modes["same_count_wrong_values"],
                "exact": modes["exact"],
                "order_only": modes["order_only"],
                "type_only": modes["type_only"],
                "column_error": modes["column_error"],
            }
        )

    model_summary = []
    for model, items in by_model.items():
        pass_exact = {}
        pass_score = {}
        pass_cell = {}
        for pass_no in ("1", "2", "3"):
            pass_items = by_model_pass[(model, pass_no)]
            pass_exact[pass_no] = sum(base.as_bool(r["exact_match"]) for r in pass_items)
            pass_score[pass_no] = mean(base.as_float(r["score"]) for r in pass_items)
            pass_cell[pass_no] = mean(base.as_float(r["aligned_cell_accuracy"]) for r in pass_items)
        modes = Counter(r["_failure_mode"] for r in items)
        exact_total = sum(pass_exact.values())
        model_summary.append(
            {
                "model": model,
                "display_model": base.canonical_model_name(model),
                "attempts": len(items),
                "exact_attempts": exact_total,
                "exact_attempt_rate": exact_total / len(items),
                "queries_with_any_exact": sum(any(base.as_bool(r["exact_match"]) for r in by_model_case[(model, c)]) for c in by_case),
                "stable_exact_queries": sum(sum(base.as_bool(r["exact_match"]) for r in by_model_case[(model, c)]) == 3 for c in by_case),
                "pass1_exact": pass_exact["1"],
                "pass2_exact": pass_exact["2"],
                "pass3_exact": pass_exact["3"],
                "pass1_mean_score": pass_score["1"],
                "pass2_mean_score": pass_score["2"],
                "pass3_mean_score": pass_score["3"],
                "mean_score": mean(base.as_float(r["score"]) for r in items),
                "mean_aligned_cell_accuracy": mean(base.as_float(r["aligned_cell_accuracy"]) for r in items),
                "mean_row_set_correctness": mean(base.as_float(r["row_set_correctness_score"]) for r in items),
                "mean_numeric_correctness": mean(base.as_float(r["numeric_correctness_score"]) for r in items),
                "score_drop_pass1_to_pass3": pass_score["1"] - pass_score["3"],
                "exact_drop_pass1_to_pass3": pass_exact["1"] - pass_exact["3"],
                "dominant_failure_mode": modes.most_common(1)[0][0],
                "row_count_mismatch": modes["row_count_mismatch"],
                "same_count_wrong_values": modes["same_count_wrong_values"],
                "exact": modes["exact"],
                "order_only": modes["order_only"],
                "type_only": modes["type_only"],
                "column_error": modes["column_error"],
            }
        )
    model_summary.sort(key=lambda r: (-r["exact_attempts"], -r["mean_score"], r["display_model"]))

    query_summary = []
    for case_id in sorted(by_case, key=case_sort_key):
        items = by_case[case_id]
        modes = Counter(r["_failure_mode"] for r in items)
        meta = case_meta[case_id]
        query_summary.append(
            {
                "case_id": case_id,
                "query": query_label(case_id),
                "pass": str(meta["pass"]),
                "query_no": meta["query"],
                "difficulty": meta["difficulty"],
                "language": meta["language"],
                "primary_failure_family": meta["metadata"]["failure_family_primary"],
                "attempts": len(items),
                "exact_attempts": sum(base.as_bool(r["exact_match"]) for r in items),
                "exact_attempt_rate": mean(base.as_bool(r["exact_match"]) for r in items),
                "mean_score": mean(base.as_float(r["score"]) for r in items),
                "mean_aligned_cell_accuracy": mean(base.as_float(r["aligned_cell_accuracy"]) for r in items),
                "mean_row_set_correctness": mean(base.as_float(r["row_set_correctness_score"]) for r in items),
                "dominant_failure_mode": modes.most_common(1)[0][0],
                "row_count_mismatch": modes["row_count_mismatch"],
                "same_count_wrong_values": modes["same_count_wrong_values"],
                "exact": modes["exact"],
                "order_only": modes["order_only"],
                "type_only": modes["type_only"],
                "column_error": modes["column_error"],
            }
        )

    model_pass_rows = []
    for model_row in model_summary:
        model = model_row["model"]
        for pass_no in ("1", "2", "3"):
            items = by_model_pass[(model, pass_no)]
            modes = Counter(r["_failure_mode"] for r in items)
            model_pass_rows.append(
                {
                    "model": model,
                    "display_model": model_row["display_model"],
                    "pass": pass_no,
                    "exact_attempts": sum(base.as_bool(r["exact_match"]) for r in items),
                    "mean_score": mean(base.as_float(r["score"]) for r in items),
                    "mean_aligned_cell_accuracy": mean(base.as_float(r["aligned_cell_accuracy"]) for r in items),
                    "mean_row_set_correctness": mean(base.as_float(r["row_set_correctness_score"]) for r in items),
                    "dominant_failure_mode": modes.most_common(1)[0][0],
                    "row_count_mismatch": modes["row_count_mismatch"],
                    "same_count_wrong_values": modes["same_count_wrong_values"],
                    "exact": modes["exact"],
                }
            )

    return pass_summary, model_summary, query_summary, model_pass_rows


def group_models(model_summary: list[dict]) -> list[dict]:
    out = []
    for row in model_summary:
        if row["exact_attempts"] >= 30:
            group = "Dominant cross-pass leader"
            reason = "Only model with high exact conversion across all three SQL passes and the smallest pass-1 to pass-3 exactness decay."
        elif row["exact_attempts"] >= 9:
            group = "Strong but difficulty-sensitive exact converters"
            reason = "Converted easy/medium structural tasks, but exactness fell sharply as hard joins, audits, and ranking appeared."
        elif row["pass3_exact"] > 0 or row["mean_score"] >= 0.64:
            group = "Near-miss or niche hard-query operators"
            reason = "Often retained useful partial credit or a narrow hard-query skill, but exact conversion was sparse."
        else:
            group = "Brittle / low-exactness operators"
            reason = "Low or zero exact conversion with repeated row-set, join-chain, and aggregation-grain failures."
        out.append(
            {
                "model": row["model"],
                "display_model": row["display_model"],
                "group": group,
                "group_reason": reason,
                "exact_attempts": row["exact_attempts"],
                "queries_with_any_exact": row["queries_with_any_exact"],
                "stable_exact_queries": row["stable_exact_queries"],
                "pass1_exact": row["pass1_exact"],
                "pass2_exact": row["pass2_exact"],
                "pass3_exact": row["pass3_exact"],
                "mean_score": row["mean_score"],
                "score_drop_pass1_to_pass3": row["score_drop_pass1_to_pass3"],
                "dominant_failure_mode": row["dominant_failure_mode"],
            }
        )
    return out


def style_axis(ax):
    ax.set_facecolor(base.PANEL_BG)
    ax.tick_params(colors=base.TEXT)
    for spine in ax.spines.values():
        spine.set_color(base.GRID)
    ax.title.set_color(base.TEXT)
    ax.xaxis.label.set_color(base.TEXT)
    ax.yaxis.label.set_color(base.TEXT)


def render_overall_visual(pass_summary, model_summary, query_summary, model_pass_rows, rows, out_base: Path) -> None:
    models = [m["model"] for m in model_summary]
    model_labels = [base.wrap_display_name(m["display_model"]) for m in model_summary]
    passes = ["1", "2", "3"]
    pass_attempts = {p["pass"]: p["attempts"] for p in pass_summary}
    query_attempts = max(q["attempts"] for q in query_summary)
    mp = {(r["model"], r["pass"]): r for r in model_pass_rows}
    score_matrix = [[mp[(model, pass_no)]["mean_score"] for pass_no in passes] for model in models]

    fig = plt.figure(figsize=(21, 16), facecolor=base.PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.35, 1.0])
    fig.suptitle("AIBioBench Passes 1-3: SQL Capability Degradation Across 30 Queries", fontsize=23, fontweight="bold", color=base.TEXT)

    ax1 = fig.add_subplot(gs[0, 0])
    x = list(range(len(passes)))
    exacts = [p["exact_attempts"] for p in pass_summary]
    scores = [p["mean_score"] for p in pass_summary]
    ax1.bar(x, exacts, color=[base.BLUE_PALE, base.BLUE_LIGHT, base.BLUE_MID], edgecolor=base.PANEL_BG)
    ax1.set_xticks(x, [PASS_LABELS[p] for p in passes])
    ax1.set_ylabel(f"Exact attempts out of {max(pass_attempts.values())}")
    ax1.set_ylim(0, 65)
    ax1.set_title("Exact Conversion Drops with Difficulty", fontweight="bold")
    for idx, val in enumerate(exacts):
        ax1.text(idx, val + 1.2, f"{val}/{pass_summary[idx]['attempts']}", ha="center", color=base.TEXT, fontsize=11, fontweight="bold")
    ax1b = ax1.twinx()
    ax1b.plot(x, scores, color=base.BLUE, linewidth=3, marker="o", markersize=9)
    ax1b.set_ylim(0.45, 0.82)
    ax1b.set_ylabel("Mean score")
    ax1b.tick_params(colors=base.TEXT)
    ax1b.yaxis.label.set_color(base.TEXT)
    for spine in ax1b.spines.values():
        spine.set_color(base.GRID)
    ax1.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax1)

    ax2 = fig.add_subplot(gs[0, 1])
    y = list(range(len(model_summary)))
    left = [0] * len(model_summary)
    colors = {"pass1_exact": base.BLUE_PALE, "pass2_exact": base.BLUE_LIGHT, "pass3_exact": base.BLUE_MID}
    labels = {"pass1_exact": "Pass 1", "pass2_exact": "Pass 2", "pass3_exact": "Pass 3"}
    for key in ("pass1_exact", "pass2_exact", "pass3_exact"):
        vals = [m[key] for m in model_summary]
        ax2.barh(y, vals, left=left, color=colors[key], label=labels[key], edgecolor=base.PANEL_BG)
        left = [l + v for l, v in zip(left, vals)]
    ax2.set_yticks(y, model_labels)
    ax2.invert_yaxis()
    ax2.set_xlabel("Exact attempts across passes 1-3")
    ax2.set_title("Exact Attempts by Model and Pass", fontweight="bold")
    ax2.legend(frameon=False, loc="lower right", labelcolor=base.TEXT)
    ax2.grid(axis="x", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax2)

    ax3 = fig.add_subplot(gs[1, 0])
    cmap = LinearSegmentedColormap.from_list("pass123_scores", [base.BLUE_DARK, base.BLUE, base.BLUE_LIGHT, base.BLUE_PALE])
    im = ax3.imshow(score_matrix, aspect="auto", cmap=cmap, vmin=0.35, vmax=1.0)
    ax3.set_xticks(range(len(passes)), [PASS_SHORT[p] for p in passes])
    ax3.set_yticks(range(len(models)), model_labels)
    ax3.set_title("Mean Score Trajectory by Model", fontweight="bold")
    for i in range(len(models)):
        for j in range(len(passes)):
            val = score_matrix[i][j]
            ax3.text(j, i, f"{val:.2f}", ha="center", va="center", color=base.PAGE_BG if val > 0.72 else base.TEXT, fontsize=9)
    cbar = fig.colorbar(im, ax=ax3, fraction=0.025, pad=0.02)
    cbar.ax.tick_params(labelsize=8, colors=base.TEXT)
    style_axis(ax3)

    ax4 = fig.add_subplot(gs[1, 1])
    q_labels = [q["query"] for q in query_summary]
    q_exact = [q["exact_attempts"] for q in query_summary]
    q_colors = [base.BLUE_PALE if v >= 10 else base.BLUE_LIGHT if v > 0 else base.BLUE_DARK for v in q_exact]
    ax4.bar(range(len(query_summary)), q_exact, color=q_colors, edgecolor=base.PANEL_BG)
    ax4.set_xticks(range(len(query_summary)), q_labels, rotation=70, ha="right", fontsize=8)
    ax4.set_ylabel(f"Exact attempts out of {query_attempts}")
    ax4.set_ylim(0, 24)
    ax4.set_title("Query-Level Exact Conversion Across 30 SQL Tasks", fontweight="bold")
    ax4.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax4)

    ax5 = fig.add_subplot(gs[2, 0])
    modes = [
        ("exact", "Exact", base.BLUE_PALE),
        ("same_count_wrong_values", "Same count, wrong values", base.BLUE_LIGHT),
        ("row_count_mismatch", "Wrong row count", base.BLUE_MID),
        ("order_only", "Order only", base.BLUE),
        ("type_only", "Type only", base.FAIL_LIGHT),
        ("column_error", "Column error", "#365F86"),
    ]
    bottoms = [0] * len(passes)
    for mode, label, color in modes:
        vals = [sum(1 for r in rows if r["pass"] == pass_no and r["_failure_mode"] == mode) for pass_no in passes]
        ax5.bar(range(len(passes)), vals, bottom=bottoms, color=color, label=label, edgecolor=base.PANEL_BG)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax5.set_xticks(range(len(passes)), [PASS_SHORT[p] for p in passes])
    ax5.set_ylim(0, max(pass_attempts.values()))
    ax5.set_ylabel("Attempts")
    ax5.set_title("Failure Mode Mix by Pass", fontweight="bold")
    ax5.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, labelcolor=base.TEXT)
    ax5.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax5)

    ax6 = fig.add_subplot(gs[2, 1])
    row_scores = [p["mean_row_set_correctness"] for p in pass_summary]
    numeric_scores = [p["mean_numeric_correctness"] for p in pass_summary]
    cell_scores = [p["mean_aligned_cell_accuracy"] for p in pass_summary]
    ax6.plot(x, row_scores, color=base.BLUE_PALE, marker="o", linewidth=2.7, label="Row-set correctness")
    ax6.plot(x, numeric_scores, color=base.BLUE_LIGHT, marker="s", linewidth=2.7, label="Numeric correctness")
    ax6.plot(x, cell_scores, color=base.BLUE_MID, marker="^", linewidth=2.7, label="Aligned cell accuracy")
    ax6.set_xticks(x, [PASS_SHORT[p] for p in passes])
    ax6.set_ylim(0.35, 0.9)
    ax6.set_ylabel("Mean score component")
    ax6.set_title("What Degraded: Rows, Numbers, and Cells", fontweight="bold")
    ax6.legend(frameon=False, loc="lower left", labelcolor=base.TEXT)
    ax6.grid(axis="y", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax6)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def render_model_groups(model_groups, out_base: Path) -> None:
    fig = plt.figure(figsize=(18, 10), facecolor=base.PAGE_BG, constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.2, 1.0])
    fig.suptitle("Passes 1-3 Model Grouping by Exactness and Failure Pattern", fontsize=20, fontweight="bold", color=base.TEXT)

    ordered = sorted(model_groups, key=lambda r: (-r["exact_attempts"], -r["mean_score"], r["display_model"]))
    ax1 = fig.add_subplot(gs[0, 0])
    y = list(range(len(ordered)))
    colors = [GROUP_COLORS[r["group"]] for r in ordered]
    ax1.barh(y, [r["exact_attempts"] for r in ordered], color=colors, edgecolor=base.PANEL_BG)
    ax1.set_yticks(y, [base.wrap_display_name(r["display_model"]) for r in ordered])
    ax1.invert_yaxis()
    ax1.set_xlim(0, 38)
    ax1.set_xlabel("Exact attempts out of 90")
    ax1.set_title("Overall Exact Conversion", fontweight="bold")
    for idx, row in enumerate(ordered):
        ax1.text(row["exact_attempts"] + 0.5, idx, row["group"], va="center", color=base.TEXT, fontsize=9)
    ax1.grid(axis="x", color=base.GRID, linewidth=0.8, alpha=0.75)
    style_axis(ax1)

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis("off")
    ax2.set_facecolor(base.PANEL_BG)
    y_pos = 0.96
    for group, color in GROUP_COLORS.items():
        members = [r["display_model"] for r in ordered if r["group"] == group]
        if not members:
            continue
        reason = next(r["group_reason"] for r in ordered if r["group"] == group)
        ax2.text(0.02, y_pos, group, transform=ax2.transAxes, color=color, fontsize=14, fontweight="bold", va="top")
        y_pos -= 0.055
        ax2.text(0.04, y_pos, reason, transform=ax2.transAxes, color=base.TEXT, fontsize=10, va="top", wrap=True)
        y_pos -= 0.10
        ax2.text(0.04, y_pos, ", ".join(members), transform=ax2.transAxes, color=base.BLUE_PALE, fontsize=10, va="top", wrap=True)
        y_pos -= 0.13
    ax2.text(0.02, 0.08, "Grouping uses exact conversion first, then mean score and pass-3 survival.", transform=ax2.transAxes, color=base.BLUE_LIGHT, fontsize=10, va="bottom", wrap=True)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def top_failure_text(query_failures: list[dict], case_id: str, total_attempts: int) -> str:
    rows = [r for r in query_failures if r["case_id"] == case_id][:3]
    if not rows:
        return ""
    return "; ".join(f"{r['attempts_with_issue']}/{total_attempts}: {r['issue_label']}" for r in rows)


def write_notes(path: Path, results_dir: Path, pass_summary, model_summary, query_summary, query_failures, model_groups) -> None:
    total_exact = sum(p["exact_attempts"] for p in pass_summary)
    total_attempts = sum(p["attempts"] for p in pass_summary)
    zero_queries = sum(1 for q in query_summary if q["exact_attempts"] == 0)
    best_queries = sorted(query_summary, key=lambda r: (-r["exact_attempts"], -r["mean_score"]))[:5]
    hardest_queries = sorted(query_summary, key=lambda r: (r["exact_attempts"], r["mean_score"]))[:5]
    model_count = len(model_summary)
    queries_per_pass = {p["pass"]: p["queries_with_any_exact"] + p["exact_zero_queries"] for p in pass_summary}

    lines = [
        "# AIBioBench Passes 1-3 Overall Analysis",
        "",
        f"Run analyzed: `{results_dir.name}`",
        "",
        f"Scope: passes 1, 2, and 3 only. This covers 30 SQL queries, {model_count} models, and 3 repeated attempts per model-query pair.",
        "",
        "## Headline Findings",
        "",
        f"- Overall exact conversion was {total_exact}/{total_attempts} attempts ({100 * total_exact / total_attempts:.1f}%).",
        f"- Exact matches dropped monotonically by pass: {pass_summary[0]['exact_attempts']}/{pass_summary[0]['attempts']} in pass 1, {pass_summary[1]['exact_attempts']}/{pass_summary[1]['attempts']} in pass 2, and {pass_summary[2]['exact_attempts']}/{pass_summary[2]['attempts']} in pass 3.",
        f"- {zero_queries}/30 queries had zero exact attempts. Exact-zero queries increased from {pass_summary[0]['exact_zero_queries']}/{queries_per_pass[pass_summary[0]['pass']]} in pass 1 to {pass_summary[1]['exact_zero_queries']}/{queries_per_pass[pass_summary[1]['pass']]} in pass 2 and {pass_summary[2]['exact_zero_queries']}/{queries_per_pass[pass_summary[2]['pass']]} in pass 3.",
        f"- {model_summary[0]['display_model']} was the clear cross-pass leader with {model_summary[0]['exact_attempts']}/90 exact attempts and exact matches in all three passes.",
        "- The primary degradation was not invalid output. Models usually returned plausible tables but failed on row-set boundaries, join preservation, aggregation grain, or exact sort/type semantics.",
        "",
        "## Pass-Level Summary",
        "",
        "| Pass | Exact Attempts | Queries With Any Exact | Exact-Zero Queries | Mean Score | Mean Cell Accuracy | Dominant Failure Mode |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for p in pass_summary:
        lines.append(
            f"| {p['pass_label']} | {p['exact_attempts']}/{p['attempts']} | {p['queries_with_any_exact']}/10 | {p['exact_zero_queries']}/10 | {p['mean_score']:.3f} | {p['mean_aligned_cell_accuracy']:.3f} | {p['dominant_failure_mode']} |"
        )

    lines.extend(
        [
            "",
            "## Model Groups",
            "",
            "| Group | Models | Interpretation |",
            "|---|---|---|",
        ]
    )
    for group in GROUP_COLORS:
        members = [r["display_model"] for r in model_groups if r["group"] == group]
        if not members:
            continue
        reason = next(r["group_reason"] for r in model_groups if r["group"] == group)
        lines.append(f"| {group} | {', '.join(members)} | {reason} |")

    lines.extend(
        [
            "",
            "## Model Ranking",
            "",
            "| Model | Exact Attempts | Pass 1 | Pass 2 | Pass 3 | Mean Score | Score Drop P1 to P3 | Dominant Failure |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for m in model_summary:
        lines.append(
            f"| {m['display_model']} | {m['exact_attempts']}/90 | {m['pass1_exact']} | {m['pass2_exact']} | {m['pass3_exact']} | {m['mean_score']:.3f} | {m['score_drop_pass1_to_pass3']:.3f} | {m['dominant_failure_mode']} |"
        )

    lines.extend(
        [
            "",
            "## Query-Level Takeaways",
            "",
            "**Best exact-conversion queries:**",
            "",
        ]
    )
    for q in best_queries:
        lines.append(f"- {q['query']} `{q['case_id']}`: {q['exact_attempts']}/{q['attempts']} exact, mean score {q['mean_score']:.3f}, family `{q['primary_failure_family']}`.")

    lines.extend(["", "**Hardest exact-conversion queries:**", ""])
    for q in hardest_queries:
        lines.append(f"- {q['query']} `{q['case_id']}`: {q['exact_attempts']}/{q['attempts']} exact, mean score {q['mean_score']:.3f}, family `{q['primary_failure_family']}`.")

    lines.extend(
        [
            "",
            "## Query Failure Points",
            "",
            "| Query | Family | Exact | Mean Score | Top Failure Points |",
            "|---|---|---:|---:|---|",
        ]
    )
    for q in query_summary:
        lines.append(
            f"| {q['query']} | {q['primary_failure_family']} | {q['exact_attempts']}/{q['attempts']} | {q['mean_score']:.3f} | {top_failure_text(query_failures, q['case_id'], q['attempts'])} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Pass 1 mainly separated models on basic join preservation and simple aggregation grain. Even easy tasks exposed exact-match brittleness: half the queries had zero exact attempts.",
            "- Pass 2 raised the cost of snowflake traversal and preserving-table logic. Exactness concentrated in a few join-coverage tasks, while decision-support aggregates stayed exact-zero.",
            "- Pass 3 moved failures toward hard join-status classification, anti-join/orphan logic, dense ranking, and decision-priority aggregation. Some models preserved high partial scores, but exact conversion largely collapsed.",
            "- Across all three passes, row-count mismatch and same-count-wrong-values dominate. That means the benchmark is mostly measuring semantic boundary errors rather than JSON validity or execution-format failures.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: pass123_overall_analysis.py <results_dir>", file=sys.stderr)
        return 2
    results_dir = Path(sys.argv[1]).resolve()
    repo_root = Path(__file__).resolve().parents[1]
    if not (results_dir / "detailed_results.csv").exists():
        print(f"missing detailed_results.csv in {results_dir}", file=sys.stderr)
        return 1

    out_dir = results_dir / "pass123_overall_analysis"
    out_dir.mkdir(exist_ok=True)

    case_meta = load_case_meta(repo_root)
    rows = load_rows(results_dir)
    pass_summary, model_summary, query_summary, model_pass_rows = build_summaries(rows, case_meta)
    query_failures = read_pass_failure_points(results_dir)
    model_groups = group_models(model_summary)

    base.write_csv(
        out_dir / "pass123_pass_summary.csv",
        pass_summary,
        [
            "pass",
            "pass_label",
            "attempts",
            "exact_attempts",
            "exact_attempt_rate",
            "queries_with_any_exact",
            "exact_zero_queries",
            "mean_score",
            "mean_aligned_cell_accuracy",
            "mean_row_set_correctness",
            "mean_numeric_correctness",
            "dominant_failure_mode",
            "row_count_mismatch",
            "same_count_wrong_values",
            "exact",
            "order_only",
            "type_only",
            "column_error",
        ],
    )
    base.write_csv(
        out_dir / "pass123_model_summary.csv",
        model_summary,
        [
            "model",
            "display_model",
            "attempts",
            "exact_attempts",
            "exact_attempt_rate",
            "queries_with_any_exact",
            "stable_exact_queries",
            "pass1_exact",
            "pass2_exact",
            "pass3_exact",
            "pass1_mean_score",
            "pass2_mean_score",
            "pass3_mean_score",
            "mean_score",
            "mean_aligned_cell_accuracy",
            "mean_row_set_correctness",
            "mean_numeric_correctness",
            "score_drop_pass1_to_pass3",
            "exact_drop_pass1_to_pass3",
            "dominant_failure_mode",
            "row_count_mismatch",
            "same_count_wrong_values",
            "exact",
            "order_only",
            "type_only",
            "column_error",
        ],
    )
    base.write_csv(
        out_dir / "pass123_query_summary.csv",
        query_summary,
        [
            "case_id",
            "query",
            "pass",
            "query_no",
            "difficulty",
            "language",
            "primary_failure_family",
            "attempts",
            "exact_attempts",
            "exact_attempt_rate",
            "mean_score",
            "mean_aligned_cell_accuracy",
            "mean_row_set_correctness",
            "dominant_failure_mode",
            "row_count_mismatch",
            "same_count_wrong_values",
            "exact",
            "order_only",
            "type_only",
            "column_error",
        ],
    )
    base.write_csv(
        out_dir / "pass123_model_pass_matrix.csv",
        model_pass_rows,
        [
            "model",
            "display_model",
            "pass",
            "exact_attempts",
            "mean_score",
            "mean_aligned_cell_accuracy",
            "mean_row_set_correctness",
            "dominant_failure_mode",
            "row_count_mismatch",
            "same_count_wrong_values",
            "exact",
        ],
    )
    base.write_csv(
        out_dir / "pass123_model_groups.csv",
        model_groups,
        [
            "model",
            "display_model",
            "group",
            "group_reason",
            "exact_attempts",
            "queries_with_any_exact",
            "stable_exact_queries",
            "pass1_exact",
            "pass2_exact",
            "pass3_exact",
            "mean_score",
            "score_drop_pass1_to_pass3",
            "dominant_failure_mode",
        ],
    )
    base.write_csv(
        out_dir / "pass123_query_failure_points.csv",
        query_failures,
        ["pass", "case_id", "query", "short_name", "issue_code", "issue_label", "attempts_with_issue", "attempt_pct", "example_models"],
    )

    render_overall_visual(pass_summary, model_summary, query_summary, model_pass_rows, rows, out_dir / "pass123_overall_visual_report")
    render_model_groups(model_groups, out_dir / "pass123_model_groups")
    write_notes(out_dir / "pass123_overall_analysis_notes.md", results_dir, pass_summary, model_summary, query_summary, query_failures, model_groups)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
