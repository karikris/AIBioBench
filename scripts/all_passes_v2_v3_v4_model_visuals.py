#!/usr/bin/env python3
import argparse
import csv
import os
import sys
import warnings
from collections import defaultdict
from pathlib import Path
from statistics import mean

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
warnings.filterwarnings("ignore", message="Unable to import Axes3D.*")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import pass4_analysis as base


PASSES = ("1", "2", "3", "4", "5")
RUN_ORDER = ("v4", "v3", "v2")
LOAD_ORDER = ("v2", "v3", "v4")
RUN_COLORS = {"v4": base.BLUE_PALE, "v3": base.BLUE, "v2": base.BLUE_DARK}
PASS_LABELS = {"1": "Pass 1", "2": "Pass 2", "3": "Pass 3", "4": "Pass 4", "5": "Pass 5"}
METRICS = (
    ("mean_score", "Score"),
    ("mean_row_set_correctness", "Row"),
    ("mean_numeric_correctness", "Num"),
    ("mean_sort_correctness", "Sort"),
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_run_dirs(root: Path) -> dict[str, Path]:
    return {
        "v2": root / "results" / "photosynthesis_snowflake_v2",
        "v3": root / "results" / "photosynthesis_snowflake_v3",
        "v4": root / "results" / "photosynthesis_snowflake_v4",
    }


def load_rows(run_dirs: dict[str, Path]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for run, results_dir in run_dirs.items():
        path = results_dir / "detailed_results.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing detailed_results.csv for {run}: {path}")
        rows = []
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("pass") not in PASSES:
                    continue
                row["_run"] = run
                row["_display_model"] = base.canonical_model_name(row["model"])
                rows.append(row)
        out[run] = rows
    return out


def avg(values) -> float:
    values = [float(v) for v in values]
    return mean(values) if values else 0.0


def summarize(items: list[dict]) -> dict:
    attempts = len(items)
    exact = sum(base.as_bool(row.get("exact_match")) for row in items)
    return {
        "attempts": attempts,
        "exact_attempts": exact,
        "exact_attempt_rate": exact / attempts if attempts else 0.0,
        "mean_score": avg(base.as_float(row.get("score")) for row in items),
        "mean_row_set_correctness": avg(base.as_float(row.get("row_set_correctness_score")) for row in items),
        "mean_numeric_correctness": avg(base.as_float(row.get("numeric_correctness_score")) for row in items),
        "mean_sort_correctness": avg(base.as_float(row.get("sort_order_correctness_score")) for row in items),
        "avg_gen_tps": avg(base.as_float(row.get("server_gen_tps")) for row in items),
        "total_wall_s": sum(base.as_float(row.get("client_wall_s")) for row in items),
    }


def add_prefixed(row: dict, prefix: str, summary: dict, keys: tuple[str, ...]) -> None:
    for key in keys:
        row[f"{prefix}_{key}"] = summary.get(key, 0)


def build_summaries(rows_by_run: dict[str, list[dict]]) -> tuple[list[dict], list[dict], list[str]]:
    models = sorted({row["model"] for rows in rows_by_run.values() for row in rows}, key=base.canonical_model_name)
    total_keys = (
        "attempts",
        "exact_attempts",
        "exact_attempt_rate",
        "mean_score",
        "mean_row_set_correctness",
        "mean_numeric_correctness",
        "mean_sort_correctness",
        "avg_gen_tps",
        "total_wall_s",
    )

    model_rows = []
    model_pass_rows = []
    for model in models:
        display = base.canonical_model_name(model)
        row = {"model": model, "display_model": display}
        for run in LOAD_ORDER:
            items = [item for item in rows_by_run[run] if item["model"] == model]
            add_prefixed(row, run, summarize(items), total_keys)
        row["delta_v4_v2_exact_attempts"] = int(row["v4_exact_attempts"]) - int(row["v2_exact_attempts"])
        row["delta_v4_v3_exact_attempts"] = int(row["v4_exact_attempts"]) - int(row["v3_exact_attempts"])
        row["delta_v4_v2_mean_score"] = float(row["v4_mean_score"]) - float(row["v2_mean_score"])
        row["delta_v4_v3_mean_score"] = float(row["v4_mean_score"]) - float(row["v3_mean_score"])
        model_rows.append(row)

        for pass_no in PASSES:
            for run in LOAD_ORDER:
                items = [
                    item
                    for item in rows_by_run[run]
                    if item["model"] == model and item["pass"] == pass_no
                ]
                pass_summary = summarize(items)
                model_pass_rows.append(
                    {
                        "model": model,
                        "display_model": display,
                        "pass": pass_no,
                        "pass_label": PASS_LABELS[pass_no],
                        "run": run,
                        **pass_summary,
                    }
                )

    model_rows.sort(
        key=lambda row: (
            -int(row["v4_exact_attempts"]),
            -float(row["v4_mean_score"]),
            float(row["v4_total_wall_s"]),
            row["display_model"],
        )
    )
    model_order = [row["model"] for row in model_rows]
    model_pass_rows.sort(key=lambda row: (model_order.index(row["model"]), int(row["pass"]), RUN_ORDER.index(row["run"])))
    return model_rows, model_pass_rows, model_order


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


def save(fig, out_base: Path) -> None:
    fig.savefig(out_base.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(out_base.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def render_rank_table(model_rows: list[dict], out_base: Path) -> None:
    fig, ax = plt.subplots(figsize=(24, 13), facecolor=base.PAGE_BG)
    ax.set_axis_off()
    ax.set_title(
        "AIBioBench v2-v4 Model Ranking: Sorted by v4 Exact Responses",
        color=base.TEXT,
        fontsize=22,
        fontweight="bold",
        pad=26,
    )
    ax.text(
        0.0,
        1.015,
        "Each available model/run covers up to 150 attempts: 50 benchmark cases x 3 repeats. Filtered runs may have missing model rows.",
        transform=ax.transAxes,
        color=base.BLUE_PALE,
        fontsize=11,
        va="bottom",
    )

    columns = [
        "Rank",
        "Model",
        "Exact\nv4",
        "Exact\nv3",
        "Exact\nv2",
        "Delta\nv4-v2",
        "v4\nScore",
        "v4\nRow",
        "v4\nNum",
        "v4\nSort",
        "TPS\nv4",
        "Time h\nv4",
        "Time h\nv3",
        "Time h\nv2",
    ]
    table_rows = []
    for rank, row in enumerate(model_rows, start=1):
        table_rows.append(
            [
                rank,
                row["display_model"],
                int(row["v4_exact_attempts"]),
                int(row["v3_exact_attempts"]),
                int(row["v2_exact_attempts"]),
                int(row["delta_v4_v2_exact_attempts"]),
                f"{float(row['v4_mean_score']):.3f}",
                f"{float(row['v4_mean_row_set_correctness']):.3f}",
                f"{float(row['v4_mean_numeric_correctness']):.3f}",
                f"{float(row['v4_mean_sort_correctness']):.3f}",
                f"{float(row['v4_avg_gen_tps']):.1f}",
                f"{float(row['v4_total_wall_s']) / 3600:.2f}",
                f"{float(row['v3_total_wall_s']) / 3600:.2f}",
                f"{float(row['v2_total_wall_s']) / 3600:.2f}",
            ]
        )

    col_widths = [0.045, 0.20, 0.065, 0.065, 0.065, 0.07, 0.07, 0.065, 0.065, 0.065, 0.06, 0.07, 0.07, 0.07]
    table = ax.table(
        cellText=table_rows,
        colLabels=columns,
        loc="upper left",
        colWidths=col_widths,
        cellLoc="center",
        bbox=[0, 0.02, 1, 0.92],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1, 1.55)

    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor(base.GRID)
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_facecolor(base.BLUE_DARK)
            cell.set_text_props(color=base.TEXT, weight="bold")
        else:
            cell.set_facecolor(base.PANEL_BG if r % 2 else "#14334D")
            cell.set_text_props(color=base.TEXT)
            if c == 1:
                cell.set_text_props(ha="left", color=base.TEXT)
            if c == 2:
                cell.set_facecolor("#275D86")
                cell.set_text_props(color=base.BLUE_PALE, weight="bold")
            if c == 5:
                delta = int(table_rows[r - 1][c])
                cell.set_text_props(color=base.BLUE_PALE if delta >= 0 else base.FAIL_PALE, weight="bold")

    save(fig, out_base)


def render_exact_counts(model_rows: list[dict], out_base: Path) -> None:
    fig, ax = plt.subplots(figsize=(18, 13), facecolor=base.PAGE_BG)
    y = list(range(len(model_rows)))
    height = 0.22
    offsets = {"v4": -height, "v3": 0.0, "v2": height}
    for run in RUN_ORDER:
        values = [int(row[f"{run}_exact_attempts"]) for row in model_rows]
        ax.barh(
            [i + offsets[run] for i in y],
            values,
            height=height,
            color=RUN_COLORS[run],
            label=run,
            edgecolor=base.PANEL_BG,
        )
        for yi, value in zip(y, values):
            ax.text(value + 1.0, yi + offsets[run], str(value), va="center", color=base.TEXT, fontsize=8)

    ax.set_yticks(y, [row["display_model"] for row in model_rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 155)
    ax.set_xlabel("Exact responses out of up to 150 attempts")
    ax.set_title("Exact Response Counts by Model and Run", fontsize=20, fontweight="bold", pad=18)
    ax.grid(axis="x", color=base.GRID, alpha=0.65)
    ax.legend(frameon=False, labelcolor=base.TEXT, loc="lower right")
    style_axis(ax)
    save(fig, out_base)


def metric_lookup(model_pass_rows: list[dict]) -> dict[tuple[str, str, str], dict]:
    return {(row["model"], row["pass"], row["run"]): row for row in model_pass_rows}


def render_metric_heatmaps(model_rows: list[dict], model_pass_rows: list[dict], out_base: Path) -> None:
    lookup = metric_lookup(model_pass_rows)
    models = [row["model"] for row in model_rows]
    labels = [row["display_model"] for row in model_rows]
    cmap = LinearSegmentedColormap.from_list("metric_blue", [base.BLUE_DARK, base.BLUE, base.BLUE_LIGHT, base.BLUE_PALE])

    fig, axes = plt.subplots(
        len(PASSES),
        1,
        figsize=(24, 30),
        facecolor=base.PAGE_BG,
        constrained_layout=True,
    )
    fig.suptitle(
        "Mean Score Components by Pass, Run, and Model",
        color=base.TEXT,
        fontsize=23,
        fontweight="bold",
    )
    fig.text(
        0.01,
        0.986,
        "Cells show mean values from 0 to 1. Columns are grouped by run inside each pass: Score, Row, Num, Sort.",
        color=base.BLUE_PALE,
        fontsize=11,
    )

    xlabels = [f"{run.upper()} {metric_label}" for run in RUN_ORDER for _, metric_label in METRICS]
    for ax, pass_no in zip(axes, PASSES):
        matrix = []
        for model in models:
            row_values = []
            for run in RUN_ORDER:
                rec = lookup.get((model, pass_no, run), {})
                for metric, _label in METRICS:
                    row_values.append(float(rec.get(metric, 0.0) or 0.0))
            matrix.append(row_values)
        image = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0.0, vmax=1.0)
        ax.set_title(PASS_LABELS[pass_no], fontsize=15, fontweight="bold", loc="left")
        ax.set_xticks(range(len(xlabels)), xlabels, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(labels)), labels, fontsize=8)
        for boundary in (3.5, 7.5):
            ax.axvline(boundary, color=base.PAGE_BG, linewidth=2.0)
        for i, values in enumerate(matrix):
            for j, value in enumerate(values):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", color=base.TEXT if value < 0.74 else base.PAGE_BG, fontsize=5.6)
        style_axis(ax)

    cbar = fig.colorbar(image, ax=axes, shrink=0.62, pad=0.01)
    cbar.ax.tick_params(colors=base.TEXT)
    cbar.outline.set_edgecolor(base.GRID)
    save(fig, out_base)


def render_gen_tps_heatmap(model_rows: list[dict], model_pass_rows: list[dict], out_base: Path) -> None:
    lookup = metric_lookup(model_pass_rows)
    models = [row["model"] for row in model_rows]
    labels = [row["display_model"] for row in model_rows]
    columns = [(pass_no, run) for pass_no in PASSES for run in RUN_ORDER]
    xlabels = [f"P{pass_no} {run.upper()}" for pass_no, run in columns]
    matrix = [
        [float(lookup.get((model, pass_no, run), {}).get("avg_gen_tps", 0.0) or 0.0) for pass_no, run in columns]
        for model in models
    ]
    vmax = max([value for row in matrix for value in row] or [1.0])
    cmap = LinearSegmentedColormap.from_list("speed_blue", [base.BLUE_DARK, base.BLUE, base.BLUE_LIGHT, base.BLUE_PALE])

    fig, ax = plt.subplots(figsize=(24, 13), facecolor=base.PAGE_BG, constrained_layout=True)
    image = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0.0, vmax=vmax)
    ax.set_title("Average Token Generation Speed by Pass and Run", fontsize=21, fontweight="bold", pad=18)
    ax.text(
        0.0,
        1.04,
        "Cells show average `server_gen_tps`; columns are grouped by pass, with runs ordered v4, v3, v2.",
        transform=ax.transAxes,
        color=base.BLUE_PALE,
        fontsize=11,
    )
    ax.set_xticks(range(len(xlabels)), xlabels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(labels)), labels, fontsize=9)
    for boundary in (2.5, 5.5, 8.5, 11.5):
        ax.axvline(boundary, color=base.PAGE_BG, linewidth=2.0)
    for i, values in enumerate(matrix):
        for j, value in enumerate(values):
            ax.text(j, i, f"{value:.1f}", ha="center", va="center", color=base.TEXT if value < vmax * 0.72 else base.PAGE_BG, fontsize=6.2)
    style_axis(ax)
    cbar = fig.colorbar(image, ax=ax, shrink=0.75, pad=0.01)
    cbar.ax.tick_params(colors=base.TEXT)
    cbar.outline.set_edgecolor(base.GRID)
    save(fig, out_base)


