#!/usr/bin/env python3
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap


QUERY_LABELS = {
    "pass3.query1": "Q1\njoin\nstatus",
    "pass3.query2": "Q2\ntissue-gene\nVAF",
    "pass3.query3": "Q3\ngene\ncoverage",
    "pass3.query4": "Q4\nhigh\nimpact",
    "pass3.query5": "Q5\ngenotype\nclasses",
    "pass3.query6": "Q6\ntissue\nrank",
    "pass3.query7": "Q7\nanti-join\naudit",
    "pass3.query8": "Q8\ndecision\nroles",
}

QUERY_NOTES = {
    "pass3.query1": "Full snowflake left join with row-level join_status classification; failures usually confuse MISSING_GENE, MISSING_SAMPLE, and MISSING_VARIANT edge rows.",
    "pass3.query2": "Complete-chain tissue/gene aggregation with VAF arithmetic; failures cluster around excluding incomplete chains and averaging VAF per fact row.",
    "pass3.query3": "Gene-preserving coverage audit; models must include zero-call genes and count fact rows through variants without inventing missing genes.",
    "pass3.query4": "High-impact condition summary after sample and variant joins; common errors are missing zero-alt high-impact calls or using the wrong denominator.",
    "pass3.query5": "Sample-preserving genotype-class summary; failures usually mishandle S5, reference calls, or non-reference quality averaging.",
    "pass3.query6": "Complete-chain tissue/gene ranking; models must aggregate first, then dense-rank within tissue and preserve the requested sort order.",
    "pass3.query7": "Anti-join audit across sample, variant, and gene dimensions; failures tend to miss unused dimension rows or assign the wrong reason.",
    "pass3.query8": "Decision-support grouping over complete-chain non-reference calls; errors come from leaking reference calls or grouping by the wrong gene role.",
}

MODEL_DISPLAY = {
    "gemma4-31b-256:latest": "Gemma 31B 256k",
    "gemma4-31b-64:latest": "Gemma 31B 64k",
    "gemma4-26b-256:latest": "Gemma 26B 256k",
    "gemma4-26b-64:latest": "Gemma 26B 64k",
    "qwen36-256:latest": "Qwen 36B 256k",
    "qwen36-64:latest": "Qwen 36B 64k",
    "qwen3-coder-30b-64:latest": "Qwen Coder 30B 64k",
    "qwen3-coder-30b-256:latest": "Qwen Coder 30B 256k",
    "phi4-mini-128:latest": "Phi4 Mini 128k",
}

BLUE_DARK = "#073B7A"
BLUE = "#1368AA"
BLUE_MED = "#3B8FD4"
BLUE_LIGHT = "#A9D6F5"
BLUE_PALE = "#E8F4FC"
BLUE_BG = "#F6FBFF"
BLUE_TEXT = "#082B49"
BLUE_MUTED = "#5B7C99"


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
        if text.isdigit():
            return int(text)
        if "." in text:
            try:
                return float(text)
            except ValueError:
                pass
    return value


def case_number(case_id: str) -> int:
    return int(case_id.split("query")[1])


def classify_failure(row: dict) -> str:
    if row["status"] != "ok" or not as_bool(row["valid_json"]):
        return "invalid_json_or_error"
    if not as_bool(row["column_exact_match"]):
        return "column_error"
    if as_bool(row["exact_match"]):
        return "exact"

    gold_rows = json.loads(row["gold_rows_json"])
    pred_rows = json.loads(row["parsed_rows_json"])
    if coerce_numeric_strings(pred_rows) == coerce_numeric_strings(gold_rows):
        return "type_only"

    if not as_bool(row["row_count_match"]):
        return "row_count_mismatch"

    if int(row["missing_rows_count"]) == 0 and int(row["extra_rows_count"]) == 0:
        return "order_only"

    return "same_count_wrong_values"


