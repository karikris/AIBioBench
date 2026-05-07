#!/usr/bin/env python3
"""Prepare v6 code-footer query snapshot.

v6 is an oracle-code control run: each case uses the original v2 prompt text and
adds only a footer containing reference SQL/Python code for producing the gold
answer. The footer intentionally leaks the solution algorithm and must not be
reported as a normal reasoning benchmark.
"""

from __future__ import annotations

import copy
import json
import math
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "query_engineering_registry" / "runs" / "v6"

V2_CASES_PATH = REPO_ROOT / "query_engineering_registry" / "runs" / "v2" / "benchmark_cases.jsonl"
V2_INSTRUCTIONS_PATH = REPO_ROOT / "query_engineering_registry" / "runs" / "v2" / "standard_instructions.json"
ROOT_MANIFEST_PATH = REPO_ROOT / "benchmark_manifest.json"
DATASET_PATH = REPO_ROOT / "shared_dataset.json"
GOLD_PATH = REPO_ROOT / "gold_answers.jsonl"

BENCHMARK_ID = "AIBioBench_photosynthesis_snowflake_v6_code_footer"
VERSION = "6.0.0-code-footer"
OUTPUT_VERSION_ID = "v6_code_footer"
FOOTER_PREFIX = "Produce the output using the following code:"


