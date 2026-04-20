-- AIBioBench Pass 1 SQL
-- Schema:
--   fact_calls
--   sample_dim
--   variant_dim
--   gene_dim
--
-- Notes:
-- - ANSI SQL style
-- - Preserve requested sort order
-- - Round derived decimals to 3 places where requested
-- - Show SQL first, then expected result table in comments

-- ============================================================
-- pass1.query1
-- Prompt:
-- Inner join fact_calls to sample_dim on sample_id.
-- Return: call_id, sample_id, tissue, condition, genotype
-- Sort by call_id ascending.
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

-- Expected result:
-- +---------+-----------+-------------+------------+----------+
-- | call_id | sample_id | tissue      | condition  | genotype |
-- +---------+-----------+-------------+------------+----------+
-- | 1       | S1        | mature_leaf | high_light | 0/1      |
-- | 2       | S1        | mature_leaf | high_light | 1/1      |
-- | 3       | S2        | mature_leaf | control    | 0/0      |
-- | 4       | S2        | mature_leaf | control    | 0/1      |
-- | 5       | S3        | young_leaf  | drought    | 0/1      |
-- | 6       | S3        | young_leaf  | drought    | 1/1      |
-- | 7       | S4        | young_leaf  | control    | 0/0      |
-- | 9       | S2        | mature_leaf | control    | 0/1      |
-- +---------+-----------+-------------+------------+----------+

-- ============================================================
-- pass1.query2
-- Prompt:
-- Inner join fact_calls to variant_dim on variant_id.
-- Return: call_id, variant_id, variant_class, impact, qual
-- Sort by qual descending, then call_id ascending.
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

-- Expected result:
-- +---------+------------+---------------+----------+------+
-- | call_id | variant_id | variant_class | impact   | qual |
-- +---------+------------+---------------+----------+------+
-- | 1       | V1         | SNV           | moderate | 99   |
-- | 3       | V1         | SNV           | moderate | 95   |
-- | 6       | V5         | SNV           | modifier | 92   |
-- | 7       | V3         | SNV           | high     | 88   |
-- | 2       | V2         | indel         | high     | 87   |
-- | 4       | V3         | SNV           | high     | 80   |
-- | 5       | V4         | SNV           | low      | 70   |
-- | 8       | V2         | indel         | high     | 60   |
-- +---------+------------+---------------+----------+------+

-- ============================================================
-- pass1.query3
-- Prompt:
-- Left join fact_calls to sample_dim on sample_id.
-- Return: call_id, sample_id, tissue, batch, expr_ndhb
-- Keep all fact rows.
-- Sort by call_id ascending.
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

-- Expected result:
-- +---------+-----------+-------------+-------+-----------+
-- | call_id | sample_id | tissue      | batch | expr_ndhb |
-- +---------+-----------+-------------+-------+-----------+
-- | 1       | S1        | mature_leaf | B1    | 1200      |
-- | 2       | S1        | mature_leaf | B1    | 1200      |
-- | 3       | S2        | mature_leaf | B1    | 300       |
-- | 4       | S2        | mature_leaf | B1    | 300       |
-- | 5       | S3        | young_leaf  | B2    | 900       |
-- | 6       | S3        | young_leaf  | B2    | 900       |
-- | 7       | S4        | young_leaf  | B2    | 100       |
-- | 8       | S999      | NULL        | NULL  | NULL      |
-- | 9       | S2        | mature_leaf | B1    | 300       |
-- +---------+-----------+-------------+-------+-----------+

-- ============================================================
-- pass1.query4
-- Prompt:
-- Use a RIGHT JOIN from fact_calls to sample_dim, or an equivalent reversed LEFT JOIN.
-- Return one row per sample with:
-- sample_id, tissue, call_count, avg_qual
-- Include samples with zero calls.
-- Sort by sample_id ascending.
-- Round avg_qual to 3 decimals.
SELECT
    s.sample_id,
    s.tissue,
    COUNT(f.call_id) AS call_count,
    ROUND(AVG(CAST(f.qual AS DECIMAL(18, 6))), 3) AS avg_qual
FROM sample_dim AS s
LEFT JOIN fact_calls AS f
    ON s.sample_id = f.sample_id
GROUP BY
    s.sample_id,
    s.tissue
ORDER BY s.sample_id ASC;

