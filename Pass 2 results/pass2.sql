-- AIBioBench Pass 2 SQL

-- ============================================================
-- pass2.query1
-- Prompt:
-- Inner join across all four tables:
-- fact_calls -> sample_dim
-- fact_calls -> variant_dim -> gene_dim
-- Return: call_id, sample_id, tissue, gene_symbol, impact, genotype
-- Sort by call_id ascending.
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

-- Expected result:
-- +---------+-----------+-------------+-------------+----------+----------+
-- | call_id | sample_id | tissue      | gene_symbol | impact   | genotype |
-- +---------+-----------+-------------+-------------+----------+----------+
-- | 1       | S1        | mature_leaf | NDHB        | moderate | 0/1      |
-- | 2       | S1        | mature_leaf | NDHB        | high     | 1/1      |
-- | 3       | S2        | mature_leaf | NDHB        | moderate | 0/0      |
-- | 4       | S2        | mature_leaf | NDHK        | high     | 0/1      |
-- | 5       | S3        | young_leaf  | PGR5        | low      | 0/1      |
-- | 7       | S4        | young_leaf  | NDHK        | high     | 0/0      |
-- +---------+-----------+-------------+-------------+----------+----------+

-- ============================================================
-- pass2.query2
-- Prompt:
-- Left join fact_calls across the full snowflake.
-- Return: call_id, sample_id, plant_line_id, tissue, variant_id, gene_symbol
-- Keep all fact rows.
-- Sort by call_id ascending.
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

-- Expected result:
-- +---------+-----------+---------------+-------------+------------+-------------+
-- | call_id | sample_id | plant_line_id | tissue      | variant_id | gene_symbol |
-- +---------+-----------+---------------+-------------+------------+-------------+
-- | 1       | S1        | Line_A        | mature_leaf | V1         | NDHB        |
-- | 2       | S1        | Line_A        | mature_leaf | V2         | NDHB        |
-- | 3       | S2        | Line_B        | mature_leaf | V1         | NDHB        |
-- | 4       | S2        | Line_B        | mature_leaf | V3         | NDHK        |
-- | 5       | S3        | Line_C        | young_leaf  | V4         | PGR5        |
-- | 6       | S3        | Line_C        | young_leaf  | V5         | NULL        |
-- | 7       | S4        | Line_D        | young_leaf  | V3         | NDHK        |
-- | 8       | S999      | NULL          | NULL        | V2         | NDHB        |
-- | 9       | S2        | Line_B        | mature_leaf | V999       | NULL        |
-- +---------+-----------+---------------+-------------+------------+-------------+

-- ============================================================
-- pass2.query3
-- Prompt:
-- Perform a FULL OUTER JOIN between fact_calls and variant_dim on variant_id.
-- Return:
-- - variant_id as the coalesced key
-- - call_id
-- - sample_id
-- - impact
-- Sort by variant_id ascending, then call_id ascending.
--
-- Portable FULL OUTER JOIN emulation:
SELECT
    f.variant_id AS variant_id,
    f.call_id,
    f.sample_id,
    v.impact
FROM fact_calls AS f
LEFT JOIN variant_dim AS v
    ON f.variant_id = v.variant_id

UNION ALL

SELECT
    v.variant_id AS variant_id,
    CAST(NULL AS INTEGER) AS call_id,
    CAST(NULL AS VARCHAR(20)) AS sample_id,
    v.impact
FROM variant_dim AS v
LEFT JOIN fact_calls AS f
    ON v.variant_id = f.variant_id
WHERE f.variant_id IS NULL

ORDER BY variant_id ASC, call_id ASC;

-- Expected result:
-- +------------+---------+-----------+----------+
-- | variant_id | call_id | sample_id | impact   |
-- +------------+---------+-----------+----------+
-- | V1         | 1       | S1        | moderate |
-- | V1         | 3       | S2        | moderate |
-- | V2         | 2       | S1        | high     |
-- | V2         | 8       | S999      | high     |
-- | V3         | 4       | S2        | high     |
-- | V3         | 7       | S4        | high     |
-- | V4         | 5       | S3        | low      |
-- | V5         | 6       | S3        | modifier |
-- | V6         | NULL    | NULL      | moderate |
-- | V999       | 9       | S2        | NULL     |
-- +------------+---------+-----------+----------+

-- ============================================================
-- pass2.query4
-- Prompt:
-- Inner join fact_calls to sample_dim and variant_dim.
-- Count calls by condition and impact, and compute average qual.
-- Return: condition, impact, call_count, avg_qual
-- Sort by condition ascending, then impact ascending.
-- Round avg_qual to 3 decimals.
SELECT
    s.condition,
    v.impact,
    COUNT(*) AS call_count,
    ROUND(AVG(CAST(f.qual AS DECIMAL(18, 6))), 3) AS avg_qual
FROM fact_calls AS f
INNER JOIN sample_dim AS s
    ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
GROUP BY
    s.condition,
    v.impact
ORDER BY
    s.condition ASC,
    v.impact ASC;

-- Expected result:
-- +------------+----------+------------+----------+
-- | condition  | impact   | call_count | avg_qual |
-- +------------+----------+------------+----------+
-- | control    | high     | 2          | 84.000   |
-- | control    | moderate | 1          | 95.000   |
-- | drought    | low      | 1          | 70.000   |
-- | drought    | modifier | 1          | 92.000   |
-- | high_light | high     | 1          | 87.000   |
-- | high_light | moderate | 1          | 99.000   |
-- +------------+----------+------------+----------+

