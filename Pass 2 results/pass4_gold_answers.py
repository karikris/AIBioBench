#!/usr/bin/env python3
from pathlib import Path

import numpy as np
import pandas as pd


def resolve_csv_dir() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here,
        here / "aibiobench_sql_pack",
        here.parent,
        here.parent / "aibiobench_sql_pack",
        Path.cwd(),
        Path.cwd() / "aibiobench_sql_pack",
    ]
    needed = {"fact_calls.csv", "sample_dim.csv", "variant_dim.csv", "gene_dim.csv"}
    for cand in candidates:
        if all((cand / name).exists() for name in needed):
            return cand
    raise FileNotFoundError(
        "Could not find fact_calls.csv, sample_dim.csv, variant_dim.csv, and gene_dim.csv "
        "in the script directory, current working directory, or an aibiobench_sql_pack subdirectory."
    )


def load_tables(csv_dir: Path):
    fact_calls = pd.read_csv(csv_dir / "fact_calls.csv")
    sample_dim = pd.read_csv(csv_dir / "sample_dim.csv")
    variant_dim = pd.read_csv(csv_dir / "variant_dim.csv")
    gene_dim = pd.read_csv(csv_dir / "gene_dim.csv")
    return fact_calls, sample_dim, variant_dim, gene_dim


def matched_expr(row: pd.Series):
    mapping = {"NDHB": "expr_ndhb", "NDHK": "expr_ndhk", "PGR5": "expr_pgr5"}
    gene_symbol = row.get("gene_symbol")
    if pd.isna(gene_symbol) or gene_symbol not in mapping:
        return np.nan
    return row[mapping[gene_symbol]]


def complete_chain(fact_calls: pd.DataFrame, sample_dim: pd.DataFrame, variant_dim: pd.DataFrame, gene_dim: pd.DataFrame) -> pd.DataFrame:
    df = (
        fact_calls.merge(sample_dim, on="sample_id", how="inner")
        .merge(variant_dim, on="variant_id", how="inner")
        .merge(gene_dim, on="gene_id", how="inner")
        .copy()
    )
    df["vaf"] = df["alt_reads"] / df["total_reads"]
    df["matched_expr_count"] = df.apply(matched_expr, axis=1)
    df["log2_matched_expr"] = np.log2(df["matched_expr_count"] + 1)
    return df


def finalize(df: pd.DataFrame, columns):
    out = df.loc[:, columns].copy()
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].round(3)
    return out


