-- AIBioBench Pass 3 SQL

-- ============================================================
-- pass3.query1
-- Prompt:
-- Left join fact_calls across the full snowflake and classify each fact row into one join_status using this logic:
-- - COMPLETE_CHAIN: sample, variant, and gene all matched
-- - MISSING_SAMPLE: sample missing but variant and gene matched
-- - MISSING_GENE: variant matched but gene missing
-- - MISSING_VARIANT: variant missing
-- Return: call_id, sample_id, variant_id, join_status
-- Sort by call_id ascending.
SELECT
    f.call_id,
    f.sample_id,
    f.variant_id,
    CASE
        WHEN v.variant_id IS NULL THEN 'MISSING_VARIANT'
        WHEN g.gene_id IS NULL THEN 'MISSING_GENE'
        WHEN s.sample_id IS NULL THEN 'MISSING_SAMPLE'
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

-- Expected result:
-- +---------+-----------+------------+-----------------+
-- | call_id | sample_id | variant_id | join_status     |
-- +---------+-----------+------------+-----------------+
-- | 1       | S1        | V1         | COMPLETE_CHAIN  |
-- | 2       | S1        | V2         | COMPLETE_CHAIN  |
-- | 3       | S2        | V1         | COMPLETE_CHAIN  |
-- | 4       | S2        | V3         | COMPLETE_CHAIN  |
-- | 5       | S3        | V4         | COMPLETE_CHAIN  |
-- | 6       | S3        | V5         | MISSING_GENE    |
-- | 7       | S4        | V3         | COMPLETE_CHAIN  |
-- | 8       | S999      | V2         | MISSING_SAMPLE  |
-- | 9       | S2        | V999       | MISSING_VARIANT |
-- +---------+-----------+------------+-----------------+

-- ============================================================
-- pass3.query2
-- Prompt:
-- Using only complete-chain matched rows, group by tissue and gene_symbol.
-- Compute:
-- - call_count
-- - sum_alt_reads
-- - avg_vaf where VAF = alt_reads / total_reads
-- - max_qual
-- Return: tissue, gene_symbol, call_count, sum_alt_reads, avg_vaf, max_qual
-- Sort by tissue ascending, then gene_symbol ascending.
-- Round avg_vaf to 3 decimals.
SELECT
    s.tissue,
    g.gene_symbol,
    COUNT(*) AS call_count,
    SUM(f.alt_reads) AS sum_alt_reads,
    ROUND(AVG(CAST(f.alt_reads AS DECIMAL(18, 6)) / NULLIF(CAST(f.total_reads AS DECIMAL(18, 6)), 0)), 3) AS avg_vaf,
    MAX(f.qual) AS max_qual
FROM fact_calls AS f
INNER JOIN sample_dim AS s
    ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
    ON v.gene_id = g.gene_id
GROUP BY
    s.tissue,
    g.gene_symbol
ORDER BY
    s.tissue ASC,
    g.gene_symbol ASC;

-- Expected result:
-- +-------------+-------------+------------+---------------+---------+----------+
-- | tissue      | gene_symbol | call_count | sum_alt_reads | avg_vaf | max_qual |
-- +-------------+-------------+------------+---------------+---------+----------+
-- | mature_leaf | NDHB        | 3          | 40            | 0.467   | 99       |
-- | mature_leaf | NDHK        | 1          | 10            | 0.500   | 80       |
-- | young_leaf  | NDHK        | 1          | 0             | 0.000   | 88       |
-- | young_leaf  | PGR5        | 1          | 9             | 0.500   | 70       |
-- +-------------+-------------+------------+---------------+---------+----------+

-- ============================================================
-- pass3.query3
-- Prompt:
-- Start from gene_dim and left join to variant_dim, then fact_calls.
-- Return one row per gene with:
-- gene_symbol, pathway, observed_call_count, total_alt_reads
-- Count matched fact rows per gene.
-- Include genes with zero observed calls.
-- Sort by observed_call_count descending, then gene_symbol ascending.
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
GROUP BY
    g.gene_symbol,
    g.pathway
ORDER BY
    observed_call_count DESC,
    g.gene_symbol ASC;

-- Expected result:
-- +-------------+--------------------------+---------------------+-----------------+
-- | gene_symbol | pathway                  | observed_call_count | total_alt_reads |
-- +-------------+--------------------------+---------------------+-----------------+
-- | NDHB        | chloroplast_NDH_complex  | 4                   | 54              |
-- | NDHK        | chloroplast_NDH_complex  | 2                   | 10              |
-- | PGR5        | cyclic_electron_flow     | 1                   | 9               |
-- | NDHT        | chlororespiration        | 0                   | 0               |
-- | PGR1B       | PSI_photoprotection      | 0                   | 0               |
-- +-------------+--------------------------+---------------------+-----------------+