SQL_SOLUTIONS = {
    "pass1.query1": """
SELECT
  f.call_id,
  f.sample_id,
  s.tissue,
  s.condition,
  f.genotype
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
ORDER BY f.call_id ASC;
""",
    "pass1.query2": """
SELECT
  f.call_id,
  f.variant_id,
  v.variant_class,
  v.impact,
  f.qual
FROM fact_calls AS f
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
ORDER BY f.qual DESC, f.call_id ASC;
""",
    "pass1.query3": """
SELECT
  f.call_id,
  f.sample_id,
  s.tissue,
  s.batch,
  s.expr_ndhb
FROM fact_calls AS f
LEFT JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
ORDER BY f.call_id ASC;
""",
    "pass1.query4": """
SELECT
  s.sample_id,
  s.tissue,
  COUNT(f.call_id) AS call_count,
  ROUND(AVG(f.qual), 3) AS avg_qual
FROM sample_dim AS s
LEFT JOIN fact_calls AS f
  ON s.sample_id = f.sample_id
GROUP BY s.sample_id, s.tissue
ORDER BY s.sample_id ASC;
""",
    "pass1.query5": """
SELECT
  f.call_id,
  f.variant_id,
  g.gene_symbol,
  g.pathway
FROM fact_calls AS f
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
ORDER BY f.call_id ASC;
""",
    "pass1.query6": """
SELECT
  v.impact,
  COUNT(*) AS call_count,
  ROUND(AVG(f.qual), 3) AS avg_qual
FROM fact_calls AS f
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
GROUP BY v.impact
ORDER BY call_count DESC, v.impact ASC;
""",
    "pass1.query7": """
SELECT
  s.tissue,
  ROUND(AVG(f.qual), 3) AS avg_qual,
  MIN(f.qual) AS min_qual,
  MAX(f.qual) AS max_qual
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
GROUP BY s.tissue
ORDER BY avg_qual DESC;
""",
    "pass1.query8": """
SELECT
  s.condition,
  COUNT(*) AS call_count,
  ROUND(AVG(s.expr_pgr5), 3) AS avg_expr_pgr5
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
GROUP BY s.condition
ORDER BY s.condition ASC;
""",
    "pass1.query9": """
SELECT
  s.condition,
  COUNT(*) AS total_calls,
  ROUND(AVG(f.qual), 3) AS avg_qual,
  SUM(CASE WHEN v.impact = 'high' THEN 1 ELSE 0 END) AS high_impact_calls
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
GROUP BY s.condition
ORDER BY s.condition ASC;
""",
    "pass1.query10": """
SELECT
  f.call_id,
  f.variant_id,
  v.impact,
  CASE
    WHEN v.variant_id IS NOT NULL THEN 'MATCHED'
    ELSE 'MISSING_VARIANT'
  END AS variant_match_status
FROM fact_calls AS f
LEFT JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
ORDER BY f.call_id ASC;
""",
    "pass2.query1": """
SELECT
  f.call_id,
  f.sample_id,
  s.tissue,
  g.gene_symbol,
  v.impact,
  f.genotype
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
ORDER BY f.call_id ASC;
""",
    "pass2.query2": """
SELECT
  f.call_id,
  f.sample_id,
  s.plant_line_id,
  s.tissue,
  f.variant_id,
  g.gene_symbol
FROM fact_calls AS f
LEFT JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
LEFT JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
LEFT JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
ORDER BY f.call_id ASC;
""",
    "pass2.query3": """
SELECT
  COALESCE(f.variant_id, v.variant_id) AS variant_id,
  f.call_id,
  f.sample_id,
  v.impact
FROM fact_calls AS f
LEFT JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
UNION ALL
SELECT
  v.variant_id,
  NULL AS call_id,
  NULL AS sample_id,
  v.impact
FROM variant_dim AS v
LEFT JOIN fact_calls AS f
  ON f.variant_id = v.variant_id
WHERE f.variant_id IS NULL
ORDER BY variant_id ASC, call_id ASC;
""",
    "pass2.query4": """
SELECT
  s.condition,
  v.impact,
  COUNT(*) AS call_count,
  ROUND(AVG(f.qual), 3) AS avg_qual
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
GROUP BY s.condition, v.impact
ORDER BY s.condition ASC, v.impact ASC;
""",
    "pass2.query5": """
SELECT
  g.gene_symbol,
  ROUND(AVG(CAST(f.alt_reads AS REAL) / f.total_reads), 3) AS avg_vaf,
  MAX(f.qual) AS max_qual
FROM fact_calls AS f
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
GROUP BY g.gene_symbol
ORDER BY avg_vaf DESC, g.gene_symbol ASC;
""",
    "pass2.query6": """
SELECT
  s.tissue,
  COUNT(DISTINCT g.gene_symbol) AS distinct_genes,
  ROUND(AVG(s.expr_ndhb), 3) AS avg_expr_ndhb
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
GROUP BY s.tissue
ORDER BY s.tissue ASC;
""",
    "pass2.query7": """
SELECT
  s.sample_id,
  s.tissue,
  SUM(CASE WHEN v.impact = 'high' THEN 1 ELSE 0 END) AS high_impact_call_count,
  ROUND(AVG(CASE WHEN v.impact = 'high' THEN f.alt_reads END), 3) AS avg_alt_reads_high
FROM sample_dim AS s
LEFT JOIN fact_calls AS f
  ON s.sample_id = f.sample_id
LEFT JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
GROUP BY s.sample_id, s.tissue
ORDER BY high_impact_call_count DESC, s.sample_id ASC;
""",
    "pass2.query8": """
SELECT
  g.gene_symbol,
  SUM(f.alt_reads) AS total_alt_reads,
  ROUND(AVG(f.qual), 3) AS avg_qual,
  MAX(f.alt_reads) AS max_alt_reads
FROM fact_calls AS f
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
GROUP BY g.gene_symbol
ORDER BY total_alt_reads DESC, g.gene_symbol ASC;
""",
    "pass2.query9": """
SELECT
  s.condition,
  g.pathway,
  COUNT(*) AS call_count,
  ROUND(AVG(CAST(f.alt_reads AS REAL) / f.total_reads), 3) AS mean_vaf,
  COUNT(DISTINCT f.sample_id) AS distinct_samples
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
GROUP BY s.condition, g.pathway
ORDER BY s.condition ASC, g.pathway ASC;
""",
    "pass2.query10": """
SELECT
  s.sample_id,
  s.tissue,
  COUNT(f.call_id) AS total_fact_calls,
  SUM(CASE WHEN f.call_id IS NOT NULL AND v.variant_id IS NOT NULL AND g.gene_id IS NOT NULL THEN 1 ELSE 0 END) AS complete_chain_calls,
  SUM(CASE WHEN f.call_id IS NOT NULL AND NOT (v.variant_id IS NOT NULL AND g.gene_id IS NOT NULL) THEN 1 ELSE 0 END) AS incomplete_chain_calls
FROM sample_dim AS s
LEFT JOIN fact_calls AS f
  ON s.sample_id = f.sample_id
LEFT JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
LEFT JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
GROUP BY s.sample_id, s.tissue
ORDER BY s.sample_id ASC;
""",
    "pass3.query1": """
SELECT
  f.call_id,
  f.sample_id,
  f.variant_id,
  CASE
    WHEN v.variant_id IS NULL THEN 'MISSING_VARIANT'
    WHEN s.sample_id IS NULL THEN 'MISSING_SAMPLE'
    WHEN g.gene_id IS NULL THEN 'MISSING_GENE'
    ELSE 'COMPLETE_CHAIN'
  END AS join_status
FROM fact_calls AS f
LEFT JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
LEFT JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
LEFT JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
ORDER BY f.call_id ASC;
""",
    "pass3.query2": """
SELECT
  s.tissue,
  g.gene_symbol,
  COUNT(*) AS call_count,
  SUM(f.alt_reads) AS sum_alt_reads,
  ROUND(AVG(CAST(f.alt_reads AS REAL) / f.total_reads), 3) AS avg_vaf,
  MAX(f.qual) AS max_qual
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
GROUP BY s.tissue, g.gene_symbol
ORDER BY s.tissue ASC, g.gene_symbol ASC;
""",
    "pass3.query3": """
SELECT
  g.gene_symbol,
  g.pathway,
  COUNT(f.call_id) AS observed_call_count,
  COALESCE(SUM(f.alt_reads), 0) AS total_alt_reads
FROM gene_dim AS g
LEFT JOIN variant_dim AS v
  ON g.gene_id = v.gene_id
LEFT JOIN fact_calls AS f
  ON v.variant_id = f.variant_id
GROUP BY g.gene_symbol, g.pathway
ORDER BY observed_call_count DESC, g.gene_symbol ASC;
""",
    "pass3.query4": """
SELECT
  s.condition,
  COUNT(*) AS high_impact_call_count,
  ROUND(AVG(f.qual), 3) AS avg_qual,
  ROUND(AVG(f.alt_reads), 3) AS avg_alt_reads
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
WHERE v.impact = 'high'
GROUP BY s.condition
ORDER BY s.condition ASC;
""",
    "pass3.query5": """
SELECT
  s.sample_id,
  SUM(CASE WHEN f.genotype = '0/1' THEN 1 ELSE 0 END) AS heterozygous_calls,
  SUM(CASE WHEN f.genotype = '1/1' THEN 1 ELSE 0 END) AS homozygous_alt_calls,
  ROUND(AVG(CASE WHEN f.genotype IN ('0/1', '1/1') THEN f.qual END), 3) AS mean_nonref_qual
FROM sample_dim AS s
LEFT JOIN fact_calls AS f
  ON s.sample_id = f.sample_id
GROUP BY s.sample_id
ORDER BY s.sample_id ASC;
""",
    "pass3.query6": """
WITH grouped AS (
  SELECT
    s.tissue,
    g.gene_symbol,
    SUM(f.alt_reads) AS total_alt_reads,
    ROUND(AVG(CAST(f.alt_reads AS REAL) / f.total_reads), 3) AS avg_vaf
  FROM fact_calls AS f
  INNER JOIN sample_dim AS s
    ON f.sample_id = s.sample_id
  INNER JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
  INNER JOIN gene_dim AS g
    ON v.gene_id = g.gene_id
  GROUP BY s.tissue, g.gene_symbol
)
SELECT
  tissue,
  gene_symbol,
  total_alt_reads,
  avg_vaf,
  DENSE_RANK() OVER (PARTITION BY tissue ORDER BY total_alt_reads DESC) AS rank_in_tissue
FROM grouped
ORDER BY tissue ASC, rank_in_tissue ASC, gene_symbol ASC;
""",
    "pass3.query7": """
SELECT
  'gene' AS object_type,
  g.gene_id AS object_id,
  CASE
    WHEN COUNT(v.variant_id) = 0 THEN 'no_variants_attached'
    ELSE 'no_fact_calls_through_variants'
  END AS reason
FROM gene_dim AS g
LEFT JOIN variant_dim AS v
  ON g.gene_id = v.gene_id
LEFT JOIN fact_calls AS f
  ON v.variant_id = f.variant_id
GROUP BY g.gene_id
HAVING COUNT(f.call_id) = 0
UNION ALL
SELECT
  'sample' AS object_type,
  s.sample_id AS object_id,
  'no_fact_calls' AS reason
FROM sample_dim AS s
LEFT JOIN fact_calls AS f
  ON s.sample_id = f.sample_id
WHERE f.call_id IS NULL
UNION ALL
SELECT
  'variant' AS object_type,
  v.variant_id AS object_id,
  'no_fact_calls' AS reason
FROM variant_dim AS v
LEFT JOIN fact_calls AS f
  ON v.variant_id = f.variant_id
WHERE f.call_id IS NULL
ORDER BY object_type ASC, object_id ASC;
""",
    "pass3.query8": """
SELECT
  s.condition,
  g.gene_role,
  COUNT(*) AS non_reference_call_count,
  ROUND(AVG(CAST(f.alt_reads AS REAL) / f.total_reads), 3) AS mean_vaf
FROM fact_calls AS f
INNER JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
WHERE f.genotype <> '0/0'
GROUP BY s.condition, g.gene_role
ORDER BY s.condition ASC, g.gene_role ASC;
""",
    "pass3.query9": """
SELECT
  CASE WHEN s.sample_id IS NULL THEN 'UNMATCHED_SAMPLE' ELSE s.condition END AS condition_group,
  SUM(CASE WHEN s.sample_id IS NOT NULL AND v.variant_id IS NOT NULL AND g.gene_id IS NOT NULL THEN 1 ELSE 0 END) AS complete_chain_calls,
  SUM(CASE WHEN s.sample_id IS NULL AND v.variant_id IS NOT NULL AND g.gene_id IS NOT NULL THEN 1 ELSE 0 END) AS missing_sample_calls,
  SUM(CASE WHEN v.variant_id IS NULL THEN 1 ELSE 0 END) AS missing_variant_calls,
  SUM(CASE WHEN v.variant_id IS NOT NULL AND g.gene_id IS NULL THEN 1 ELSE 0 END) AS missing_gene_calls
FROM fact_calls AS f
LEFT JOIN sample_dim AS s
  ON f.sample_id = s.sample_id
LEFT JOIN variant_dim AS v
  ON f.variant_id = v.variant_id
LEFT JOIN gene_dim AS g
  ON v.gene_id = g.gene_id
GROUP BY condition_group
ORDER BY condition_group ASC;
""",
    "pass3.query10": """
WITH complete_nonref AS (
  SELECT
    g.gene_symbol,
    CAST(f.alt_reads AS REAL) / f.total_reads AS vaf,
    CASE
      WHEN g.gene_symbol = 'NDHB' THEN s.expr_ndhb
      WHEN g.gene_symbol = 'NDHK' THEN s.expr_ndhk
      WHEN g.gene_symbol = 'PGR5' THEN s.expr_pgr5
    END AS matched_expr
  FROM fact_calls AS f
  INNER JOIN sample_dim AS s
    ON f.sample_id = s.sample_id
  INNER JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
  INNER JOIN gene_dim AS g
    ON v.gene_id = g.gene_id
  WHERE f.genotype <> '0/0'
)
SELECT
  gene_symbol,
  COUNT(*) AS non_reference_calls,
  ROUND(AVG(vaf), 3) AS avg_vaf,
  ROUND(AVG(matched_expr), 3) AS avg_matched_expr,
  ROUND(AVG(vaf) * AVG(matched_expr), 3) AS decision_score
FROM complete_nonref
GROUP BY gene_symbol
ORDER BY decision_score DESC, gene_symbol ASC;
""",
}