def printable(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    return out.where(pd.notna(out), "NULL")


def show(name: str, df: pd.DataFrame):
    print(f"\n{name}")
    print(printable(df).to_string(index=False))


def main():
    csv_dir = resolve_csv_dir()
    fact_calls, sample_dim, variant_dim, gene_dim = load_tables(csv_dir)

    complete = complete_chain(fact_calls, sample_dim, variant_dim, gene_dim)

    # pass4.query1
    metrics = [
        ["fact_rows_total", int(len(fact_calls))],
        ["complete_chain_rows", int(len(complete))],
        ["fact_rows_missing_sample", int((~fact_calls["sample_id"].isin(sample_dim["sample_id"])).sum())],
        ["fact_rows_missing_variant", int((~fact_calls["variant_id"].isin(variant_dim["variant_id"])).sum())],
        [
            "fact_rows_missing_gene",
            int(
                fact_calls["variant_id"]
                .isin(variant_dim.loc[~variant_dim["gene_id"].isin(gene_dim["gene_id"]), "variant_id"])
                .sum()
            ),
        ],
        ["unused_samples", int((~sample_dim["sample_id"].isin(fact_calls["sample_id"])).sum())],
        ["unused_variants", int((~variant_dim["variant_id"].isin(fact_calls["variant_id"])).sum())],
        ["genes_with_no_variants", int((~gene_dim["gene_id"].isin(variant_dim["gene_id"])).sum())],
    ]
    pass4_query1 = finalize(pd.DataFrame(metrics, columns=["metric", "value"]), ["metric", "value"])

    # pass4.query2
    pass4_query2 = finalize(
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

    # pass4.query3
    pass4_query3 = finalize(
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

    # pass4.query4
    tmp = complete.groupby("gene_symbol", as_index=False).agg(
        control_calls=("condition", lambda x: int((x == "control").sum())),
        non_control_calls=("condition", lambda x: int((x != "control").sum())),
        total_alt_reads=("alt_reads", "sum"),
    )
    pass4_query4 = finalize(
        tmp[(tmp["control_calls"] > 0) & (tmp["non_control_calls"] > 0)]
        .sort_values(["total_alt_reads", "gene_symbol"], ascending=[False, True]),
        ["gene_symbol", "control_calls", "non_control_calls", "total_alt_reads"],
    )

    # pass4.query5
    tmp = (
        gene_dim.merge(variant_dim, on="gene_id", how="left")
        .merge(fact_calls[["variant_id", "sample_id", "call_id"]], on="variant_id", how="left")
        .merge(sample_dim, on="sample_id", how="left")
    )
    tmp["matched_expr"] = tmp.apply(matched_expr, axis=1)
    tmp["matched_sample_id"] = tmp["sample_id"].where(tmp["plant_line_id"].notna())
    pass4_query5 = finalize(
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

    # pass4.query6
    burden = (
        complete[(complete["genotype"] != "0/0") & (complete["impact"].isin(["high", "moderate"]))]
        .groupby("sample_id", as_index=False)
        .agg(burden_genes=("gene_symbol", "nunique"))
    )
    tmp = sample_dim.copy()
    tmp["mean_log2_marker_expr"] = tmp.apply(
        lambda r: np.mean(
            [np.log2(r["expr_ndhb"] + 1), np.log2(r["expr_pgr5"] + 1), np.log2(r["expr_ndhk"] + 1)]
        ),
        axis=1,
    )
    tmp = tmp.merge(burden, on="sample_id", how="left").fillna({"burden_genes": 0})
    tmp["burden_genes"] = tmp["burden_genes"].astype(int)
    pass4_query6 = finalize(
        tmp.sort_values(["burden_genes", "sample_id"], ascending=[False, True]),
        ["sample_id", "tissue", "burden_genes", "mean_log2_marker_expr"],
    )

    # pass4.query7
    rows = []
    for x in sorted(set(fact_calls.loc[~fact_calls["sample_id"].isin(sample_dim["sample_id"]), "sample_id"])):
        rows.append(["fact_calls.sample_id", x, "missing_in_sample_dim"])
    for x in sorted(set(fact_calls.loc[~fact_calls["variant_id"].isin(variant_dim["variant_id"]), "variant_id"])):
        rows.append(["fact_calls.variant_id", x, "missing_in_variant_dim"])
    for x in sorted(set(gene_dim.loc[~gene_dim["gene_id"].isin(variant_dim["gene_id"]), "gene_id"])):
        rows.append(["gene_dim.gene_id", x, "no_variants_attached"])
    for x in sorted(set(sample_dim.loc[~sample_dim["sample_id"].isin(fact_calls["sample_id"]), "sample_id"])):
        rows.append(["sample_dim.sample_id", x, "unused_dimension_row"])
    for x in sorted(set(variant_dim.loc[~variant_dim["gene_id"].isin(gene_dim["gene_id"]), "gene_id"])):
        rows.append(["variant_dim.gene_id", x, "missing_in_gene_dim"])
    for x in sorted(set(variant_dim.loc[~variant_dim["variant_id"].isin(fact_calls["variant_id"]), "variant_id"])):
        rows.append(["variant_dim.variant_id", x, "unused_dimension_row"])
    pass4_query7 = finalize(
        pd.DataFrame(rows, columns=["source_table", "key_value", "orphan_type"]).sort_values(
            ["source_table", "key_value"]
        ),
        ["source_table", "key_value", "orphan_type"],
    )

    # pass4.query8
    pass4_query8 = finalize(
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

    results = {
        "pass4.query1": pass4_query1,
        "pass4.query2": pass4_query2,
        "pass4.query3": pass4_query3,
        "pass4.query4": pass4_query4,
        "pass4.query5": pass4_query5,
        "pass4.query6": pass4_query6,
        "pass4.query7": pass4_query7,
        "pass4.query8": pass4_query8,
    }

    for name, df in results.items():
        show(name, df)


if __name__ == "__main__":
    main()