-- ============================================================
-- pass3.query4
-- Prompt:
-- Inner join fact_calls to sample_dim and variant_dim.
-- Filter to impact = 'high'.
-- For each condition, compute:
-- - high_impact_call_count
-- - avg_qual
-- - avg_alt_reads
-- Return: condition, high_impact_call_count, avg_qual, avg_alt_reads
-- Sort by condition ascending.
-- Round decimal outputs to 3 decimals.
SELECT
    s.condition,
    COUNT(*) AS high_impact_call_count,
    ROUND(AVG(CAST(f.qual AS DECIMAL(18, 6))), 3) AS avg_qual,
    ROUND(AVG(CAST(f.alt_reads AS DECIMAL(18, 6))), 3) AS avg_alt_reads
FROM fact_calls AS f
INNER JOIN sample_dim AS s
    ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
WHERE v.impact = 'high'
GROUP BY s.condition
ORDER BY s.condition ASC;

-- Expected result:
-- +------------+------------------------+----------+---------------+
-- | condition  | high_impact_call_count | avg_qual | avg_alt_reads |
-- +------------+------------------------+----------+---------------+
-- | control    | 2                      | 84.000   | 5.000         |
-- | high_light | 1                      | 87.000   | 28.000        |
-- +------------+------------------------+----------+---------------+

-- ============================================================
-- pass3.query5
-- Prompt:
-- Using sample_dim as the preserving table, count genotype classes per sample.
-- Compute:
-- - heterozygous_calls where genotype = '0/1'
-- - homozygous_alt_calls where genotype = '1/1'
-- - mean_nonref_qual over only non-reference calls where genotype in ('0/1','1/1')
-- Return: sample_id, heterozygous_calls, homozygous_alt_calls, mean_nonref_qual
-- Include samples with zero calls.
-- Sort by sample_id ascending.
-- Round mean_nonref_qual to 3 decimals.
SELECT
    s.sample_id,
    COUNT(CASE WHEN f.genotype = '0/1' THEN 1 END) AS heterozygous_calls,
    COUNT(CASE WHEN f.genotype = '1/1' THEN 1 END) AS homozygous_alt_calls,
    ROUND(AVG(CASE WHEN f.genotype IN ('0/1', '1/1') THEN CAST(f.qual AS DECIMAL(18, 6)) END), 3) AS mean_nonref_qual
FROM sample_dim AS s
LEFT JOIN fact_calls AS f
    ON s.sample_id = f.sample_id
GROUP BY s.sample_id
ORDER BY s.sample_id ASC;

-- Expected result:
-- +-----------+-------------------+----------------------+------------------+
-- | sample_id | heterozygous_calls| homozygous_alt_calls | mean_nonref_qual |
-- +-----------+-------------------+----------------------+------------------+
-- | S1        | 1                 | 1                    | 93.000           |
-- | S2        | 2                 | 0                    | 67.500           |
-- | S3        | 1                 | 1                    | 81.000           |
-- | S4        | 0                 | 0                    | NULL             |
-- | S5        | 0                 | 0                    | NULL             |
-- +-----------+-------------------+----------------------+------------------+

-- ============================================================
-- pass3.query6
-- Prompt:
-- Using only complete-chain matched rows, compute total_alt_reads and avg_vaf by tissue and gene_symbol.
-- Within each tissue, rank genes by total_alt_reads descending using dense rank.
-- Return: tissue, gene_symbol, total_alt_reads, avg_vaf, rank_in_tissue
-- Sort by tissue ascending, then rank_in_tissue ascending, then gene_symbol ascending.
-- Round avg_vaf to 3 decimals.
WITH gene_tissue_summary AS (
    SELECT
        s.tissue,
        g.gene_symbol,
        SUM(f.alt_reads) AS total_alt_reads,
        ROUND(AVG(CAST(f.alt_reads AS DECIMAL(18, 6)) / NULLIF(CAST(f.total_reads AS DECIMAL(18, 6)), 0)), 3) AS avg_vaf
    FROM fact_calls AS f
    INNER JOIN sample_dim AS s
        ON f.sample_id = s.sample_id
    INNER JOIN variant_dim AS v
        ON f.variant_id = v.variant_id
    INNER JOIN gene_dim AS g
        ON v.gene_id = g.gene_id
    GROUP BY
        s.tissue,
        g.gene_symbol
)
SELECT
    tissue,
    gene_symbol,
    total_alt_reads,
    avg_vaf,
    DENSE_RANK() OVER (
        PARTITION BY tissue
        ORDER BY total_alt_reads DESC
    ) AS rank_in_tissue
