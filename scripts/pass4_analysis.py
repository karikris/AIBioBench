#!/usr/bin/env python3
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

import pass3_analysis as base


QUERY_LABELS = {
    "pass4.query1": "Q1\nreconcile\nmetrics",
    "pass4.query2": "Q2\ncondition\npathway",
    "pass4.query3": "Q3\nbatch\nrole",
    "pass4.query4": "Q4\ncontrol\nshared",
    "pass4.query5": "Q5\ngene\nprofile",
    "pass4.query6": "Q6\nsample\nburden",
    "pass4.query7": "Q7\norphan-key\nreport",
    "pass4.query8": "Q8\npresentation\ntable",
}

QUERY_NOTES = {
    "pass4.query1": "Pandas reconciliation summary; failures indicate weak audit counting across complete chains, missing dimensions, and unused dimension rows.",
    "pass4.query2": "Complete-chain condition/pathway aggregation; hard parts are expression mapping, pathway grouping, and exact numeric rounding.",
    "pass4.query3": "Complete-chain non-reference batch/gene-role summary; models must filter genotype, compute VAF, and map expression to PGR5 correctly.",
    "pass4.query4": "Genes observed in both control and non-control conditions; this is a narrow decision-support filter with one expected row.",
    "pass4.query5": "Gene-preserving profile through variant, fact, and sample joins; failures usually mishandle zero-call genes, distinct matched samples, or expression averaging.",
    "pass4.query6": "Sample-level burden table; models must filter non-reference high/moderate complete-chain calls while preserving zero-burden samples.",
    "pass4.query7": "Union-style orphan-key report; failures tend to miss one source table, duplicate keys, or assign the wrong orphan type.",
    "pass4.query8": "Final presentation table; this stresses complete-chain filtering, matched expression mapping, VAF/log2 arithmetic, exact column order, and multi-key sorting.",
}


def case_number(case_id: str) -> int:
    return int(case_id.split("query")[1])