def render_total_runtime(model_rows: list[dict], out_base: Path) -> None:
    fig, ax = plt.subplots(figsize=(18, 13), facecolor=base.PAGE_BG)
    y = list(range(len(model_rows)))
    height = 0.22
    offsets = {"v4": -height, "v3": 0.0, "v2": height}
    for run in RUN_ORDER:
        values = [float(row[f"{run}_total_wall_s"]) / 3600.0 for row in model_rows]
        ax.barh(
            [i + offsets[run] for i in y],
            values,
            height=height,
            color=RUN_COLORS[run],
            label=run,
            edgecolor=base.PANEL_BG,
        )
        for yi, value in zip(y, values):
            ax.text(value + 0.025, yi + offsets[run], f"{value:.2f}h", va="center", color=base.TEXT, fontsize=7.4)

    ax.set_yticks(y, [row["display_model"] for row in model_rows])
    ax.invert_yaxis()
    ax.set_xlabel("Total client wall time for available attempts (hours)")
    ax.set_title("Total Runtime to Complete 150 Queries per Model", fontsize=20, fontweight="bold", pad=18)
    ax.grid(axis="x", color=base.GRID, alpha=0.65)
    ax.legend(frameon=False, labelcolor=base.TEXT, loc="lower right")
    style_axis(ax)
    save(fig, out_base)