PYTHON_SOLUTIONS = {
    "pass4.query1": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
fact_variant = fact_calls.merge(variant_dim, on="variant_id", how="inner")

metrics = [
    ["fact_rows_total", len(fact_calls)],
    ["complete_chain_rows", len(complete)],
    ["fact_rows_missing_sample", int((~fact_calls["sample_id"].isin(sample_dim["sample_id"])).sum())],
    ["fact_rows_missing_variant", int((~fact_calls["variant_id"].isin(variant_dim["variant_id"])).sum())],
    ["fact_rows_missing_gene", int((~fact_variant["gene_id"].isin(gene_dim["gene_id"])).sum())],
    ["unused_samples", int((~sample_dim["sample_id"].isin(fact_calls["sample_id"])).sum())],
    ["unused_variants", int((~variant_dim["variant_id"].isin(fact_calls["variant_id"])).sum())],
    ["genes_with_no_variants", int((~gene_dim["gene_id"].isin(variant_dim["gene_id"])).sum())],
]

result = pd.DataFrame(metrics, columns=["metric", "value"])
result = result[["metric", "value"]]
""",
    "pass4.query2": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)

result = (
    complete
    .groupby(["condition", "pathway"], as_index=False)
    .agg(
        call_count=("call_id", "size"),
        total_alt_reads=("alt_reads", "sum"),
        mean_qual=("qual", "mean"),
        avg_expr_ndhb=("expr_ndhb", "mean"),
    )
)
result["mean_qual"] = result["mean_qual"].round(3)
result["avg_expr_ndhb"] = result["avg_expr_ndhb"].round(3)
result = result.sort_values(["condition", "total_alt_reads", "pathway"], ascending=[True, False, True])
result = result[["condition", "pathway", "call_count", "total_alt_reads", "mean_qual", "avg_expr_ndhb"]]
""",
    "pass4.query3": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
nonref = complete[complete["genotype"] != "0/0"].copy()
nonref["vaf"] = nonref["alt_reads"] / nonref["total_reads"]

result = (
    nonref
    .groupby(["batch", "gene_role"], as_index=False)
    .agg(
        non_reference_calls=("call_id", "size"),
        avg_qual=("qual", "mean"),
        max_vaf=("vaf", "max"),
        mean_expr_pgr5=("expr_pgr5", "mean"),
    )
)
for col in ["avg_qual", "max_vaf", "mean_expr_pgr5"]:
    result[col] = result[col].round(3)
result = result.sort_values(["batch", "gene_role"])
result = result[["batch", "gene_role", "non_reference_calls", "avg_qual", "max_vaf", "mean_expr_pgr5"]]
""",
    "pass4.query4": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
grouped = (
    complete
    .groupby("gene_symbol")
    .agg(
        control_calls=("condition", lambda x: int((x == "control").sum())),
        non_control_calls=("condition", lambda x: int((x != "control").sum())),
        total_alt_reads=("alt_reads", "sum"),
    )
    .reset_index()
)
result = grouped[(grouped["control_calls"] > 0) & (grouped["non_control_calls"] > 0)].copy()
result = result.sort_values(["total_alt_reads", "gene_symbol"], ascending=[False, True])
result = result[["gene_symbol", "control_calls", "non_control_calls", "total_alt_reads"]]
""",
    "pass4.query5": """
import pandas as pd
import numpy as np

gv = gene_dim.merge(variant_dim, on="gene_id", how="left")
gvf = gv.merge(fact_calls, on="variant_id", how="left")
full = gvf.merge(sample_dim, on="sample_id", how="left")

def expr_for_row(row):
    if pd.isna(row["call_id"]) or pd.isna(row["plant_line_id"]):
        return np.nan
    if row["gene_symbol"] == "NDHB":
        return row["expr_ndhb"]
    if row["gene_symbol"] == "NDHK":
        return row["expr_ndhk"]
    if row["gene_symbol"] == "PGR5":
        return row["expr_pgr5"]
    return np.nan

full["matched_expression"] = full.apply(expr_for_row, axis=1)
rows = []
for _, gene in gene_dim.sort_values("gene_symbol").iterrows():
    block = full[full["gene_id"] == gene["gene_id"]]
    rows.append([
        gene["gene_symbol"],
        int(block["variant_id"].dropna().nunique()),
        int(block["call_id"].dropna().nunique()),
        int(block.loc[block["plant_line_id"].notna(), "sample_id"].nunique()),
        int(block.loc[block["plant_line_id"].notna(), "tissue"].nunique()),
        block["matched_expression"].mean(),
    ])

result = pd.DataFrame(rows, columns=[
    "gene_symbol",
    "variant_count",
    "call_count",
    "distinct_matched_sample_count",
    "distinct_tissue_count",
    "avg_matched_expression",
])
result["avg_matched_expression"] = result["avg_matched_expression"].round(3)
result = result[["gene_symbol", "variant_count", "call_count", "distinct_matched_sample_count", "distinct_tissue_count", "avg_matched_expression"]]
""",
    "pass4.query6": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
eligible = complete[
    (complete["genotype"] != "0/0") &
    (complete["impact"].isin(["high", "moderate"]))
].copy()
burden = (
    eligible
    .groupby("sample_id")["gene_symbol"]
    .nunique()
    .rename("burden_genes")
    .reset_index()
)
result = sample_dim[["sample_id", "tissue", "expr_ndhb", "expr_pgr5", "expr_ndhk"]].merge(burden, on="sample_id", how="left")
result["burden_genes"] = result["burden_genes"].fillna(0).astype(int)
result["mean_log2_marker_expr"] = np.mean(
    [
        np.log2(result["expr_ndhb"] + 1),
        np.log2(result["expr_pgr5"] + 1),
        np.log2(result["expr_ndhk"] + 1),
    ],
    axis=0,
).round(3)
result = result.sort_values(["burden_genes", "sample_id"], ascending=[False, True])
result = result[["sample_id", "tissue", "burden_genes", "mean_log2_marker_expr"]]
""",
    "pass4.query7": """
import pandas as pd
import numpy as np

parts = [
    pd.DataFrame({
        "source_table": ["fact_calls.sample_id"],
        "key_value": sorted(set(fact_calls["sample_id"]) - set(sample_dim["sample_id"])),
        "orphan_type": ["missing_in_sample_dim"],
    }),
    pd.DataFrame({
        "source_table": ["fact_calls.variant_id"],
        "key_value": sorted(set(fact_calls["variant_id"]) - set(variant_dim["variant_id"])),
        "orphan_type": ["missing_in_variant_dim"],
    }),
    pd.DataFrame({
        "source_table": ["variant_dim.gene_id"],
        "key_value": sorted(set(variant_dim["gene_id"]) - set(gene_dim["gene_id"])),
        "orphan_type": ["missing_in_gene_dim"],
    }),
    pd.DataFrame({
        "source_table": ["sample_dim.sample_id"],
        "key_value": sorted(set(sample_dim["sample_id"]) - set(fact_calls["sample_id"])),
        "orphan_type": ["unused_dimension_row"],
    }),
    pd.DataFrame({
        "source_table": ["variant_dim.variant_id"],
        "key_value": sorted(set(variant_dim["variant_id"]) - set(fact_calls["variant_id"])),
        "orphan_type": ["unused_dimension_row"],
    }),
    pd.DataFrame({
        "source_table": ["gene_dim.gene_id"],
        "key_value": sorted(set(gene_dim["gene_id"]) - set(variant_dim["gene_id"])),
        "orphan_type": ["no_variants_attached"],
    }),
]
result = pd.concat(parts, ignore_index=True)
result = result.sort_values(["source_table", "key_value"])
result = result[["source_table", "key_value", "orphan_type"]]
""",
    "pass4.query8": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
result = complete[complete["genotype"] != "0/0"].copy()
result["vaf"] = (result["alt_reads"] / result["total_reads"]).round(3)
result["matched_expr_count"] = np.select(
    [
        result["gene_symbol"].eq("NDHB"),
        result["gene_symbol"].eq("NDHK"),
        result["gene_symbol"].eq("PGR5"),
    ],
    [result["expr_ndhb"], result["expr_ndhk"], result["expr_pgr5"]],
    default=np.nan,
)
result["log2_matched_expr"] = np.log2(result["matched_expr_count"] + 1).round(3)
result = result.sort_values(["condition", "tissue", "gene_symbol", "variant_id", "call_id"])
result = result[[
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
]]
""",
    "pass4.query9": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
complete["vaf"] = complete["alt_reads"] / complete["total_reads"]
complete["matched_expr_count"] = np.select(
    [
        complete["gene_symbol"].eq("NDHB"),
        complete["gene_symbol"].eq("NDHK"),
        complete["gene_symbol"].eq("PGR5"),
    ],
    [complete["expr_ndhb"], complete["expr_ndhk"], complete["expr_pgr5"]],
    default=np.nan,
)
result = (
    complete
    .groupby("pathway", as_index=False)
    .agg(
        call_count=("call_id", "size"),
        non_reference_rate=("genotype", lambda x: (x != "0/0").mean()),
        mean_vaf=("vaf", "mean"),
        mean_matched_expr=("matched_expr_count", "mean"),
    )
)
for col in ["non_reference_rate", "mean_vaf", "mean_matched_expr"]:
    result[col] = result[col].round(3)
result = result.sort_values(["non_reference_rate", "pathway"], ascending=[False, True])
result = result[["pathway", "call_count", "non_reference_rate", "mean_vaf", "mean_matched_expr"]]
""",
    "pass4.query10": """
import pandas as pd
import numpy as np

joined = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="left", indicator="sample_join")
    .merge(variant_dim, on="variant_id", how="left", indicator="variant_join")
    .merge(gene_dim, on="gene_id", how="left", indicator="gene_join")
)
conditions = [
    joined["variant_join"].eq("left_only"),
    joined["sample_join"].eq("left_only"),
    joined["gene_join"].eq("left_only"),
]
choices = ["MISSING_VARIANT", "MISSING_SAMPLE", "MISSING_GENE"]
joined["join_status"] = np.select(conditions, choices, default="COMPLETE_CHAIN")
joined["repairable_by_human"] = joined["join_status"].isin(["MISSING_SAMPLE", "MISSING_GENE"])
result = joined.sort_values("call_id")
result = result[["call_id", "sample_id", "variant_id", "join_status", "repairable_by_human"]]
""",
    "pass5.query1": """