def load_rows(results_dir: Path) -> list[dict]:
    rows = []
    with (results_dir / "detailed_results.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["pass"] == "4":
                row["_failure_mode"] = base.classify_failure(row)
                rows.append(row)
    return rows


def build_summaries(rows: list[dict]):
    by_model = defaultdict(list)
    by_case = defaultdict(list)
    for row in rows:
        by_model[row["model"]].append(row)
        by_case[row["case_id"]].append(row)

    model_summary = []
    for model, items in by_model.items():
        exact = sum(base.as_bool(r["exact_match"]) for r in items)
        modes = Counter(r["_failure_mode"] for r in items)
        model_summary.append(
            {
                "model": model,
                "display_model": base.MODEL_DISPLAY.get(model, model.replace(":latest", "")),
                "cases": len(items),
                "exact_matches": exact,
                "accuracy": exact / len(items),
                "total_score": sum(base.as_float(r["score"]) for r in items),
                "mean_score": base.mean(base.as_float(r["score"]) for r in items),
                "valid_json_rate": base.mean(base.as_bool(r["valid_json"]) for r in items),
                "mean_aligned_cell_accuracy": base.mean(base.as_float(r["aligned_cell_accuracy"]) for r in items),
                "row_count_match_rate": base.mean(base.as_bool(r["row_count_match"]) for r in items),
                "total_wall_s": sum(base.as_float(r["client_wall_s"]) for r in items),
                "mean_gen_tps": base.mean(base.as_float(r["server_gen_tps"]) for r in items),
                "mean_gpu_share": base.mean(base.as_float(r["ps_vram_ratio"]) for r in items),
                "exact": modes["exact"],
                "row_count_mismatch": modes["row_count_mismatch"],
                "order_only": modes["order_only"],
                "same_count_wrong_values": modes["same_count_wrong_values"],
                "type_only": modes["type_only"],
                "column_error": modes["column_error"],
                "invalid_json_or_error": modes["invalid_json_or_error"],
            }
        )

    model_summary.sort(
        key=lambda r: (
            -r["exact_matches"],
            -r["mean_aligned_cell_accuracy"],
            r["total_wall_s"],
            r["model"],
        )
    )

    case_summary = []
    for case_id in sorted(by_case, key=case_number):
        items = by_case[case_id]
        modes = Counter(r["_failure_mode"] for r in items)
        exact = sum(base.as_bool(r["exact_match"]) for r in items)
        row_mismatch = sum(not base.as_bool(r["row_count_match"]) for r in items)
        same_count_wrong = sum(
            base.as_bool(r["row_count_match"]) and not base.as_bool(r["exact_match"])
            for r in items
        )
        case_summary.append(
            {
                "case_id": case_id,
                "query": f"Q{case_number(case_id)}",
                "semantic_focus": QUERY_LABELS[case_id].replace("\n", " "),
                "exact_models": exact,
                "accuracy": exact / len(items),
                "mean_score": base.mean(base.as_float(r["score"]) for r in items),
                "mean_aligned_cell_accuracy": base.mean(base.as_float(r["aligned_cell_accuracy"]) for r in items),
                "row_count_mismatch_models": row_mismatch,
                "same_count_but_wrong_models": same_count_wrong,
                "order_only": modes["order_only"],
                "type_only": modes["type_only"],
                "column_error": modes["column_error"],
                "dominant_failure_mode": modes.most_common(1)[0][0],
                "note": QUERY_NOTES[case_id],
            }
        )

    return model_summary, case_summary


def render_figure(rows: list[dict], model_summary: list[dict], case_summary: list[dict], out_base: Path) -> None:
    models = [m["model"] for m in model_summary]
    model_labels = [m["display_model"] for m in model_summary]
    cases = [c["case_id"] for c in case_summary]
    case_labels = [QUERY_LABELS[c] for c in cases]
    row_lookup = {(r["model"], r["case_id"]): r for r in rows}
    exact_matrix = [
        [1 if base.as_bool(row_lookup[(model, case)]["exact_match"]) else 0 for case in cases]
        for model in models
    ]
    cell_matrix = [
        [base.as_float(row_lookup[(model, case)]["aligned_cell_accuracy"]) for case in cases]
        for model in models
    ]

    fig = plt.figure(figsize=(18, 14), facecolor=base.BLUE_BG, constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.05, 1.15, 1.0])
    fig.suptitle(
        "AIBioBench Pass 4: Extra-Hard Pandas Audits and Presentation Tables",
        fontsize=22,
        fontweight="bold",
        color=base.BLUE_TEXT,
    )

    ax1 = fig.add_subplot(gs[0, 0])
    y = list(range(len(model_summary)))
    exacts = [m["exact_matches"] for m in model_summary]
    bar_colors = [
        base.BLUE_DARK if x >= 4 else base.BLUE if x >= 3 else base.BLUE_MED if x >= 2 else base.BLUE_LIGHT
        for x in exacts
    ]
    bars = ax1.barh(y, exacts, color=bar_colors)
    ax1.set_yticks(y, model_labels)
    ax1.invert_yaxis()
    ax1.set_xlim(0, 8)
    ax1.set_xlabel("Exact matches out of 8 pass-4 cases", color=base.BLUE_TEXT)
    ax1.set_title("Pass-4 Accuracy by Model", color=base.BLUE_TEXT, fontweight="bold")
    ax1.grid(axis="x", color="#D4EAF7", linewidth=1)
    for bar, item in zip(bars, model_summary):
        ax1.text(
            bar.get_width() + 0.07,
            bar.get_y() + bar.get_height() / 2,
            f"{item['exact_matches']}/8  ({100*item['accuracy']:.0f}%)",
            va="center",
            color=base.BLUE_TEXT,
            fontsize=10,
        )

    ax2 = fig.add_subplot(gs[0, 1])
    partial_accuracy = [m["mean_aligned_cell_accuracy"] for m in model_summary]
    ax2.scatter(
        [m["mean_gen_tps"] for m in model_summary],
        partial_accuracy,
        s=[130 + 420 * m["mean_gpu_share"] for m in model_summary],
        color=base.BLUE,
        alpha=0.82,
        edgecolors=base.BLUE_DARK,
        linewidth=1.2,
    )
    for m in model_summary:
        ax2.annotate(
            m["display_model"].replace(" ", "\n", 1),
            (m["mean_gen_tps"], m["mean_aligned_cell_accuracy"]),
            xytext=(6, 5),
            textcoords="offset points",
            fontsize=8,
            color=base.BLUE_TEXT,
        )
    ax2.set_xlabel("Mean generation tokens/sec", color=base.BLUE_TEXT)
    ax2.set_ylabel("Mean aligned cell accuracy", color=base.BLUE_TEXT)
    ax2.set_title("Throughput vs Partial Accuracy", color=base.BLUE_TEXT, fontweight="bold")
    ax2.set_xlim(left=0)
    ax2.set_ylim(0, min(1.0, max(partial_accuracy) + 0.18))
    ax2.grid(color="#D4EAF7", linewidth=1)

    ax3 = fig.add_subplot(gs[1, 0])
    exact_cmap = ListedColormap([base.BLUE_PALE, base.BLUE_DARK])
    ax3.imshow(exact_matrix, aspect="auto", cmap=exact_cmap, vmin=0, vmax=1)
    ax3.set_xticks(range(len(cases)), case_labels)
    ax3.set_yticks(range(len(models)), model_labels)
    ax3.set_title("Exact-Match Heatmap", color=base.BLUE_TEXT, fontweight="bold")
    for i in range(len(models)):
        for j in range(len(cases)):
            ax3.text(
                j,
                i,
                "1" if exact_matrix[i][j] else "0",
                ha="center",
                va="center",
                color="white" if exact_matrix[i][j] else base.BLUE_MUTED,
                fontsize=9,
                fontweight="bold",
            )

    ax4 = fig.add_subplot(gs[1, 1])
    cell_cmap = LinearSegmentedColormap.from_list(
        "pass4_blues", [base.BLUE_PALE, base.BLUE_LIGHT, base.BLUE_MED, base.BLUE_DARK]
    )
    im = ax4.imshow(cell_matrix, aspect="auto", cmap=cell_cmap, vmin=0, vmax=1)
    ax4.set_xticks(range(len(cases)), case_labels)
    ax4.set_yticks(range(len(models)), model_labels)
    ax4.set_title("Aligned Cell Accuracy: Partial Credit Pattern", color=base.BLUE_TEXT, fontweight="bold")
    for i in range(len(models)):
        for j in range(len(cases)):
            val = cell_matrix[i][j]
            ax4.text(
                j,
                i,
                f"{val:.0%}",
                ha="center",
                va="center",
                color="white" if val > 0.64 else base.BLUE_TEXT,
                fontsize=8,
                fontweight="bold" if val >= 1.0 else "normal",
            )
    cbar = fig.colorbar(im, ax=ax4, fraction=0.025, pad=0.02)
    cbar.ax.tick_params(labelsize=8, colors=base.BLUE_TEXT)

    ax5 = fig.add_subplot(gs[2, 0])
    mode_order = [
        ("exact", "Exact", base.BLUE_DARK),
        ("order_only", "Correct rows, wrong order", base.BLUE),
        ("type_only", "Type only", "#4FA3D9"),
        ("same_count_wrong_values", "Same count, wrong values", "#8FC6E8"),
        ("row_count_mismatch", "Wrong row count", "#CBE5F6"),
        ("column_error", "Column error", "#DDEFF9"),
    ]
    bottoms = [0] * len(cases)
    for mode, label, color in mode_order:
        vals = [sum(1 for r in rows if r["case_id"] == case and r["_failure_mode"] == mode) for case in cases]
        ax5.bar(range(len(cases)), vals, bottom=bottoms, label=label, color=color, edgecolor=base.BLUE_BG)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax5.set_xticks(range(len(cases)), [f"Q{i + 1}" for i in range(len(cases))])
    ax5.set_ylim(0, 9)
    ax5.set_ylabel("Models", color=base.BLUE_TEXT)
    ax5.set_title("Failure Mode by Query", color=base.BLUE_TEXT, fontweight="bold")
    ax5.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=9)
    ax5.grid(axis="y", color="#D4EAF7", linewidth=1)

    ax6 = fig.add_subplot(gs[2, 1])
    avg_cells = [c["mean_aligned_cell_accuracy"] for c in case_summary]
    exact_by_case = [c["exact_models"] for c in case_summary]
    ax6.plot(range(len(cases)), avg_cells, color=base.BLUE_DARK, linewidth=2.7, marker="o", markersize=8)
    ax6.fill_between(range(len(cases)), avg_cells, color=base.BLUE_LIGHT, alpha=0.45)
    for idx, (avg_cell, exact) in enumerate(zip(avg_cells, exact_by_case)):
        ax6.text(idx, min(avg_cell + 0.035, 1.03), f"{exact}/9 exact", ha="center", color=base.BLUE_TEXT, fontsize=9)
    ax6.set_xticks(range(len(cases)), [f"Q{i + 1}" for i in range(len(cases))])
    ax6.set_ylim(0, 1.08)
    ax6.set_ylabel("Mean aligned cell accuracy", color=base.BLUE_TEXT)
    ax6.set_title("Extra-Hard Task Solvability by Query", color=base.BLUE_TEXT, fontweight="bold")
    ax6.grid(axis="y", color="#D4EAF7", linewidth=1)

    for ax in fig.axes:
        ax.set_facecolor("white")
        for spine in ax.spines.values():
            spine.set_color("#C7E0F2")
        ax.tick_params(colors=base.BLUE_TEXT)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def write_notes(path: Path, model_summary: list[dict], case_summary: list[dict]) -> None:
    lines = [
        "# AIBioBench Pass 4 Analysis",
        "",
        "Pass 4 contains eight extra-hard Python/pandas tasks in the completed run. It stresses reconciliation metrics, complete-chain aggregation, expression mapping, sample burden scoring, orphan-key reporting, and final presentation-table construction.",
        "",
        "## Model Summary",
        "",
        "| Model | Exact | Accuracy | Mean Cell Accuracy | Row Count Match | Wall Time | Mean Gen TPS |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for m in model_summary:
        lines.append(
            f"| {m['display_model']} | {m['exact_matches']}/8 | {100*m['accuracy']:.1f}% | "
            f"{100*m['mean_aligned_cell_accuracy']:.1f}% | {100*m['row_count_match_rate']:.1f}% | "
            f"{m['total_wall_s']:.1f}s | {m['mean_gen_tps']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Case Summary",
            "",
            "| Query | Exact Models | Mean Cell Accuracy | Row Count Mismatches | Same Count But Wrong | Dominant Failure |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for c in case_summary:
        lines.append(
            f"| {c['query']} | {c['exact_models']}/9 | {100*c['mean_aligned_cell_accuracy']:.1f}% | "
            f"{c['row_count_mismatch_models']} | {c['same_count_but_wrong_models']} | {c['dominant_failure_mode']} |"
        )
    lines.extend(["", "## Query Notes", ""])
    for c in case_summary:
        lines.append(f"- **{c['query']}**: {c['note']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: pass4_analysis.py <results_dir>", file=sys.stderr)
        return 2

    results_dir = Path(sys.argv[1]).resolve()
    if not (results_dir / "detailed_results.csv").exists():
        print(f"missing detailed_results.csv in {results_dir}", file=sys.stderr)
        return 1

    out_dir = results_dir / "pass4_analysis"
    out_dir.mkdir(exist_ok=True)

    rows = load_rows(results_dir)
    if not rows:
        print("no pass-4 rows found", file=sys.stderr)
        return 1

    model_summary, case_summary = build_summaries(rows)

    model_fields = [
        "model",
        "display_model",
        "cases",
        "exact_matches",
        "accuracy",
        "total_score",
        "mean_score",
        "valid_json_rate",
        "mean_aligned_cell_accuracy",
        "row_count_match_rate",
        "total_wall_s",
        "mean_gen_tps",
        "mean_gpu_share",
        "exact",
        "row_count_mismatch",
        "order_only",
        "same_count_wrong_values",
        "type_only",
        "column_error",
        "invalid_json_or_error",
    ]
    case_fields = [
        "case_id",
        "query",
        "semantic_focus",
        "exact_models",
        "accuracy",
        "mean_score",
        "mean_aligned_cell_accuracy",
        "row_count_mismatch_models",
        "same_count_but_wrong_models",
        "order_only",
        "type_only",
        "column_error",
        "dominant_failure_mode",
        "note",
    ]
    base.write_csv(out_dir / "pass4_model_summary.csv", model_summary, model_fields)
    base.write_csv(out_dir / "pass4_case_summary.csv", case_summary, case_fields)

    failure_rows = [
        {
            "model": r["model"],
            "case_id": r["case_id"],
            "exact_match": r["exact_match"],
            "score": r["score"],
            "failure_mode": r["_failure_mode"],
            "aligned_cell_accuracy": r["aligned_cell_accuracy"],
            "row_count_match": r["row_count_match"],
            "pred_row_count": r["pred_row_count"],
            "gold_row_count": r["gold_row_count"],
            "missing_rows_count": r["missing_rows_count"],
            "extra_rows_count": r["extra_rows_count"],
        }
        for r in rows
    ]
    base.write_csv(
        out_dir / "pass4_failure_modes.csv",
        failure_rows,
        [
            "model",
            "case_id",
            "exact_match",
            "score",
            "failure_mode",
            "aligned_cell_accuracy",
            "row_count_match",
            "pred_row_count",
            "gold_row_count",
            "missing_rows_count",
            "extra_rows_count",
        ],
    )

    render_figure(rows, model_summary, case_summary, out_dir / "pass4_visual_report")
    write_notes(out_dir / "pass4_analysis_notes.md", model_summary, case_summary)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
