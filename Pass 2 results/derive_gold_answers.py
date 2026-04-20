#!/usr/bin/env python3
"""
Reproduce all AIBioBench gold answers from the shared dataset.

Usage:
    python derive_gold_answers.py --base .
    python derive_gold_answers.py --base ./plant_benchmark_jsonl --check
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def resolve_base(base: Path) -> Path:
    if (base / "shared_dataset.json").exists():
        return base
    if (base / "plant_benchmark_jsonl" / "shared_dataset.json").exists():
        return base / "plant_benchmark_jsonl"
    raise FileNotFoundError("Could not find shared_dataset.json in the provided base path.")


def tables_from_dataset(dataset: dict) -> Dict[str, pd.DataFrame]:
    tables: Dict[str, pd.DataFrame] = {}
    for name, spec in dataset["tables"].items():
        tables[name] = pd.DataFrame(spec["rows"], columns=spec["columns"])
    return tables


def matched_expr(row: pd.Series) -> float:
    mapping = {"NDHB": "expr_ndhb", "NDHK": "expr_ndhk", "PGR5": "expr_pgr5"}
    gene_symbol = row.get("gene_symbol")
    if pd.isna(gene_symbol) or gene_symbol not in mapping:
        return np.nan
    return row[mapping[gene_symbol]]


def finalize(df: pd.DataFrame, cols: List[str]) -> dict:
    out = df.loc[:, cols].copy()
    rows: List[list] = []
    for row in out.itertuples(index=False, name=None):
        cooked = []
        for value in row:
            if pd.isna(value):
                cooked.append(None)
            elif isinstance(value, (np.integer, int)):
                cooked.append(int(value))
            elif isinstance(value, (np.floating, float)):
                rounded = round(float(value), 3)
                if abs(rounded - round(rounded)) < 1e-12:
                    cooked.append(int(round(rounded)))
                else:
                    cooked.append(rounded)
            else:
                cooked.append(value)
        rows.append(cooked)
    return {"columns": cols, "rows": rows}


def derive_answers(dataset: dict) -> Dict[str, dict]:
    t = tables_from_dataset(dataset)
    f = t["fact_calls"]
    s = t["sample_dim"]
    v = t["variant_dim"]
    g = t["gene_dim"]

    inner_fs = f.merge(s, on="sample_id", how="inner")
    inner_fv = f.merge(v, on="variant_id", how="inner")
    inner_fvg = inner_fv.merge(g, on="gene_id", how="inner")

    complete = (
        f.merge(s, on="sample_id", how="inner")
        .merge(v, on="variant_id", how="inner")
        .merge(g, on="gene_id", how="inner")
        .copy()
    )
    complete["vaf"] = complete["alt_reads"] / complete["total_reads"]
    complete["matched_expr_count"] = complete.apply(matched_expr, axis=1)
    complete["log2_matched_expr"] = np.log2(complete["matched_expr_count"] + 1)

    left_full = (
        f.merge(s, on="sample_id", how="left")
        .merge(v, on="variant_id", how="left")
        .merge(g, on="gene_id", how="left")
    )

    answers: Dict[str, dict] = {}

    # PASS 1
    answers["pass1.query1"] = finalize(
        inner_fs.sort_values("call_id"),
        ["call_id", "sample_id", "tissue", "condition", "genotype"],
    )
    answers["pass1.query2"] = finalize(
        inner_fv.sort_values(["qual", "call_id"], ascending=[False, True]),
        ["call_id", "variant_id", "variant_class", "impact", "qual"],
    )
    answers["pass1.query3"] = finalize(
        f.merge(s, on="sample_id", how="left").sort_values("call_id"),
        ["call_id", "sample_id", "tissue", "batch", "expr_ndhb"],
    )
    answers["pass1.query4"] = finalize(
        s.merge(f, on="sample_id", how="left")
        .groupby(["sample_id", "tissue"], as_index=False)
        .agg(
            call_count=("call_id", lambda x: x.notna().sum()),
            avg_qual=("qual", "mean"),
        )
        .sort_values("sample_id"),
        ["sample_id", "tissue", "call_count", "avg_qual"],
    )
    answers["pass1.query5"] = finalize(
        inner_fvg.sort_values("call_id"),
        ["call_id", "variant_id", "gene_symbol", "pathway"],
    )
    answers["pass1.query6"] = finalize(
        inner_fv.groupby("impact", as_index=False)
        .agg(call_count=("call_id", "size"), avg_qual=("qual", "mean"))
        .sort_values(["call_count", "impact"], ascending=[False, True]),
        ["impact", "call_count", "avg_qual"],
    )
    answers["pass1.query7"] = finalize(
        inner_fs.groupby("tissue", as_index=False)
        .agg(avg_qual=("qual", "mean"), min_qual=("qual", "min"), max_qual=("qual", "max"))
        .sort_values("avg_qual", ascending=False),
        ["tissue", "avg_qual", "min_qual", "max_qual"],
    )
    answers["pass1.query8"] = finalize(
        inner_fs.groupby("condition", as_index=False)
        .agg(call_count=("call_id", "size"), avg_expr_pgr5=("expr_pgr5", "mean"))
        .sort_values("condition"),
        ["condition", "call_count", "avg_expr_pgr5"],
    )

    # PASS 2
    answers["pass2.query1"] = finalize(
        complete.sort_values("call_id"),
        ["call_id", "sample_id", "tissue", "gene_symbol", "impact", "genotype"],
    )
    answers["pass2.query2"] = finalize(
        left_full.sort_values("call_id"),
        ["call_id", "sample_id", "plant_line_id", "tissue", "variant_id", "gene_symbol"],
    )
    answers["pass2.query3"] = finalize(
        f.merge(v[["variant_id", "impact"]], on="variant_id", how="outer")
        .sort_values(["variant_id", "call_id"], na_position="last"),
        ["variant_id", "call_id", "sample_id", "impact"],
    )
    answers["pass2.query4"] = finalize(
        inner_fs.merge(v[["variant_id", "impact"]], on="variant_id")
        .groupby(["condition", "impact"], as_index=False)
        .agg(call_count=("call_id", "size"), avg_qual=("qual", "mean"))
        .sort_values(["condition", "impact"]),
        ["condition", "impact", "call_count", "avg_qual"],
    )
    tmp = inner_fvg.copy()
    tmp["vaf"] = tmp["alt_reads"] / tmp["total_reads"]
    answers["pass2.query5"] = finalize(
        tmp.groupby("gene_symbol", as_index=False)
        .agg(avg_vaf=("vaf", "mean"), max_qual=("qual", "max"))
        .sort_values(["avg_vaf", "gene_symbol"], ascending=[False, True]),
        ["gene_symbol", "avg_vaf", "max_qual"],
    )
    answers["pass2.query6"] = finalize(
        complete.groupby("tissue", as_index=False)
        .agg(distinct_genes=("gene_symbol", "nunique"), avg_expr_ndhb=("expr_ndhb", "mean"))
        .sort_values("tissue"),
        ["tissue", "distinct_genes", "avg_expr_ndhb"],
    )
    tmp = s.merge(
        f.merge(v[["variant_id", "impact"]], on="variant_id", how="left").query("impact == 'high'"),
        on="sample_id",
        how="left",
    )
    answers["pass2.query7"] = finalize(
        tmp.groupby(["sample_id", "tissue"], as_index=False)
        .agg(
            high_impact_call_count=("call_id", lambda x: x.notna().sum()),
            avg_alt_reads_high=("alt_reads", "mean"),
        )
        .sort_values(["high_impact_call_count", "sample_id"], ascending=[False, True]),
        ["sample_id", "tissue", "high_impact_call_count", "avg_alt_reads_high"],
    )
    answers["pass2.query8"] = finalize(
        inner_fvg.groupby("gene_symbol", as_index=False)
        .agg(
            total_alt_reads=("alt_reads", "sum"),
            avg_qual=("qual", "mean"),
            max_alt_reads=("alt_reads", "max"),
        )
        .sort_values(["total_alt_reads", "gene_symbol"], ascending=[False, True]),
        ["gene_symbol", "total_alt_reads", "avg_qual", "max_alt_reads"],
    )

    # PASS 3
    def classify_join_status(row: pd.Series) -> str:
        if pd.isna(row["impact"]):
            return "MISSING_VARIANT"
        if pd.isna(row["gene_symbol"]):
            return "MISSING_GENE"
        if pd.isna(row["plant_line_id"]):
            return "MISSING_SAMPLE"
        return "COMPLETE_CHAIN"

    tmp = left_full.copy()
    tmp["join_status"] = tmp.apply(classify_join_status, axis=1)
    answers["pass3.query1"] = finalize(
        tmp.sort_values("call_id"),
        ["call_id", "sample_id", "variant_id", "join_status"],
    )
    answers["pass3.query2"] = finalize(
        complete.groupby(["tissue", "gene_symbol"], as_index=False)
        .agg(
            call_count=("call_id", "size"),
            sum_alt_reads=("alt_reads", "sum"),
            avg_vaf=("vaf", "mean"),
            max_qual=("qual", "max"),
        )
        .sort_values(["tissue", "gene_symbol"]),
        ["tissue", "gene_symbol", "call_count", "sum_alt_reads", "avg_vaf", "max_qual"],
    )
    tmp = g.merge(v, on="gene_id", how="left").merge(
        f[["variant_id", "alt_reads", "call_id"]], on="variant_id", how="left"
    )
    answers["pass3.query3"] = finalize(
        tmp.groupby(["gene_symbol", "pathway"], as_index=False)
        .agg(
            observed_call_count=("call_id", lambda x: x.notna().sum()),
            total_alt_reads=("alt_reads", "sum"),
        )
        .fillna({"total_alt_reads": 0})
        .sort_values(["observed_call_count", "gene_symbol"], ascending=[False, True]),
        ["gene_symbol", "pathway", "observed_call_count", "total_alt_reads"],
    )
    tmp = inner_fs.merge(v[["variant_id", "impact"]], on="variant_id")
    answers["pass3.query4"] = finalize(
        tmp[tmp["impact"] == "high"]
        .groupby("condition", as_index=False)
        .agg(
            high_impact_call_count=("call_id", "size"),
            avg_qual=("qual", "mean"),
            avg_alt_reads=("alt_reads", "mean"),
        )
        .sort_values("condition"),
        ["condition", "high_impact_call_count", "avg_qual", "avg_alt_reads"],
    )
    tmp = s.merge(f, on="sample_id", how="left")
    tmp["heterozygous_calls"] = (tmp["genotype"] == "0/1").astype(int)
    tmp["homozygous_alt_calls"] = (tmp["genotype"] == "1/1").astype(int)
    tmp["mean_nonref_qual"] = tmp["qual"].where(tmp["genotype"].isin(["0/1", "1/1"]))
    answers["pass3.query5"] = finalize(
        tmp.groupby("sample_id", as_index=False)
        .agg(
            heterozygous_calls=("heterozygous_calls", "sum"),
            homozygous_alt_calls=("homozygous_alt_calls", "sum"),
            mean_nonref_qual=("mean_nonref_qual", "mean"),
        )
        .sort_values("sample_id"),
        ["sample_id", "heterozygous_calls", "homozygous_alt_calls", "mean_nonref_qual"],
    )
    tmp = complete.groupby(["tissue", "gene_symbol"], as_index=False).agg(
        total_alt_reads=("alt_reads", "sum"),
        avg_vaf=("vaf", "mean"),
    )
    tmp["rank_in_tissue"] = (
        tmp.groupby("tissue")["total_alt_reads"].rank(method="dense", ascending=False).astype(int)
    )
    answers["pass3.query6"] = finalize(
        tmp.sort_values(["tissue", "rank_in_tissue", "gene_symbol"]),
        ["tissue", "gene_symbol", "total_alt_reads", "avg_vaf", "rank_in_tissue"],
    )
    rows = []
    for sample_id in sorted(set(s.loc[~s["sample_id"].isin(f["sample_id"]), "sample_id"])):
        rows.append(["sample", sample_id, "no_fact_calls"])
    for variant_id in sorted(set(v.loc[~v["variant_id"].isin(f["variant_id"]), "variant_id"])):
        rows.append(["variant", variant_id, "no_fact_calls"])
    for gene_id in g["gene_id"]:
        vids = list(v.loc[v["gene_id"] == gene_id, "variant_id"])
        if not vids:
            rows.append(["gene", gene_id, "no_variants_attached"])
        elif not any(vid in set(f["variant_id"]) for vid in vids):
            rows.append(["gene", gene_id, "no_fact_calls_through_variants"])
    answers["pass3.query7"] = finalize(
        pd.DataFrame(rows, columns=["object_type", "object_id", "reason"]).sort_values(
            ["object_type", "object_id"]
        ),
        ["object_type", "object_id", "reason"],
    )
    answers["pass3.query8"] = finalize(
        complete[complete["genotype"] != "0/0"]
        .groupby(["condition", "gene_role"], as_index=False)
        .agg(non_reference_call_count=("call_id", "size"), mean_vaf=("vaf", "mean"))
        .sort_values(["condition", "gene_role"]),
        ["condition", "gene_role", "non_reference_call_count", "mean_vaf"],
    )

    # PASS 4
    variants_with_gene = set(v.merge(g, on="gene_id", how="inner")["variant_id"])
    metrics = [
        ["fact_rows_total", len(f)],
        ["complete_chain_rows", len(complete)],
        ["fact_rows_missing_sample", int(((~f["sample_id"].isin(s["sample_id"])) & (f["variant_id"].isin(variants_with_gene))).sum())],
        ["fact_rows_missing_variant", int((~f["variant_id"].isin(v["variant_id"])).sum())],
        ["fact_rows_missing_gene", int(((f["variant_id"].isin(v["variant_id"])) & (~f["variant_id"].isin(variants_with_gene))).sum())],
        ["unused_samples", int((~s["sample_id"].isin(f["sample_id"])).sum())],
        ["unused_variants", int((~v["variant_id"].isin(f["variant_id"])).sum())],
        ["genes_with_no_variants", int((~g["gene_id"].isin(v["gene_id"])).sum())],
    ]
    answers["pass4.query1"] = finalize(pd.DataFrame(metrics, columns=["metric", "value"]), ["metric", "value"])
    answers["pass4.query2"] = finalize(
        complete.groupby(["condition", "pathway"], as_index=False)
        .agg(
            call_count=("call_id", "size"),
            total_alt_reads=("alt_reads", "sum"),
            mean_qual=("qual", "mean"),
            avg_expr_ndhb=("expr_ndhb", "mean"),
        )
        .sort_values(["condition", "total_alt_reads", "pathway"], ascending=[True, False, True]),
        ["condition", "pathway", "call_count", "total_alt_reads", "mean_qual", "avg_expr_ndhb"],
    )
    answers["pass4.query3"] = finalize(
        complete[complete["genotype"] != "0/0"]
        .groupby(["batch", "gene_role"], as_index=False)
        .agg(
            non_reference_calls=("call_id", "size"),
            avg_qual=("qual", "mean"),
            max_vaf=("vaf", "max"),
            mean_expr_pgr5=("expr_pgr5", "mean"),
        )
        .sort_values(["batch", "gene_role"]),
        ["batch", "gene_role", "non_reference_calls", "avg_qual", "max_vaf", "mean_expr_pgr5"],
    )
    tmp = complete.groupby("gene_symbol", as_index=False).agg(
        control_calls=("condition", lambda x: int((x == "control").sum())),
        non_control_calls=("condition", lambda x: int((x != "control").sum())),
        total_alt_reads=("alt_reads", "sum"),
    )
    answers["pass4.query4"] = finalize(
        tmp[(tmp["control_calls"] > 0) & (tmp["non_control_calls"] > 0)].sort_values(
            ["total_alt_reads", "gene_symbol"], ascending=[False, True]
        ),
        ["gene_symbol", "control_calls", "non_control_calls", "total_alt_reads"],
    )
    tmp = (
        g.merge(v, on="gene_id", how="left")
        .merge(f[["variant_id", "sample_id", "call_id"]], on="variant_id", how="left")
        .merge(s, on="sample_id", how="left")
    )
    tmp["matched_expr"] = tmp.apply(matched_expr, axis=1)
    tmp["matched_sample_id"] = tmp["sample_id"].where(tmp["plant_line_id"].notna())
    answers["pass4.query5"] = finalize(
        tmp.groupby("gene_symbol", as_index=False)
        .agg(
            variant_count=("variant_id", lambda x: x.dropna().nunique()),
            call_count=("call_id", lambda x: x.notna().sum()),
            distinct_matched_sample_count=("matched_sample_id", lambda x: x.dropna().nunique()),
            distinct_tissue_count=("tissue", lambda x: x.dropna().nunique()),
            avg_matched_expression=("matched_expr", "mean"),
        )
        .sort_values("gene_symbol"),
        [
            "gene_symbol",
            "variant_count",
            "call_count",
            "distinct_matched_sample_count",
            "distinct_tissue_count",
            "avg_matched_expression",
        ],
    )
    burden = (
        complete[(complete["genotype"] != "0/0") & (complete["impact"].isin(["high", "moderate"]))]
        .groupby("sample_id", as_index=False)
        .agg(burden_genes=("gene_symbol", "nunique"))
    )
    tmp = s.copy()
    tmp["mean_log2_marker_expr"] = tmp.apply(
        lambda r: np.mean(
            [np.log2(r["expr_ndhb"] + 1), np.log2(r["expr_pgr5"] + 1), np.log2(r["expr_ndhk"] + 1)]
        ),
        axis=1,
    )
    tmp = tmp.merge(burden, on="sample_id", how="left").fillna({"burden_genes": 0})
    tmp["burden_genes"] = tmp["burden_genes"].astype(int)
    answers["pass4.query6"] = finalize(
        tmp.sort_values(["burden_genes", "sample_id"], ascending=[False, True]),
        ["sample_id", "tissue", "burden_genes", "mean_log2_marker_expr"],
    )
    rows = []
    for x in sorted(set(f.loc[~f["sample_id"].isin(s["sample_id"]), "sample_id"])):
        rows.append(["fact_calls.sample_id", x, "missing_in_sample_dim"])
    for x in sorted(set(f.loc[~f["variant_id"].isin(v["variant_id"]), "variant_id"])):
        rows.append(["fact_calls.variant_id", x, "missing_in_variant_dim"])
    for x in sorted(set(g.loc[~g["gene_id"].isin(v["gene_id"]), "gene_id"])):
        rows.append(["gene_dim.gene_id", x, "no_variants_attached"])
    for x in sorted(set(s.loc[~s["sample_id"].isin(f["sample_id"]), "sample_id"])):
        rows.append(["sample_dim.sample_id", x, "unused_dimension_row"])
    for x in sorted(set(v.loc[~v["gene_id"].isin(g["gene_id"]), "gene_id"])):
        rows.append(["variant_dim.gene_id", x, "missing_in_gene_dim"])
    for x in sorted(set(v.loc[~v["variant_id"].isin(f["variant_id"]), "variant_id"])):
        rows.append(["variant_dim.variant_id", x, "unused_dimension_row"])
    answers["pass4.query7"] = finalize(
        pd.DataFrame(rows, columns=["source_table", "key_value", "orphan_type"]).sort_values(
            ["source_table", "key_value"]
        ),
        ["source_table", "key_value", "orphan_type"],
    )
    answers["pass4.query8"] = finalize(
        complete[complete["genotype"] != "0/0"].sort_values(
            ["condition", "tissue", "gene_symbol", "variant_id", "call_id"]
        ),
        [
            "call_id",
            "plant_line_id",
            "tissue",
            "condition",
            "gene_symbol",
            "pathway",
            "variant_id",
            "impact",
            "genotype",
            "alt_reads",
            "total_reads",
            "vaf",
            "matched_expr_count",
            "log2_matched_expr",
            "qual",
        ],
    )

    # PASS 5
    tmp = s.copy()
    tmp["log2_expr_ndhb"] = np.log2(tmp["expr_ndhb"] + 1)
    tmp["log2_expr_pgr5"] = np.log2(tmp["expr_pgr5"] + 1)
    tmp["log2_expr_ndhk"] = np.log2(tmp["expr_ndhk"] + 1)
    tmp["ndh_module_ratio"] = (tmp["expr_ndhb"] + tmp["expr_ndhk"]) / (
        tmp["expr_ndhb"] + tmp["expr_pgr5"] + tmp["expr_ndhk"]
    )
    answers["pass5.query1"] = finalize(
        tmp.sort_values("sample_id"),
        ["sample_id", "tissue", "log2_expr_ndhb", "log2_expr_pgr5", "log2_expr_ndhk", "ndh_module_ratio"],
    )
    tmp = complete.copy()
    tmp["expr_weighted_vaf"] = tmp["vaf"] * tmp["log2_matched_expr"]
    answers["pass5.query2"] = finalize(
        tmp.sort_values("call_id"),
        ["call_id", "gene_symbol", "matched_expr_count", "log2_matched_expr", "vaf", "expr_weighted_vaf"],
    )
    answers["pass5.query3"] = finalize(
        complete.groupby(["condition", "gene_symbol"], as_index=False)
        .agg(
            n_calls=("call_id", "size"),
            mean_matched_expr=("matched_expr_count", "mean"),
            median_matched_expr=("matched_expr_count", "median"),
            pop_std_matched_expr=("matched_expr_count", lambda x: float(np.std(x, ddof=0))),
        )
        .sort_values(["condition", "gene_symbol"]),
        ["condition", "gene_symbol", "n_calls", "mean_matched_expr", "median_matched_expr", "pop_std_matched_expr"],
    )
    stress = s.copy()
    stress["stress_group"] = np.where(stress["condition"].isin(["high_light", "drought"]), "stress", "control")
    rows = []
    for gene_symbol, col in [("NDHB", "expr_ndhb"), ("NDHK", "expr_ndhk"), ("PGR5", "expr_pgr5")]:
        log_expr = np.log2(stress[col] + 1)
        stress_mean = log_expr[stress["stress_group"] == "stress"].mean()
        control_mean = log_expr[stress["stress_group"] == "control"].mean()
        rows.append([gene_symbol, stress_mean, control_mean, stress_mean - control_mean])
    answers["pass5.query4"] = finalize(
        pd.DataFrame(
            rows,
            columns=[
                "gene_symbol",
                "stress_mean_log2",
                "control_mean_log2",
                "delta_log2_stress_minus_control",
            ],
        ).sort_values("gene_symbol"),
        ["gene_symbol", "stress_mean_log2", "control_mean_log2", "delta_log2_stress_minus_control"],
    )
    tmp = complete[complete["genotype"] != "0/0"].copy()
    tmp["burden_score"] = tmp["vaf"] * tmp["log2_matched_expr"]
    answers["pass5.query5"] = finalize(
        tmp.groupby(["pathway", "tissue"], as_index=False)
        .agg(
            non_reference_calls=("call_id", "size"),
            mean_vaf=("vaf", "mean"),
            mean_log2_matched_expr=("log2_matched_expr", "mean"),
            burden_score=("burden_score", "sum"),
        )
        .sort_values(["pathway", "tissue"]),
        ["pathway", "tissue", "non_reference_calls", "mean_vaf", "mean_log2_matched_expr", "burden_score"],
    )
    tmp = s.copy()
    for col, z in [("expr_ndhb", "z_ndhb"), ("expr_pgr5", "z_pgr5"), ("expr_ndhk", "z_ndhk")]:
        tmp[z] = (tmp[col] - tmp[col].mean()) / tmp[col].std(ddof=0)
    tmp["photosynthesis_expr_z_mean"] = tmp[["z_ndhb", "z_pgr5", "z_ndhk"]].mean(axis=1)
    answers["pass5.query6"] = finalize(
        tmp.sort_values(["photosynthesis_expr_z_mean", "sample_id"], ascending=[False, True]),
        ["sample_id", "z_ndhb", "z_pgr5", "z_ndhk", "photosynthesis_expr_z_mean"],
    )
    answers["pass5.query7"] = finalize(
        complete.groupby("condition", as_index=False)
        .agg(
            distinct_genes_observed=("gene_symbol", "nunique"),
            mean_matched_expr=("matched_expr_count", "mean"),
            cv_matched_expr=("matched_expr_count", lambda x: float(np.std(x, ddof=0)) / float(np.mean(x))),
            mean_vaf=("vaf", "mean"),
        )
        .sort_values("condition"),
        ["condition", "distinct_genes_observed", "mean_matched_expr", "cv_matched_expr", "mean_vaf"],
    )
    agg = (
        complete[complete["genotype"] != "0/0"]
        .groupby("sample_id", as_index=False)
        .agg(
            non_reference_complete_chain_calls=("call_id", "size"),
            high_or_moderate_nonref_calls=("impact", lambda x: int(x.isin(["high", "moderate"]).sum())),
        )
    )
    tmp = s.copy()
    tmp["total_marker_expr"] = tmp["expr_ndhb"] + tmp["expr_pgr5"] + tmp["expr_ndhk"]
    tmp["log2_total_marker_expr"] = np.log2(tmp["total_marker_expr"] + 1)
    tmp = tmp.merge(agg, on="sample_id", how="left").fillna(
        {"non_reference_complete_chain_calls": 0, "high_or_moderate_nonref_calls": 0}
    )
    tmp["non_reference_complete_chain_calls"] = tmp["non_reference_complete_chain_calls"].astype(int)
    tmp["high_or_moderate_nonref_calls"] = tmp["high_or_moderate_nonref_calls"].astype(int)
    tmp["photosynthesis_variant_pressure"] = (
        tmp["high_or_moderate_nonref_calls"] * tmp["log2_total_marker_expr"]
    )
    answers["pass5.query8"] = finalize(
        tmp.sort_values(["photosynthesis_variant_pressure", "sample_id"], ascending=[False, True]),
        [
            "sample_id",
            "tissue",
            "non_reference_complete_chain_calls",
            "high_or_moderate_nonref_calls",
            "total_marker_expr",
            "log2_total_marker_expr",
            "photosynthesis_variant_pressure",
        ],
    )

    return answers


def check_against_gold(base: Path, answers: Dict[str, dict]) -> None:
    gold_rows = {obj["case_id"]: obj for obj in load_jsonl(base / "gold_answers.jsonl")}
    mismatches = []
    for case_id in sorted(answers):
        calc = answers[case_id]
        gold = gold_rows[case_id]
        if calc["columns"] != gold["columns"] or calc["rows"] != gold["rows"]:
            mismatches.append(case_id)
    if mismatches:
        raise SystemExit(f"Gold mismatch in {len(mismatches)} cases: {', '.join(mismatches[:5])}")
    print(f"All {len(answers)} derived answers match gold_answers.jsonl")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, default=Path("."), help="Repo root or benchmark folder")
    ap.add_argument("--output", type=Path, default=None, help="Write derived answers JSONL here")
    ap.add_argument("--check", action="store_true", help="Validate derived answers against gold_answers.jsonl")
    args = ap.parse_args()

    base = resolve_base(args.base)
    dataset = load_json(base / "shared_dataset.json")
    answers = derive_answers(dataset)

    if args.output:
        with args.output.open("w", encoding="utf-8") as f:
            for case_id in sorted(answers):
                row = {
                    "benchmark_id": dataset["benchmark_id"],
                    "case_id": case_id,
                    "columns": answers[case_id]["columns"],
                    "rows": answers[case_id]["rows"],
                    "row_order_matters": True,
                    "column_order_matters": True,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Wrote {len(answers)} derived answers to {args.output}")

    if args.check:
        check_against_gold(base, answers)


if __name__ == "__main__":
    main()