import pandas as pd
import numpy as np

result = sample_dim[["sample_id", "tissue", "expr_ndhb", "expr_pgr5", "expr_ndhk"]].copy()
result["log2_expr_ndhb"] = np.log2(result["expr_ndhb"] + 1).round(3)
result["log2_expr_pgr5"] = np.log2(result["expr_pgr5"] + 1).round(3)
result["log2_expr_ndhk"] = np.log2(result["expr_ndhk"] + 1).round(3)
total = result["expr_ndhb"] + result["expr_pgr5"] + result["expr_ndhk"]
result["ndh_module_ratio"] = ((result["expr_ndhb"] + result["expr_ndhk"]) / total).round(3)
result = result.sort_values("sample_id")
result = result[["sample_id", "tissue", "log2_expr_ndhb", "log2_expr_pgr5", "log2_expr_ndhk", "ndh_module_ratio"]]
""",
    "pass5.query2": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
complete["matched_expr_count"] = np.select(
    [
        complete["gene_symbol"].eq("NDHB"),
        complete["gene_symbol"].eq("NDHK"),
        complete["gene_symbol"].eq("PGR5"),
    ],
    [complete["expr_ndhb"], complete["expr_ndhk"], complete["expr_pgr5"]],
    default=np.nan,
)
complete["_log2_matched_expr_raw"] = np.log2(complete["matched_expr_count"] + 1)
complete["_vaf_raw"] = complete["alt_reads"] / complete["total_reads"]
complete["log2_matched_expr"] = complete["_log2_matched_expr_raw"].round(3)
complete["vaf"] = complete["_vaf_raw"].round(3)
complete["expr_weighted_vaf"] = (complete["_vaf_raw"] * complete["_log2_matched_expr_raw"]).round(3)
result = complete.sort_values("call_id")
result = result[["call_id", "gene_symbol", "matched_expr_count", "log2_matched_expr", "vaf", "expr_weighted_vaf"]]
""",
    "pass5.query3": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