FROM gene_tissue_summary
ORDER BY
    tissue ASC,
    rank_in_tissue ASC,
    gene_symbol ASC;

-- Expected result:
-- +-------------+-------------+-----------------+---------+----------------+
-- | tissue      | gene_symbol | total_alt_reads | avg_vaf | rank_in_tissue |
-- +-------------+-------------+-----------------+---------+----------------+
-- | mature_leaf | NDHB        | 40              | 0.467   | 1              |
-- | mature_leaf | NDHK        | 10              | 0.500   | 2              |
-- | young_leaf  | PGR5        | 9               | 0.500   | 1              |
-- | young_leaf  | NDHK        | 0               | 0.000   | 2              |
-- +-------------+-------------+-----------------+---------+----------------+

-- ============================================================
-- pass3.query7
-- Prompt:
-- Find unused dimension rows across both branches using anti-join logic.
-- Return: object_type, object_id, reason
-- Use these rules:
-- - sample_dim rows with no fact_calls => no_fact_calls
-- - variant_dim rows with no fact_calls => no_fact_calls
-- - gene_dim rows with variants but no fact_calls through those variants => no_fact_calls_through_variants
-- - gene_dim rows with no variants at all => no_variants_attached
-- Sort by object_type ascending, then object_id ascending.
SELECT
    'gene' AS object_type,
    g.gene_id AS object_id,
    'no_fact_calls_through_variants' AS reason
FROM gene_dim AS g
WHERE EXISTS (
    SELECT 1
    FROM variant_dim AS v
    WHERE v.gene_id = g.gene_id
)
AND NOT EXISTS (
    SELECT 1
    FROM variant_dim AS v
    INNER JOIN fact_calls AS f
        ON v.variant_id = f.variant_id
    WHERE v.gene_id = g.gene_id
)

UNION ALL

SELECT
    'gene' AS object_type,
    g.gene_id AS object_id,
    'no_variants_attached' AS reason
FROM gene_dim AS g
WHERE NOT EXISTS (
    SELECT 1
    FROM variant_dim AS v
    WHERE v.gene_id = g.gene_id
)

UNION ALL

SELECT
    'sample' AS object_type,
    s.sample_id AS object_id,
    'no_fact_calls' AS reason
FROM sample_dim AS s
WHERE NOT EXISTS (
    SELECT 1
    FROM fact_calls AS f
    WHERE f.sample_id = s.sample_id
)

UNION ALL

SELECT
    'variant' AS object_type,
    v.variant_id AS object_id,
    'no_fact_calls' AS reason
FROM variant_dim AS v
WHERE NOT EXISTS (
    SELECT 1
    FROM fact_calls AS f
    WHERE f.variant_id = v.variant_id
)

ORDER BY
    object_type ASC,
    object_id ASC;

-- Expected result:
-- +-------------+-----------+-------------------------------+
-- | object_type | object_id | reason                        |
-- +-------------+-----------+-------------------------------+
-- | gene        | G4        | no_fact_calls_through_variants|
-- | gene        | G5        | no_variants_attached          |
-- | sample      | S5        | no_fact_calls                 |
-- | variant     | V6        | no_fact_calls                 |
-- +-------------+-----------+-------------------------------+

-- ============================================================
-- pass3.query8
-- Prompt:
-- Using complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0'.
-- Group by condition and gene_role.
-- Return: condition, gene_role, non_reference_call_count, mean_vaf
-- Sort by condition ascending, then gene_role ascending.
-- Round mean_vaf to 3 decimals.
SELECT
    s.condition,
    g.gene_role,
    COUNT(*) AS non_reference_call_count,
    ROUND(AVG(CAST(f.alt_reads AS DECIMAL(18, 6)) / NULLIF(CAST(f.total_reads AS DECIMAL(18, 6)), 0)), 3) AS mean_vaf
FROM fact_calls AS f
INNER JOIN sample_dim AS s
    ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
    ON v.gene_id = g.gene_id
WHERE f.genotype <> '0/0'
GROUP BY
    s.condition,
    g.gene_role
ORDER BY
    s.condition ASC,
    g.gene_role ASC;

-- Expected result:
-- +------------+------------------+--------------------------+----------+
-- | condition  | gene_role        | non_reference_call_count | mean_vaf |
-- +------------+------------------+--------------------------+----------+
-- | control    | ndh_membrane_arm | 1                        | 0.500    |
-- | drought    | pgr_regulator    | 1                        | 0.500    |
-- | high_light | ndh_membrane_arm | 2                        | 0.700    |
-- +------------+------------------+--------------------------+----------+