def render_score_runtime_scatter(model_rows: list[dict], out_base: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(24, 8), facecolor=base.PAGE_BG, constrained_layout=True, sharey=True)
    fig.suptitle("Accuracy, Runtime, and Generation Speed Tradeoff", color=base.TEXT, fontsize=21, fontweight="bold")
    for ax, run in zip(axes, RUN_ORDER):
        x = [float(row[f"{run}_total_wall_s"]) / 3600.0 for row in model_rows]
        y = [int(row[f"{run}_exact_attempts"]) for row in model_rows]
        tps = [float(row[f"{run}_avg_gen_tps"]) for row in model_rows]
        max_tps = max(tps) if tps else 1.0
        sizes = [65 + 360 * (value / max_tps) for value in tps]
        ax.scatter(x, y, s=sizes, color=RUN_COLORS[run], edgecolor=base.BLUE_PALE, alpha=0.82, linewidth=0.8)
        for xi, yi, row in zip(x, y, model_rows):
            ax.text(xi, yi + 1.4, row["display_model"].split()[0], color=base.TEXT, fontsize=7, ha="center")
        ax.set_title(run.upper(), fontweight="bold")
        ax.set_xlabel("Total runtime (hours)")
        ax.grid(color=base.GRID, alpha=0.65)
        style_axis(ax)
    axes[0].set_ylabel("Exact responses out of 150")
    save(fig, out_base)