complete["matched_expr_count"] = np.select(
    [
        complete["gene_symbol"].eq("NDHB"),
        complete["gene_symbol"].eq("NDHK"),
        complete["gene_symbol"].eq("PGR5"),
    ],
    [complete["expr_ndhb"], complete["expr_ndhk"], complete["expr_pgr5"]],
    default=np.nan,
)
result = (
    complete
    .groupby(["condition", "gene_symbol"], as_index=False)
    .agg(
        n_calls=("call_id", "size"),
        mean_matched_expr=("matched_expr_count", "mean"),
        median_matched_expr=("matched_expr_count", "median"),
        pop_std_matched_expr=("matched_expr_count", lambda x: x.std(ddof=0)),
    )
)
for col in ["mean_matched_expr", "median_matched_expr", "pop_std_matched_expr"]:
    result[col] = result[col].round(3)
result = result.sort_values(["condition", "gene_symbol"])
result = result[["condition", "gene_symbol", "n_calls", "mean_matched_expr", "median_matched_expr", "pop_std_matched_expr"]]
""",
    "pass5.query4": """
import pandas as pd
import numpy as np

tmp = sample_dim.copy()
tmp["stress_group"] = np.where(tmp["condition"].isin(["high_light", "drought"]), "stress", "control")
rows = []
for gene_symbol, expr_col in [("NDHB", "expr_ndhb"), ("NDHK", "expr_ndhk"), ("PGR5", "expr_pgr5")]:
    tmp["log_expr"] = np.log2(tmp[expr_col] + 1)
    stress_mean = tmp.loc[tmp["stress_group"] == "stress", "log_expr"].mean()
    control_mean = tmp.loc[tmp["stress_group"] == "control", "log_expr"].mean()
    rows.append([
        gene_symbol,
        round(stress_mean, 3),
        round(control_mean, 3),
        round(stress_mean - control_mean, 3),
    ])