def load_rows(results_dir: Path) -> list[dict]:
    rows = []
    with (results_dir / "detailed_results.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["pass"] == "3":
                row["_failure_mode"] = classify_failure(row)
                rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def build_summaries(rows: list[dict]):
    by_model = defaultdict(list)
    by_case = defaultdict(list)
    for row in rows:
        by_model[row["model"]].append(row)
        by_case[row["case_id"]].append(row)

    model_summary = []
    for model, items in by_model.items():
        exact = sum(as_bool(r["exact_match"]) for r in items)
        modes = Counter(r["_failure_mode"] for r in items)
        model_summary.append(
            {
                "model": model,
                "display_model": MODEL_DISPLAY.get(model, model.replace(":latest", "")),
                "cases": len(items),
                "exact_matches": exact,
                "accuracy": exact / len(items),
                "total_score": sum(as_float(r["score"]) for r in items),
                "mean_score": mean(as_float(r["score"]) for r in items),
                "valid_json_rate": mean(as_bool(r["valid_json"]) for r in items),
                "mean_aligned_cell_accuracy": mean(as_float(r["aligned_cell_accuracy"]) for r in items),
                "row_count_match_rate": mean(as_bool(r["row_count_match"]) for r in items),
                "total_wall_s": sum(as_float(r["client_wall_s"]) for r in items),
                "mean_gen_tps": mean(as_float(r["server_gen_tps"]) for r in items),
                "mean_gpu_share": mean(as_float(r["ps_vram_ratio"]) for r in items),
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
        exact = sum(as_bool(r["exact_match"]) for r in items)
        row_mismatch = sum(not as_bool(r["row_count_match"]) for r in items)
        same_count_wrong = sum(
            as_bool(r["row_count_match"]) and not as_bool(r["exact_match"]) for r in items
        )
        case_summary.append(
            {
                "case_id": case_id,
                "query": f"Q{case_number(case_id)}",
                "semantic_focus": QUERY_LABELS[case_id].replace("\n", " "),
                "exact_models": exact,
                "accuracy": exact / len(items),
                "mean_score": mean(as_float(r["score"]) for r in items),
                "mean_aligned_cell_accuracy": mean(as_float(r["aligned_cell_accuracy"]) for r in items),
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
        [1 if as_bool(row_lookup[(model, case)]["exact_match"]) else 0 for case in cases]
        for model in models
    ]
    cell_matrix = [
        [as_float(row_lookup[(model, case)]["aligned_cell_accuracy"]) for case in cases]
        for model in models
    ]

    fig = plt.figure(figsize=(18, 14), facecolor=BLUE_BG, constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.05, 1.15, 1.0])
    fig.suptitle(
        "AIBioBench Pass 3: Hard Join Audits, Ranking, and Decision Summaries",
        fontsize=22,
        fontweight="bold",
        color=BLUE_TEXT,
    )

    ax1 = fig.add_subplot(gs[0, 0])
    y = list(range(len(model_summary)))
    exacts = [m["exact_matches"] for m in model_summary]
    bar_colors = [
        BLUE_DARK if x >= 4 else BLUE if x >= 3 else BLUE_MED if x >= 2 else BLUE_LIGHT
        for x in exacts
    ]
    bars = ax1.barh(y, exacts, color=bar_colors)
    ax1.set_yticks(y, model_labels)
    ax1.invert_yaxis()
    ax1.set_xlim(0, 8)
    ax1.set_xlabel("Exact matches out of 8 pass-3 cases", color=BLUE_TEXT)
    ax1.set_title("Pass-3 Accuracy by Model", color=BLUE_TEXT, fontweight="bold")
    ax1.grid(axis="x", color="#D4EAF7", linewidth=1)
    for bar, item in zip(bars, model_summary):
        ax1.text(
            bar.get_width() + 0.07,
            bar.get_y() + bar.get_height() / 2,
            f"{item['exact_matches']}/8  ({100*item['accuracy']:.0f}%)",
            va="center",
            color=BLUE_TEXT,
            fontsize=10,
        )

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.scatter(
        [m["mean_gen_tps"] for m in model_summary],
        [m["exact_matches"] for m in model_summary],
        s=[130 + 420 * m["mean_gpu_share"] for m in model_summary],
        color=BLUE,
        alpha=0.82,
        edgecolors=BLUE_DARK,
        linewidth=1.2,
    )
    for m in model_summary:
        ax2.annotate(
            m["display_model"].replace(" ", "\n", 1),
            (m["mean_gen_tps"], m["exact_matches"]),
            xytext=(6, 5),
            textcoords="offset points",
            fontsize=8,
            color=BLUE_TEXT,
        )
    ax2.set_xlabel("Mean generation tokens/sec", color=BLUE_TEXT)
    ax2.set_ylabel("Exact matches", color=BLUE_TEXT)
    ax2.set_title("Throughput vs Exactness", color=BLUE_TEXT, fontweight="bold")
    ax2.set_xlim(left=0)
    ax2.set_ylim(-0.4, max(exacts) + 0.8)
    ax2.grid(color="#D4EAF7", linewidth=1)

    ax3 = fig.add_subplot(gs[1, 0])
    exact_cmap = ListedColormap([BLUE_PALE, BLUE_DARK])
    ax3.imshow(exact_matrix, aspect="auto", cmap=exact_cmap, vmin=0, vmax=1)
    ax3.set_xticks(range(len(cases)), case_labels)
    ax3.set_yticks(range(len(models)), model_labels)
    ax3.set_title("Exact-Match Heatmap", color=BLUE_TEXT, fontweight="bold")
    for i in range(len(models)):
        for j in range(len(cases)):
            ax3.text(
                j,
                i,
                "1" if exact_matrix[i][j] else "0",
                ha="center",
                va="center",
                color="white" if exact_matrix[i][j] else BLUE_MUTED,
                fontsize=9,
                fontweight="bold",
            )

    ax4 = fig.add_subplot(gs[1, 1])
    cell_cmap = LinearSegmentedColormap.from_list("pass3_blues", [BLUE_PALE, BLUE_LIGHT, BLUE_MED, BLUE_DARK])
    im = ax4.imshow(cell_matrix, aspect="auto", cmap=cell_cmap, vmin=0, vmax=1)
    ax4.set_xticks(range(len(cases)), case_labels)
    ax4.set_yticks(range(len(models)), model_labels)
    ax4.set_title("Aligned Cell Accuracy: Partial Credit Pattern", color=BLUE_TEXT, fontweight="bold")
    for i in range(len(models)):
        for j in range(len(cases)):
            val = cell_matrix[i][j]
            ax4.text(
                j,
                i,
                f"{val:.0%}",
                ha="center",
                va="center",
                color="white" if val > 0.64 else BLUE_TEXT,
                fontsize=8,
                fontweight="bold" if val >= 1.0 else "normal",
            )
    cbar = fig.colorbar(im, ax=ax4, fraction=0.025, pad=0.02)
    cbar.ax.tick_params(labelsize=8, colors=BLUE_TEXT)

    ax5 = fig.add_subplot(gs[2, 0])
    mode_order = [
        ("exact", "Exact", BLUE_DARK),
        ("order_only", "Correct rows, wrong order", BLUE),
        ("type_only", "Type only", "#4FA3D9"),
        ("same_count_wrong_values", "Same count, wrong values", "#8FC6E8"),
        ("row_count_mismatch", "Wrong row count", "#CBE5F6"),
        ("column_error", "Column error", "#DDEFF9"),
    ]
    bottoms = [0] * len(cases)
    for mode, label, color in mode_order:
        vals = [sum(1 for r in rows if r["case_id"] == case and r["_failure_mode"] == mode) for case in cases]
        ax5.bar(range(len(cases)), vals, bottom=bottoms, label=label, color=color, edgecolor=BLUE_BG)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax5.set_xticks(range(len(cases)), [f"Q{i + 1}" for i in range(len(cases))])
    ax5.set_ylim(0, 9)
    ax5.set_ylabel("Models", color=BLUE_TEXT)
    ax5.set_title("Failure Mode by Query", color=BLUE_TEXT, fontweight="bold")
    ax5.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=9)
    ax5.grid(axis="y", color="#D4EAF7", linewidth=1)

    ax6 = fig.add_subplot(gs[2, 1])
    avg_cells = [c["mean_aligned_cell_accuracy"] for c in case_summary]
    exact_by_case = [c["exact_models"] for c in case_summary]
    ax6.plot(range(len(cases)), avg_cells, color=BLUE_DARK, linewidth=2.7, marker="o", markersize=8)
    ax6.fill_between(range(len(cases)), avg_cells, color=BLUE_LIGHT, alpha=0.45)
    for idx, (avg_cell, exact) in enumerate(zip(avg_cells, exact_by_case)):
        ax6.text(idx, min(avg_cell + 0.035, 1.03), f"{exact}/9 exact", ha="center", color=BLUE_TEXT, fontsize=9)
    ax6.set_xticks(range(len(cases)), [f"Q{i + 1}" for i in range(len(cases))])
    ax6.set_ylim(0, 1.08)
    ax6.set_ylabel("Mean aligned cell accuracy", color=BLUE_TEXT)
    ax6.set_title("Hard-Task Solvability by Query", color=BLUE_TEXT, fontweight="bold")
    ax6.grid(axis="y", color="#D4EAF7", linewidth=1)

    for ax in fig.axes:
        ax.set_facecolor("white")
        for spine in ax.spines.values():
            spine.set_color("#C7E0F2")
        ax.tick_params(colors=BLUE_TEXT)

    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def write_notes(path: Path, model_summary: list[dict], case_summary: list[dict]) -> None:
    lines = [
        "# AIBioBench Pass 3 Analysis",
        "",
        "Pass 3 contains eight hard SQL-style tasks over the plant/variant snowflake. It stresses join-status classification, complete-chain aggregation, dimension-preserving audits, ranking, anti-join logic, and decision-support grouping.",
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
        print("usage: pass3_analysis.py <results_dir>", file=sys.stderr)
        return 2

    results_dir = Path(sys.argv[1]).resolve()
    if not (results_dir / "detailed_results.csv").exists():
        print(f"missing detailed_results.csv in {results_dir}", file=sys.stderr)
        return 1

    out_dir = results_dir / "pass3_analysis"
    out_dir.mkdir(exist_ok=True)

    rows = load_rows(results_dir)
    if not rows:
        print("no pass-3 rows found", file=sys.stderr)
        return 1

    model_summary, case_summary = build_summaries(rows)

    write_csv(
        out_dir / "pass3_model_summary.csv",
        model_summary,
        [
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
        ],
    )
    write_csv(
        out_dir / "pass3_case_summary.csv",
        case_summary,
        [
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
        ],
    )

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
    write_csv(
        out_dir / "pass3_failure_modes.csv",
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

    render_figure(rows, model_summary, case_summary, out_dir / "pass3_visual_report")
    write_notes(out_dir / "pass3_analysis_notes.md", model_summary, case_summary)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