def write_report(path: Path, model_rows: list[dict], out_dir: Path) -> None:
    top = model_rows[:6]
    bottom = model_rows[-8:]
    lines = [
        "# AIBioBench v2-v4 all-pass model visual summary",
        "",
        "Scope: all 50 benchmark cases and 3 repeats per case, up to 150 attempts per available model/run.",
        "Model ordering: descending v4 exact responses, then v4 mean score, then lower v4 runtime.",
        "",
        "## Output files",
        "",
        "- `all_passes_v2_v3_v4_model_rank_summary.csv`",
        "- `all_passes_v2_v3_v4_model_pass_summary.csv`",
        "- `all_passes_v2_v3_v4_model_rank_table.png` / `.svg`",
        "- `all_passes_v2_v3_v4_exact_counts.png` / `.svg`",
        "- `all_passes_v2_v3_v4_pass_metric_heatmaps.png` / `.svg`",
        "- `all_passes_v2_v3_v4_gen_tps_heatmap.png` / `.svg`",
        "- `all_passes_v2_v3_v4_total_runtime.png` / `.svg`",
        "- `all_passes_v2_v3_v4_score_runtime_scatter.png` / `.svg`",
        "",
        "## Top v4 exact responders",
        "",
        "| Model | v4 exact | v3 exact | v2 exact | v4 mean score | v4 total time h | v4 avg gen TPS |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in top:
        lines.append(
            f"| {row['display_model']} | {int(row['v4_exact_attempts'])} | {int(row['v3_exact_attempts'])} | "
            f"{int(row['v2_exact_attempts'])} | {float(row['v4_mean_score']):.3f} | "
            f"{float(row['v4_total_wall_s']) / 3600:.2f} | {float(row['v4_avg_gen_tps']):.1f} |"
        )
    lines.extend(
        [
            "",
            "## Bottom v4 exact responders",
            "",
            "| Model | v4 exact | v3 exact | v2 exact | v4 mean score | v4 total time h | v4 avg gen TPS |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in bottom:
        lines.append(
            f"| {row['display_model']} | {int(row['v4_exact_attempts'])} | {int(row['v3_exact_attempts'])} | "
            f"{int(row['v2_exact_attempts'])} | {float(row['v4_mean_score']):.3f} | "
            f"{float(row['v4_total_wall_s']) / 3600:.2f} | {float(row['v4_avg_gen_tps']):.1f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> Path:
    root = repo_root()
    run_dirs = default_run_dirs(root)
    if args.v2_dir:
        run_dirs["v2"] = args.v2_dir.resolve()
    if args.v3_dir:
        run_dirs["v3"] = args.v3_dir.resolve()
    if args.v4_dir:
        run_dirs["v4"] = args.v4_dir.resolve()
    out_dir = args.out_dir.resolve() if args.out_dir else run_dirs["v4"] / "all_passes_v2_v3_v4_model_visuals"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows_by_run = load_rows(run_dirs)
    model_rows, model_pass_rows, _model_order = build_summaries(rows_by_run)

    write_csv(out_dir / "all_passes_v2_v3_v4_model_rank_summary.csv", model_rows)
    write_csv(out_dir / "all_passes_v2_v3_v4_model_pass_summary.csv", model_pass_rows)

    prefix = out_dir / "all_passes_v2_v3_v4"
    render_rank_table(model_rows, prefix.with_name(prefix.name + "_model_rank_table"))
    render_exact_counts(model_rows, prefix.with_name(prefix.name + "_exact_counts"))
    render_metric_heatmaps(model_rows, model_pass_rows, prefix.with_name(prefix.name + "_pass_metric_heatmaps"))
    render_gen_tps_heatmap(model_rows, model_pass_rows, prefix.with_name(prefix.name + "_gen_tps_heatmap"))
    render_total_runtime(model_rows, prefix.with_name(prefix.name + "_total_runtime"))
    render_score_runtime_scatter(model_rows, prefix.with_name(prefix.name + "_score_runtime_scatter"))
    write_report(out_dir / "all_passes_v2_v3_v4_model_visual_summary.md", model_rows, out_dir)

    print(out_dir)
    return out_dir


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create all-pass v2/v3/v4 model comparison visuals sorted by v4 exact counts.")
    parser.add_argument("--v2-dir", type=Path)
    parser.add_argument("--v3-dir", type=Path)
    parser.add_argument("--v4-dir", type=Path)
    parser.add_argument("--out-dir", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