result = pd.DataFrame(rows, columns=["gene_symbol", "stress_mean_log2", "control_mean_log2", "delta_log2_stress_minus_control"])
result = result.sort_values("gene_symbol")
result = result[["gene_symbol", "stress_mean_log2", "control_mean_log2", "delta_log2_stress_minus_control"]]
""",
    "pass5.query5": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
nonref = complete[complete["genotype"] != "0/0"].copy()
nonref["vaf"] = nonref["alt_reads"] / nonref["total_reads"]
nonref["matched_expr_count"] = np.select(
    [
        nonref["gene_symbol"].eq("NDHB"),
        nonref["gene_symbol"].eq("NDHK"),
        nonref["gene_symbol"].eq("PGR5"),
    ],
    [nonref["expr_ndhb"], nonref["expr_ndhk"], nonref["expr_pgr5"]],
    default=np.nan,
)
nonref["log2_matched_expr"] = np.log2(nonref["matched_expr_count"] + 1)
nonref["weighted"] = nonref["vaf"] * nonref["log2_matched_expr"]
result = (
    nonref
    .groupby(["pathway", "tissue"], as_index=False)
    .agg(
        non_reference_calls=("call_id", "size"),
        mean_vaf=("vaf", "mean"),
        mean_log2_matched_expr=("log2_matched_expr", "mean"),
        burden_score=("weighted", "sum"),
    )
)
for col in ["mean_vaf", "mean_log2_matched_expr", "burden_score"]:
    result[col] = result[col].round(3)
result = result.sort_values(["pathway", "tissue"])
result = result[["pathway", "tissue", "non_reference_calls", "mean_vaf", "mean_log2_matched_expr", "burden_score"]]
""",
    "pass5.query6": """
import pandas as pd
import numpy as np

result = sample_dim[["sample_id", "expr_ndhb", "expr_pgr5", "expr_ndhk"]].copy()
for out_col, expr_col in [("z_ndhb", "expr_ndhb"), ("z_pgr5", "expr_pgr5"), ("z_ndhk", "expr_ndhk")]:
    result[out_col] = (result[expr_col] - result[expr_col].mean()) / result[expr_col].std(ddof=0)
result["photosynthesis_expr_z_mean"] = result[["z_ndhb", "z_pgr5", "z_ndhk"]].mean(axis=1)
for col in ["z_ndhb", "z_pgr5", "z_ndhk", "photosynthesis_expr_z_mean"]:
    result[col] = result[col].round(3)
result = result.sort_values(["photosynthesis_expr_z_mean", "sample_id"], ascending=[False, True])
result = result[["sample_id", "z_ndhb", "z_pgr5", "z_ndhk", "photosynthesis_expr_z_mean"]]
""",
    "pass5.query7": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
complete["vaf"] = complete["alt_reads"] / complete["total_reads"]
complete["matched_expr_count"] = np.select(
    [
        complete["gene_symbol"].eq("NDHB"),
        complete["gene_symbol"].eq("NDHK"),
        complete["gene_symbol"].eq("PGR5"),
    ],
    [complete["expr_ndhb"], complete["expr_ndhk"], complete["expr_pgr5"]],
    default=np.nan,
)
result = (
    complete
    .groupby("condition", as_index=False)
    .agg(
        distinct_genes_observed=("gene_symbol", "nunique"),
        mean_matched_expr=("matched_expr_count", "mean"),
        cv_matched_expr=("matched_expr_count", lambda x: x.std(ddof=0) / x.mean()),
        mean_vaf=("vaf", "mean"),
    )
)
for col in ["mean_matched_expr", "cv_matched_expr", "mean_vaf"]:
    result[col] = result[col].round(3)
result = result.sort_values("condition")
result = result[["condition", "distinct_genes_observed", "mean_matched_expr", "cv_matched_expr", "mean_vaf"]]
""",
    "pass5.query8": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
nonref = complete[complete["genotype"] != "0/0"].copy()
summary = (
    nonref
    .groupby("sample_id", as_index=False)
    .agg(
        non_reference_complete_chain_calls=("call_id", "size"),
        high_or_moderate_nonref_calls=("impact", lambda x: int(x.isin(["high", "moderate"]).sum())),
    )
)
result = sample_dim[["sample_id", "tissue", "expr_ndhb", "expr_pgr5", "expr_ndhk"]].merge(summary, on="sample_id", how="left")
result[["non_reference_complete_chain_calls", "high_or_moderate_nonref_calls"]] = (
    result[["non_reference_complete_chain_calls", "high_or_moderate_nonref_calls"]]
    .fillna(0)
    .astype(int)
)
result["total_marker_expr"] = result["expr_ndhb"] + result["expr_pgr5"] + result["expr_ndhk"]
result["log2_total_marker_expr"] = np.log2(result["total_marker_expr"] + 1).round(3)
result["photosynthesis_variant_pressure"] = (result["high_or_moderate_nonref_calls"] * result["log2_total_marker_expr"]).round(3)
result = result.sort_values(["photosynthesis_variant_pressure", "sample_id"], ascending=[False, True])
result = result[["sample_id", "tissue", "non_reference_complete_chain_calls", "high_or_moderate_nonref_calls", "total_marker_expr", "log2_total_marker_expr", "photosynthesis_variant_pressure"]]
""",
    "pass5.query9": """
import pandas as pd
import numpy as np

complete = (
    fact_calls
    .merge(sample_dim, on="sample_id", how="inner")
    .merge(variant_dim, on="variant_id", how="inner")
    .merge(gene_dim, on="gene_id", how="inner")
)
nonref = complete[complete["genotype"] != "0/0"].copy()
nonref["vaf"] = nonref["alt_reads"] / nonref["total_reads"]
nonref["matched_expr_count"] = np.select(
    [
        nonref["gene_symbol"].eq("NDHB"),
        nonref["gene_symbol"].eq("NDHK"),
        nonref["gene_symbol"].eq("PGR5"),
    ],
    [nonref["expr_ndhb"], nonref["expr_ndhk"], nonref["expr_pgr5"]],
    default=np.nan,
)
nonref["log2_matched_expr"] = np.log2(nonref["matched_expr_count"] + 1)
result = (
    nonref
    .groupby(["condition", "gene_symbol"], as_index=False)
    .agg(
        non_reference_calls=("call_id", "size"),
        mean_vaf=("vaf", "mean"),
        mean_log2_matched_expr=("log2_matched_expr", "mean"),
    )
)
result["expression_weighted_signal"] = result["mean_vaf"] * result["mean_log2_matched_expr"]
for col in ["mean_vaf", "mean_log2_matched_expr", "expression_weighted_signal"]:
    result[col] = result[col].round(3)
result = result.sort_values(["expression_weighted_signal", "gene_symbol", "condition"], ascending=[False, True, True])
result = result[["condition", "gene_symbol", "non_reference_calls", "mean_vaf", "mean_log2_matched_expr", "expression_weighted_signal"]]
""",
    "pass5.query10": """
import pandas as pd
import numpy as np

result = sample_dim[["sample_id", "condition", "expr_ndhb", "expr_pgr5", "expr_ndhk"]].copy()
total = result["expr_ndhb"] + result["expr_pgr5"] + result["expr_ndhk"]
result["ndhb_share"] = result["expr_ndhb"] / total
result["pgr5_share"] = result["expr_pgr5"] / total
result["ndhk_share"] = result["expr_ndhk"] / total
result["marker_imbalance"] = result[["ndhb_share", "pgr5_share", "ndhk_share"]].max(axis=1) - result[["ndhb_share", "pgr5_share", "ndhk_share"]].min(axis=1)
for col in ["ndhb_share", "pgr5_share", "ndhk_share", "marker_imbalance"]:
    result[col] = result[col].round(3)
result = result.sort_values(["marker_imbalance", "sample_id"], ascending=[False, True])
result = result[["sample_id", "condition", "ndhb_share", "pgr5_share", "ndhk_share", "marker_imbalance"]]
""",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def normalize_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.generic,)):
        value = value.item()
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        if value.is_integer():
            return int(value)
        return float(value)
    if pd.isna(value):
        return None
    return value