-- ============================================================
-- pass2.query5
-- Prompt:
-- Inner join fact_calls to variant_dim and gene_dim.
-- Compute VAF = alt_reads / total_reads.
-- Return average VAF and maximum qual by gene_symbol.
-- Columns: gene_symbol, avg_vaf, max_qual
-- Sort by avg_vaf descending, then gene_symbol ascending.
-- Round avg_vaf to 3 decimals.
SELECT
    g.gene_symbol,
    ROUND(AVG(CAST(f.alt_reads AS DECIMAL(18, 6)) / NULLIF(CAST(f.total_reads AS DECIMAL(18, 6)), 0)), 3) AS avg_vaf,
    MAX(f.qual) AS max_qual
FROM fact_calls AS f
INNER JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
    ON v.gene_id = g.gene_id
GROUP BY g.gene_symbol
ORDER BY avg_vaf DESC, g.gene_symbol ASC;

-- Expected result:
-- +-------------+---------+----------+
-- | gene_symbol | avg_vaf | max_qual |
-- +-------------+---------+----------+
-- | PGR5        | 0.500   | 70       |
-- | NDHB        | 0.459   | 99       |
-- | NDHK        | 0.250   | 88       |
-- +-------------+---------+----------+

-- ============================================================
-- pass2.query6
-- Prompt:
-- Use complete inner joins across all four tables.
-- For each tissue, compute:
-- - distinct_genes
-- - avg_expr_ndhb
-- Return: tissue, distinct_genes, avg_expr_ndhb
-- Sort by tissue ascending.
-- Round avg_expr_ndhb to 3 decimals.
SELECT
    s.tissue,
    COUNT(DISTINCT g.gene_symbol) AS distinct_genes,
    ROUND(AVG(CAST(s.expr_ndhb AS DECIMAL(18, 6))), 3) AS avg_expr_ndhb
FROM fact_calls AS f
INNER JOIN sample_dim AS s
    ON f.sample_id = s.sample_id
INNER JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
    ON v.gene_id = g.gene_id
GROUP BY s.tissue
ORDER BY s.tissue ASC;

-- Expected result:
-- +-------------+----------------+---------------+
-- | tissue      | distinct_genes | avg_expr_ndhb |
-- +-------------+----------------+---------------+
-- | mature_leaf | 2              | 750.000       |
-- | young_leaf  | 2              | 500.000       |
-- +-------------+----------------+---------------+

-- ============================================================
-- pass2.query7
-- Prompt:
-- Use sample_dim as the preserving table.
-- For each sample, count high-impact calls and compute average alt_reads among only high-impact calls.
-- Return: sample_id, tissue, high_impact_call_count, avg_alt_reads_high
-- Include samples with zero high-impact calls.
-- Sort by high_impact_call_count descending, then sample_id ascending.
-- Round avg_alt_reads_high to 3 decimals.
SELECT
    s.sample_id,
    s.tissue,
    COUNT(CASE WHEN v.impact = 'high' THEN 1 END) AS high_impact_call_count,
    ROUND(AVG(CASE WHEN v.impact = 'high' THEN CAST(f.alt_reads AS DECIMAL(18, 6)) END), 3) AS avg_alt_reads_high
FROM sample_dim AS s
LEFT JOIN fact_calls AS f
    ON s.sample_id = f.sample_id
LEFT JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
GROUP BY
    s.sample_id,
    s.tissue
ORDER BY
    high_impact_call_count DESC,
    s.sample_id ASC;

-- Expected result:
-- +-----------+-------------+------------------------+--------------------+
-- | sample_id | tissue      | high_impact_call_count | avg_alt_reads_high |
-- +-----------+-------------+------------------------+--------------------+
-- | S1        | mature_leaf | 1                      | 28.000             |
-- | S2        | mature_leaf | 1                      | 10.000             |
-- | S4        | young_leaf  | 1                      | 0.000              |
-- | S3        | young_leaf  | 0                      | NULL               |
-- | S5        | root        | 0                      | NULL               |
-- +-----------+-------------+------------------------+--------------------+

-- ============================================================
-- pass2.query8
-- Prompt:
-- Inner join fact_calls to variant_dim and gene_dim.
-- For each gene_symbol, compute:
-- - total_alt_reads
-- - avg_qual
-- - max_alt_reads
-- Return: gene_symbol, total_alt_reads, avg_qual, max_alt_reads
-- Sort by total_alt_reads descending, then gene_symbol ascending.
-- Round avg_qual to 3 decimals.
SELECT
    g.gene_symbol,
    SUM(f.alt_reads) AS total_alt_reads,
    ROUND(AVG(CAST(f.qual AS DECIMAL(18, 6))), 3) AS avg_qual,
    MAX(f.alt_reads) AS max_alt_reads
FROM fact_calls AS f
INNER JOIN variant_dim AS v
    ON f.variant_id = v.variant_id
INNER JOIN gene_dim AS g
    ON v.gene_id = g.gene_id
GROUP BY g.gene_symbol
ORDER BY total_alt_reads DESC, g.gene_symbol ASC;

-- Expected result:
-- +-------------+-----------------+----------+---------------+
-- | gene_symbol | total_alt_reads | avg_qual | max_alt_reads |
-- +-------------+-----------------+----------+---------------+
-- | NDHB        | 54              | 85.250   | 28            |
-- | NDHK        | 10              | 84.000   | 10            |
-- | PGR5        | 9               | 70.000   | 9             |
-- +-------------+-----------------+----------+---------------+
