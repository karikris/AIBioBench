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

    # pass5.query1
    tmp = sample_dim.copy()
    tmp["log2_expr_ndhb"] = np.log2(tmp["expr_ndhb"] + 1)
    tmp["log2_expr_pgr5"] = np.log2(tmp["expr_pgr5"] + 1)
    tmp["log2_expr_ndhk"] = np.log2(tmp["expr_ndhk"] + 1)
    tmp["ndh_module_ratio"] = (tmp["expr_ndhb"] + tmp["expr_ndhk"]) / (
        tmp["expr_ndhb"] + tmp["expr_pgr5"] + tmp["expr_ndhk"]
    )
    pass5_query1 = finalize(
        tmp.sort_values("sample_id"),
        ["sample_id", "tissue", "log2_expr_ndhb", "log2_expr_pgr5", "log2_expr_ndhk", "ndh_module_ratio"],
    )

    # pass5.query2
    tmp = complete.copy()
    tmp["expr_weighted_vaf"] = tmp["vaf"] * tmp["log2_matched_expr"]
    pass5_query2 = finalize(
        tmp.sort_values("call_id"),
        ["call_id", "gene_symbol", "matched_expr_count", "log2_matched_expr", "vaf", "expr_weighted_vaf"],
    )

    # pass5.query3
    pass5_query3 = finalize(
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

    # pass5.query4
    stress = sample_dim.copy()
    stress["stress_group"] = np.where(stress["condition"].isin(["high_light", "drought"]), "stress", "control")
    rows = []
    for gene_symbol, col in [("NDHB", "expr_ndhb"), ("NDHK", "expr_ndhk"), ("PGR5", "expr_pgr5")]:
        log_expr = np.log2(stress[col] + 1)
        stress_mean = log_expr[stress["stress_group"] == "stress"].mean()
        control_mean = log_expr[stress["stress_group"] == "control"].mean()
        rows.append([gene_symbol, stress_mean, control_mean, stress_mean - control_mean])
    pass5_query4 = finalize(
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

    # pass5.query5
    tmp = complete[complete["genotype"] != "0/0"].copy()
    tmp["burden_score"] = tmp["vaf"] * tmp["log2_matched_expr"]
    pass5_query5 = finalize(
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

    # pass5.query6
    tmp = sample_dim.copy()
    for col, z in [("expr_ndhb", "z_ndhb"), ("expr_pgr5", "z_pgr5"), ("expr_ndhk", "z_ndhk")]:
        tmp[z] = (tmp[col] - tmp[col].mean()) / tmp[col].std(ddof=0)
    tmp["photosynthesis_expr_z_mean"] = tmp[["z_ndhb", "z_pgr5", "z_ndhk"]].mean(axis=1)
    pass5_query6 = finalize(
        tmp.sort_values(["photosynthesis_expr_z_mean", "sample_id"], ascending=[False, True]),
        ["sample_id", "z_ndhb", "z_pgr5", "z_ndhk", "photosynthesis_expr_z_mean"],
    )

    # pass5.query7
    pass5_query7 = finalize(
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

    # pass5.query8
    agg = (
        complete[complete["genotype"] != "0/0"]
        .groupby("sample_id", as_index=False)
        .agg(
            non_reference_complete_chain_calls=("call_id", "size"),
            high_or_moderate_nonref_calls=("impact", lambda x: int(x.isin(["high", "moderate"]).sum())),
        )
    )
    tmp = sample_dim.copy()
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
    pass5_query8 = finalize(
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

    results = {
        "pass5.query1": pass5_query1,
        "pass5.query2": pass5_query2,
        "pass5.query3": pass5_query3,
        "pass5.query4": pass5_query4,
        "pass5.query5": pass5_query5,
        "pass5.query6": pass5_query6,
        "pass5.query7": pass5_query7,
        "pass5.query8": pass5_query8,
    }

    for name, df in results.items():
        show(name, df)


if __name__ == "__main__":
    main()