def normalize_rows(rows: list[list[Any]]) -> list[list[Any]]:
    return [[normalize_scalar(cell) for cell in row] for row in rows]


def dataset_frames(dataset: dict[str, Any]) -> dict[str, pd.DataFrame]:
    frames = {}
    for table_name, table in dataset["tables"].items():
        frames[table_name] = pd.DataFrame(table["rows"], columns=table["columns"])
    return frames


def sqlite_connection(dataset: dict[str, Any]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    for table_name, frame in dataset_frames(dataset).items():
        frame.to_sql(table_name, con, index=False, if_exists="replace")
    return con


def execute_sql_solution(dataset: dict[str, Any], code: str) -> tuple[list[str], list[list[Any]]]:
    con = sqlite_connection(dataset)
    try:
        cur = con.execute(code)
        columns = [desc[0] for desc in cur.description]
        rows = [list(row) for row in cur.fetchall()]
        return columns, normalize_rows(rows)
    finally:
        con.close()


def execute_python_solution(dataset: dict[str, Any], code: str) -> tuple[list[str], list[list[Any]]]:
    namespace: dict[str, Any] = {"pd": pd, "np": np}
    namespace.update(dataset_frames(dataset))
    exec(code, namespace)
    result = namespace.get("result")
    if not isinstance(result, pd.DataFrame):
        raise ValueError("Python solution did not define a pandas DataFrame named `result`")
    columns = list(result.columns)
    rows = normalize_rows(result.where(pd.notna(result), None).values.tolist())
    return columns, rows


def values_match(left: Any, right: Any, tolerance: float = 0.001) -> bool:
    left = normalize_scalar(left)
    right = normalize_scalar(right)
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) <= tolerance
    return left == right


def table_matches_gold(columns: list[str], rows: list[list[Any]], gold: dict[str, Any]) -> bool:
    if columns != gold["columns"]:
        return False
    gold_rows = gold["rows"]
    if len(rows) != len(gold_rows):
        return False
    for actual_row, gold_row in zip(rows, gold_rows):
        if len(actual_row) != len(gold_row):
            return False
        if any(not values_match(actual, expected) for actual, expected in zip(actual_row, gold_row)):
            return False
    return True


def validate_reference_solutions(cases: list[dict[str, Any]], gold_lookup: dict[str, dict[str, Any]], dataset: dict[str, Any]) -> None:
    failures = []
    for case in cases:
        case_id = case["case_id"]
        code = solution_code_for_case(case)
        if case["pass"] <= 3:
            columns, rows = execute_sql_solution(dataset, code)
        else:
            columns, rows = execute_python_solution(dataset, code)
        if not table_matches_gold(columns, rows, gold_lookup[case_id]):
            failures.append(
                {
                    "case_id": case_id,
                    "columns": columns,
                    "gold_columns": gold_lookup[case_id]["columns"],
                    "rows": rows,
                    "gold_rows": gold_lookup[case_id]["rows"],
                }
            )
    if failures:
        preview = json.dumps(failures[:3], indent=2, ensure_ascii=False)
        raise RuntimeError(f"{len(failures)} reference solutions failed validation:\n{preview}")


def solution_code_for_case(case: dict[str, Any]) -> str:
    case_id = case["case_id"]
    if case["pass"] <= 3:
        code = SQL_SOLUTIONS.get(case_id)
    else:
        code = PYTHON_SOLUTIONS.get(case_id)
    if not code:
        raise KeyError(f"Missing reference solution for {case_id}")
    return code.strip()


def footer_language(case: dict[str, Any]) -> str:
    return "sql" if case["pass"] <= 3 else "python"


def v6_prompt(base_prompt: str, language: str, code: str) -> str:
    return f"{base_prompt.rstrip()}\n\n{FOOTER_PREFIX}\n```{language}\n{code.strip()}\n```"


def build_v6_instructions() -> dict[str, Any]:
    v2 = json.loads(V2_INSTRUCTIONS_PATH.read_text(encoding="utf-8"))
    by_lang = {item["language"]: item for item in v2["instructions"]}
    return {
        "benchmark_id": BENCHMARK_ID,
        "instructions": [
            {
                "standard_instructions_id": "sql_v5",
                "language": "sql",
                "text": by_lang["sql"]["text"],
            },
            {
                "standard_instructions_id": "python_v5",
                "language": "python",
                "text": by_lang["python"]["text"],
            },
        ],
        "notes": "Instruction ids remain sql_v5/python_v5 for current schema compatibility; instruction text is copied from the v2 run.",
    }