-- Expected result:
-- +-----------+-------------+------------+----------+
-- | sample_id | tissue      | call_count | avg_qual |
-- +-----------+-------------+------------+----------+
-- | S1        | mature_leaf | 2          | 93.000   |
-- | S2        | mature_leaf | 3          | 76.667   |
-- | S3        | young_leaf  | 2          | 81.000   |
-- | S4        | young_leaf  | 1          | 88.000   |
-- | S5        | root        | 0          | NULL     |
-- +-----------+-------------+------------+----------+

-- ============================================================
-- pass1.query5
-- Prompt:
-- Inner join fact_calls to variant_dim, then to gene_dim.
-- Return: call_id, variant_id, gene_symbol, pathway
-- Sort by call_id ascending.
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

-- Expected result:
-- +---------+------------+-------------+--------------------------+
-- | call_id | variant_id | gene_symbol | pathway                  |
-- +---------+------------+-------------+--------------------------+
-- | 1       | V1         | NDHB        | chloroplast_NDH_complex  |
-- | 2       | V2         | NDHB        | chloroplast_NDH_complex  |
-- | 3       | V1         | NDHB        | chloroplast_NDH_complex  |
-- | 4       | V3         | NDHK        | chloroplast_NDH_complex  |
-- | 5       | V4         | PGR5        | cyclic_electron_flow     |
-- | 7       | V3         | NDHK        | chloroplast_NDH_complex  |
-- | 8       | V2         | NDHB        | chloroplast_NDH_complex  |
-- +---------+------------+-------------+--------------------------+

-- ============================================================
-- pass1.query6
-- Prompt:
-- Inner join fact_calls to variant_dim.
-- Count calls by impact and also compute average qual.
-- Return: impact, call_count, avg_qual
-- Sort by call_count descending, then impact ascending.
-- Round avg_qual to 3 decimals.
SELECT
    v.impact,
    COUNT(*) AS call_count,
    ROUND(AVG(CAST(f.qual AS DECIMAL(18, 6))), 3) AS avg_qual
FROM fact_calls AS f
INNER JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
GROUP BY v.impact
ORDER BY call_count DESC, v.impact ASC;

-- Expected result:
-- +----------+------------+----------+
-- | impact   | call_count | avg_qual |
-- +----------+------------+----------+
-- | high     | 4          | 78.750   |
-- | moderate | 2          | 97.000   |
-- | low      | 1          | 70.000   |
-- | modifier | 1          | 92.000   |
-- +----------+------------+----------+

-- ============================================================
-- pass1.query7
-- Prompt:
-- Inner join fact_calls to sample_dim.
-- Compute average, minimum, and maximum qual by tissue.
-- Return: tissue, avg_qual, min_qual, max_qual
-- Sort by avg_qual descending.
-- Round avg_qual to 3 decimals.
SELECT
    s.tissue,
    ROUND(AVG(CAST(f.qual AS DECIMAL(18, 6))), 3) AS avg_qual,
    MIN(f.qual) AS min_qual,
    MAX(f.qual) AS max_qual
FROM fact_calls AS f
INNER JOIN sample_dim AS s
    ON f.sample_id = s.sample_id
GROUP BY s.tissue
ORDER BY avg_qual DESC;

-- Expected result:
-- +-------------+----------+----------+----------+
-- | tissue      | avg_qual | min_qual | max_qual |
-- +-------------+----------+----------+----------+
-- | young_leaf  | 83.333   | 70       | 92       |
-- | mature_leaf | 83.200   | 55       | 99       |
-- +-------------+----------+----------+----------+

-- ============================================================
-- pass1.query8
-- Prompt:
-- Inner join fact_calls to sample_dim.
-- For each condition, compute:
-- - call_count
-- - avg_expr_pgr5
-- Return: condition, call_count, avg_expr_pgr5
-- Sort by condition ascending.
-- Round avg_expr_pgr5 to 3 decimals.
SELECT
    s.condition,
    COUNT(*) AS call_count,
    ROUND(AVG(CAST(s.expr_pgr5 AS DECIMAL(18, 6))), 3) AS avg_expr_pgr5
FROM fact_calls AS f
INNER JOIN sample_dim AS s
    ON f.sample_id = s.sample_id
GROUP BY s.condition
ORDER BY s.condition ASC;

-- Expected result:
-- +------------+------------+---------------+
-- | condition  | call_count | avg_expr_pgr5 |
-- +------------+------------+---------------+
-- | control    | 4          | 475.000       |
-- | drought    | 2          | 700.000       |
-- | high_light | 2          | 800.000       |
-- +------------+------------+---------------+