def build_manifest() -> dict[str, Any]:
    manifest = json.loads(ROOT_MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest = copy.deepcopy(manifest)
    manifest["benchmark_id"] = BENCHMARK_ID
    manifest["version"] = VERSION
    manifest["output_version_id"] = OUTPUT_VERSION_ID
    manifest["dataset_file"] = "../../../shared_dataset.json"
    manifest["cases_file"] = "benchmark_cases.jsonl"
    manifest["gold_file"] = "../../../gold_answers.jsonl"
    manifest["results_template_file"] = "../../../results_template.jsonl"
    manifest["schemas"] = {
        "case": "../../../benchmark_case.schema.json",
        "gold": "../../../gold_answer.schema.json",
        "result": "../../../run_result.schema.json",
    }
    manifest["standard_instructions_file"] = "standard_instructions.json"
    manifest["default_repeat_group_id"] = "default_repeatability_v6_code_footer"
    manifest["prompt_rendering"] = {
        "include_query_context_title": False,
        "include_query_metadata": False,
        "reason": "v6 prompts keep original v2 query text plus code footer; runner-added Part 3 title and case metadata are suppressed.",
    }
    manifest["query_engineering"] = {
        "enabled": False,
        "registry_id": "photosynthesis_snowflake_v6_code_footer",
        "strategy": "v2_original_prompt_plus_reference_solution_code_footer",
        "reference_solution_file": "query_engineering_registry/runs/v6/reference_solutions.jsonl",
        "footer_policy": "append only `Produce the output using the following code:` plus fenced SQL for passes 1-3 or fenced Python for passes 4-5",
        "comparability": "oracle-code control; not comparable to non-oracle benchmark runs",
    }
    manifest["runner_notes"] = {
        **manifest.get("runner_notes", {}),
        "v6_code_footer": (
            "v6 uses original v2 case prompt text and appends reference SQL/Python solution code. "
            "The solution algorithm is present in the prompt, so scores measure code-following and JSON output compliance rather than independent data reasoning."
        ),
    }
    return manifest


def build_v6_cases(v2_cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    cases = []
    references = []
    previews = []
    for case in v2_cases:
        case_id = case["case_id"]
        language = footer_language(case)
        code = solution_code_for_case(case)
        rec = copy.deepcopy(case)
        rec["benchmark_id"] = BENCHMARK_ID
        rec["standard_instructions_id"] = "sql_v5" if rec["language"] == "sql" else "python_v5"
        rec["prompt"] = v6_prompt(case["prompt"], language, code)
        rec["metadata"] = copy.deepcopy(rec["metadata"])
        rec["metadata"]["tags"] = sorted(set(rec["metadata"]["tags"] + ["v6_code_footer", "oracle_code_control"]))
        cases.append(rec)
        references.append(
            {
                "case_id": case_id,
                "pass": case["pass"],
                "query": case["query"],
                "language": language,
                "code": code,
            }
        )
        previews.append(
            {
                "case_id": case_id,
                "pass": case["pass"],
                "query": case["query"],
                "language": rec["language"],
                "base_prompt": case["prompt"],
                "footer_language": language,
                "footer_prefix": FOOTER_PREFIX,
                "solution_code": code,
                "final_prompt": rec["prompt"],
                "final_prompt_chars": len(rec["prompt"]),
            }
        )
    return cases, references, previews


def write_readme() -> None:
    readme = f"""# AIBioBench v6 Code-Footer Query Snapshot

This directory contains the v6 oracle-code control prompt snapshot.

v6 prompts are intentionally not comparable to normal benchmark prompts. Each
case uses the original v2 prompt text and appends only this footer:

````text
{FOOTER_PREFIX}
```<sql-or-python>
<reference solution code>
```
````

Footer policy:

- passes 1-3 use SQL reference code
- passes 4-5 use Python/pandas reference code
- no gold-answer rows are pasted directly into the footer
- every reference solution is validated against `gold_answers.jsonl`
- v6 suppresses the runner-added `Part 3 - Query-specific context` title and
  benchmark/case/pass/difficulty/language metadata in the model prompt

Generated files:

- `benchmark_cases.jsonl`: v6 cases used by the runner
- `standard_instructions.json`: schema-compatible instruction ids with v2 instruction text
- `reference_solutions.jsonl`: per-case reference SQL/Python code
- `prompt_preview.jsonl`: audit preview of the final case prompt field
- `benchmark_manifest.json`: v6 manifest snapshot

Benchmark mode: oracle-code control. Scores measure code-following and JSON
output compliance, not independent reasoning.
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    v2_cases = read_jsonl(V2_CASES_PATH)
    gold = read_jsonl(GOLD_PATH)
    gold_lookup = {row["case_id"]: row for row in gold}

    case_ids = {case["case_id"] for case in v2_cases}
    gold_ids = set(gold_lookup)
    solution_ids = set(SQL_SOLUTIONS) | set(PYTHON_SOLUTIONS)
    if case_ids != gold_ids:
        raise RuntimeError(f"v2/gold case mismatch: missing_gold={sorted(case_ids - gold_ids)} missing_case={sorted(gold_ids - case_ids)}")
    if case_ids != solution_ids:
        raise RuntimeError(f"v2/solution case mismatch: missing_solution={sorted(case_ids - solution_ids)} extra_solution={sorted(solution_ids - case_ids)}")

    v6_cases, references, previews = build_v6_cases(v2_cases)
    validate_reference_solutions(v6_cases, gold_lookup, dataset)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUT_DIR / "benchmark_cases.jsonl", v6_cases)
    write_json(OUT_DIR / "standard_instructions.json", build_v6_instructions())
    write_jsonl(OUT_DIR / "reference_solutions.jsonl", references)
    write_jsonl(OUT_DIR / "prompt_preview.jsonl", previews)
    write_json(OUT_DIR / "benchmark_manifest.json", build_manifest())
    write_readme()

    sql_count = sum(1 for row in references if row["language"] == "sql")
    python_count = sum(1 for row in references if row["language"] == "python")
    print(f"wrote {OUT_DIR}")
    print(f"validated reference solutions: sql={sql_count} python={python_count} total={len(references)}")
    print(f"generated v6 cases: {len(v6_cases)}")


if __name__ == "__main__":
    main()
