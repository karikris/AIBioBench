# AIBioBench prompts and gold answers

This file lists every benchmark prompt for all 5 passes together with the gold answer table.

## Shared dataset

Schema: `fact_calls -> sample_dim and fact_calls -> variant_dim -> gene_dim`

### fact_calls

|   call_id | sample_id   | variant_id   | genotype   |   alt_reads |   total_reads |   qual |
|----------:|:------------|:-------------|:-----------|------------:|--------------:|-------:|
|         1 | S1          | V1           | 0/1        |          12 |            30 |     99 |
|         2 | S1          | V2           | 1/1        |          28 |            28 |     87 |
|         3 | S2          | V1           | 0/0        |           0 |            26 |     95 |
|         4 | S2          | V3           | 0/1        |          10 |            20 |     80 |
|         5 | S3          | V4           | 0/1        |           9 |            18 |     70 |
|         6 | S3          | V5           | 1/1        |          22 |            22 |     92 |
|         7 | S4          | V3           | 0/0        |           0 |            24 |     88 |
|         8 | S999        | V2           | 0/1        |          14 |            32 |     60 |
|         9 | S2          | V999         | 0/1        |           7 |            21 |     55 |

### sample_dim

| sample_id   | plant_line_id   | tissue      | condition   | batch   |   expr_ndhb |   expr_pgr5 |   expr_ndhk |
|:------------|:----------------|:------------|:------------|:--------|------------:|------------:|------------:|
| S1          | Line_A          | mature_leaf | high_light  | B1      |        1200 |         800 |         150 |
| S2          | Line_B          | mature_leaf | control     | B1      |         300 |         500 |          90 |
| S3          | Line_C          | young_leaf  | drought     | B2      |         900 |         700 |         110 |
| S4          | Line_D          | young_leaf  | control     | B2      |         100 |         400 |          50 |
| S5          | Line_E          | root        | high_light  | B3      |          20 |          30 |           5 |

### variant_dim

| variant_id   | gene_id   | chrom   |    pos | variant_class   | impact   |
|:-------------|:----------|:--------|-------:|:----------------|:---------|
| V1           | G1        | cpDNA   |  11452 | SNV             | moderate |
| V2           | G1        | cpDNA   |  11477 | indel           | high     |
| V3           | G2        | cpDNA   |  12345 | SNV             | high     |
| V4           | G3        | Chr2    | 987654 | SNV             | low      |
| V5           | G999      | cpDNA   |  12888 | SNV             | modifier |
| V6           | G4        | cpDNA   |  13001 | indel           | moderate |

### gene_dim

| gene_id   | gene_symbol   | pathway                 | gene_role        |
|:----------|:--------------|:------------------------|:-----------------|
| G1        | NDHB          | chloroplast_NDH_complex | ndh_membrane_arm |
| G2        | NDHK          | chloroplast_NDH_complex | ndh_membrane_arm |
| G3        | PGR5          | cyclic_electron_flow    | pgr_regulator    |
| G4        | NDHT          | chlororespiration       | ndh_lumen_module |
| G5        | PGR1B         | PSI_photoprotection     | pgr_regulator    |

## Standard instructions

### sql_v1

```text
You are given four CSV tables in a snowflake schema:

fact_calls
├── sample_dim
└── variant_dim
    └── gene_dim

Rules:
1. Use ANSI SQL.
2. Show the SQL first, then show the final result table.
3. Use NULL for missing values.
4. Preserve the exact requested sort order.
5. Round derived decimal values to 3 decimals.
6. If your SQL dialect does not support RIGHT JOIN, use an equivalent reversed LEFT JOIN.
7. If your SQL dialect does not support FULL OUTER JOIN, emulate it correctly.
8. Do not invent rows or columns.
9. Unless explicitly stated otherwise, summaries that follow a join should be computed over the joined rows, not over distinct source rows.
```

### python_v1

```text
You are given four CSV tables in a snowflake schema:

fact_calls
├── sample_dim
└── variant_dim
    └── gene_dim

Rules:
1. Use Python with pandas and numpy only.
2. Show the Python code first, then show the final result table.
3. Use NaN/None in code, but present missing values as NULL in the final table.
4. Preserve the exact requested sort order.
5. Round derived decimal values to 3 decimals.
6. Use numpy.log2(x + 1) for all requested log transforms.
7. When a task requests matched expression by gene_symbol, use this mapping:
   - NDHB -> expr_ndhb
   - NDHK -> expr_ndhk
   - PGR5 -> expr_pgr5
   - all other genes -> NULL
8. When a task requests standard deviation or coefficient of variation, use population standard deviation with ddof=0 unless the prompt says otherwise.
9. Do not invent rows or columns.
```

## pass1.query1

- pass: 1
- language: sql
- difficulty: easy
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join fact_calls to sample_dim on sample_id.
Return: call_id, sample_id, tissue, condition, genotype
Sort by call_id ascending.
```

### Gold answer

|   call_id | sample_id   | tissue      | condition   | genotype   |
|----------:|:------------|:------------|:------------|:-----------|
|         1 | S1          | mature_leaf | high_light  | 0/1        |
|         2 | S1          | mature_leaf | high_light  | 1/1        |
|         3 | S2          | mature_leaf | control     | 0/0        |
|         4 | S2          | mature_leaf | control     | 0/1        |
|         5 | S3          | young_leaf  | drought     | 0/1        |
|         6 | S3          | young_leaf  | drought     | 1/1        |
|         7 | S4          | young_leaf  | control     | 0/0        |
|         9 | S2          | mature_leaf | control     | 0/1        |

### JSON answer

```json
{
  "case_id": "pass1.query1",
  "columns": [
    "call_id",
    "sample_id",
    "tissue",
    "condition",
    "genotype"
  ],
  "rows": [
    [
      1,
      "S1",
      "mature_leaf",
      "high_light",
      "0/1"
    ],
    [
      2,
      "S1",
      "mature_leaf",
      "high_light",
      "1/1"
    ],
    [
      3,
      "S2",
      "mature_leaf",
      "control",
      "0/0"
    ],
    [
      4,
      "S2",
      "mature_leaf",
      "control",
      "0/1"
    ],
    [
      5,
      "S3",
      "young_leaf",
      "drought",
      "0/1"
    ],
    [
      6,
      "S3",
      "young_leaf",
      "drought",
      "1/1"
    ],
    [
      7,
      "S4",
      "young_leaf",
      "control",
      "0/0"
    ],
    [
      9,
      "S2",
      "mature_leaf",
      "control",
      "0/1"
    ]
  ]
}
```

## pass1.query2

- pass: 1
- language: sql
- difficulty: easy
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join fact_calls to variant_dim on variant_id.
Return: call_id, variant_id, variant_class, impact, qual
Sort by qual descending, then call_id ascending.
```

### Gold answer

|   call_id | variant_id   | variant_class   | impact   |   qual |
|----------:|:-------------|:----------------|:---------|-------:|
|         1 | V1           | SNV             | moderate |     99 |
|         3 | V1           | SNV             | moderate |     95 |
|         6 | V5           | SNV             | modifier |     92 |
|         7 | V3           | SNV             | high     |     88 |
|         2 | V2           | indel           | high     |     87 |
|         4 | V3           | SNV             | high     |     80 |
|         5 | V4           | SNV             | low      |     70 |
|         8 | V2           | indel           | high     |     60 |

### JSON answer

```json
{
  "case_id": "pass1.query2",
  "columns": [
    "call_id",
    "variant_id",
    "variant_class",
    "impact",
    "qual"
  ],
  "rows": [
    [
      1,
      "V1",
      "SNV",
      "moderate",
      99
    ],
    [
      3,
      "V1",
      "SNV",
      "moderate",
      95
    ],
    [
      6,
      "V5",
      "SNV",
      "modifier",
      92
    ],
    [
      7,
      "V3",
      "SNV",
      "high",
      88
    ],
    [
      2,
      "V2",
      "indel",
      "high",
      87
    ],
    [
      4,
      "V3",
      "SNV",
      "high",
      80
    ],
    [
      5,
      "V4",
      "SNV",
      "low",
      70
    ],
    [
      8,
      "V2",
      "indel",
      "high",
      60
    ]
  ]
}
```

## pass1.query3

- pass: 1
- language: sql
- difficulty: easy
- standard_instructions_id: sql_v1

### Prompt

```text
Left join fact_calls to sample_dim on sample_id.
Return: call_id, sample_id, tissue, batch, expr_ndhb
Keep all fact rows.
Sort by call_id ascending.
```

### Gold answer

|   call_id | sample_id   | tissue      | batch   |   expr_ndhb |
|----------:|:------------|:------------|:--------|------------:|
|         1 | S1          | mature_leaf | B1      |        1200 |
|         2 | S1          | mature_leaf | B1      |        1200 |
|         3 | S2          | mature_leaf | B1      |         300 |
|         4 | S2          | mature_leaf | B1      |         300 |
|         5 | S3          | young_leaf  | B2      |         900 |
|         6 | S3          | young_leaf  | B2      |         900 |
|         7 | S4          | young_leaf  | B2      |         100 |
|         8 | S999        |             |         |         nan |
|         9 | S2          | mature_leaf | B1      |         300 |

### JSON answer

```json
{
  "case_id": "pass1.query3",
  "columns": [
    "call_id",
    "sample_id",
    "tissue",
    "batch",
    "expr_ndhb"
  ],
  "rows": [
    [
      1,
      "S1",
      "mature_leaf",
      "B1",
      1200.0
    ],
    [
      2,
      "S1",
      "mature_leaf",
      "B1",
      1200.0
    ],
    [
      3,
      "S2",
      "mature_leaf",
      "B1",
      300.0
    ],
    [
      4,
      "S2",
      "mature_leaf",
      "B1",
      300.0
    ],
    [
      5,
      "S3",
      "young_leaf",
      "B2",
      900.0
    ],
    [
      6,
      "S3",
      "young_leaf",
      "B2",
      900.0
    ],
    [
      7,
      "S4",
      "young_leaf",
      "B2",
      100.0
    ],
    [
      8,
      "S999",
      null,
      null,
      null
    ],
    [
      9,
      "S2",
      "mature_leaf",
      "B1",
      300.0
    ]
  ]
}
```

## pass1.query4

- pass: 1
- language: sql
- difficulty: easy
- standard_instructions_id: sql_v1

### Prompt

```text
Use a RIGHT JOIN from fact_calls to sample_dim, or an equivalent reversed LEFT JOIN.
Return one row per sample with:
sample_id, tissue, call_count, avg_qual
Include samples with zero calls.
Sort by sample_id ascending.
Round avg_qual to 3 decimals.
```

### Gold answer

| sample_id   | tissue      |   call_count |   avg_qual |
|:------------|:------------|-------------:|-----------:|
| S1          | mature_leaf |            2 |     93     |
| S2          | mature_leaf |            3 |     76.667 |
| S3          | young_leaf  |            2 |     81     |
| S4          | young_leaf  |            1 |     88     |
| S5          | root        |            0 |    nan     |

### JSON answer

```json
{
  "case_id": "pass1.query4",
  "columns": [
    "sample_id",
    "tissue",
    "call_count",
    "avg_qual"
  ],
  "rows": [
    [
      "S1",
      "mature_leaf",
      2,
      93.0
    ],
    [
      "S2",
      "mature_leaf",
      3,
      76.667
    ],
    [
      "S3",
      "young_leaf",
      2,
      81.0
    ],
    [
      "S4",
      "young_leaf",
      1,
      88.0
    ],
    [
      "S5",
      "root",
      0,
      null
    ]
  ]
}
```

## pass1.query5

- pass: 1
- language: sql
- difficulty: easy
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join fact_calls to variant_dim, then to gene_dim.
Return: call_id, variant_id, gene_symbol, pathway
Sort by call_id ascending.
```

### Gold answer

|   call_id | variant_id   | gene_symbol   | pathway                 |
|----------:|:-------------|:--------------|:------------------------|
|         1 | V1           | NDHB          | chloroplast_NDH_complex |
|         2 | V2           | NDHB          | chloroplast_NDH_complex |
|         3 | V1           | NDHB          | chloroplast_NDH_complex |
|         4 | V3           | NDHK          | chloroplast_NDH_complex |
|         5 | V4           | PGR5          | cyclic_electron_flow    |
|         7 | V3           | NDHK          | chloroplast_NDH_complex |
|         8 | V2           | NDHB          | chloroplast_NDH_complex |

### JSON answer

```json
{
  "case_id": "pass1.query5",
  "columns": [
    "call_id",
    "variant_id",
    "gene_symbol",
    "pathway"
  ],
  "rows": [
    [
      1,
      "V1",
      "NDHB",
      "chloroplast_NDH_complex"
    ],
    [
      2,
      "V2",
      "NDHB",
      "chloroplast_NDH_complex"
    ],
    [
      3,
      "V1",
      "NDHB",
      "chloroplast_NDH_complex"
    ],
    [
      4,
      "V3",
      "NDHK",
      "chloroplast_NDH_complex"
    ],
    [
      5,
      "V4",
      "PGR5",
      "cyclic_electron_flow"
    ],
    [
      7,
      "V3",
      "NDHK",
      "chloroplast_NDH_complex"
    ],
    [
      8,
      "V2",
      "NDHB",
      "chloroplast_NDH_complex"
    ]
  ]
}
```

## pass1.query6

- pass: 1
- language: sql
- difficulty: easy
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join fact_calls to variant_dim.
Count calls by impact and also compute average qual.
Return: impact, call_count, avg_qual
Sort by call_count descending, then impact ascending.
Round avg_qual to 3 decimals.
```

### Gold answer

| impact   |   call_count |   avg_qual |
|:---------|-------------:|-----------:|
| high     |            4 |      78.75 |
| moderate |            2 |      97    |
| low      |            1 |      70    |
| modifier |            1 |      92    |

### JSON answer

```json
{
  "case_id": "pass1.query6",
  "columns": [
    "impact",
    "call_count",
    "avg_qual"
  ],
  "rows": [
    [
      "high",
      4,
      78.75
    ],
    [
      "moderate",
      2,
      97.0
    ],
    [
      "low",
      1,
      70.0
    ],
    [
      "modifier",
      1,
      92.0
    ]
  ]
}
```

## pass1.query7

- pass: 1
- language: sql
- difficulty: easy
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join fact_calls to sample_dim.
Compute average, minimum, and maximum qual by tissue.
Return: tissue, avg_qual, min_qual, max_qual
Sort by avg_qual descending.
Round avg_qual to 3 decimals.
```

### Gold answer

| tissue      |   avg_qual |   min_qual |   max_qual |
|:------------|-----------:|-----------:|-----------:|
| young_leaf  |     83.333 |         70 |         92 |
| mature_leaf |     83.2   |         55 |         99 |

### JSON answer

```json
{
  "case_id": "pass1.query7",
  "columns": [
    "tissue",
    "avg_qual",
    "min_qual",
    "max_qual"
  ],
  "rows": [
    [
      "young_leaf",
      83.333,
      70,
      92
    ],
    [
      "mature_leaf",
      83.2,
      55,
      99
    ]
  ]
}
```

## pass1.query8

- pass: 1
- language: sql
- difficulty: easy
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join fact_calls to sample_dim.
For each condition, compute:
- call_count
- avg_expr_pgr5

Return: condition, call_count, avg_expr_pgr5
Sort by condition ascending.
Round avg_expr_pgr5 to 3 decimals.
```

### Gold answer

| condition   |   call_count |   avg_expr_pgr5 |
|:------------|-------------:|----------------:|
| control     |            4 |             475 |
| drought     |            2 |             700 |
| high_light  |            2 |             800 |

### JSON answer

```json
{
  "case_id": "pass1.query8",
  "columns": [
    "condition",
    "call_count",
    "avg_expr_pgr5"
  ],
  "rows": [
    [
      "control",
      4,
      475.0
    ],
    [
      "drought",
      2,
      700.0
    ],
    [
      "high_light",
      2,
      800.0
    ]
  ]
}
```

## pass2.query1

- pass: 2
- language: sql
- difficulty: medium
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join across all four tables:
fact_calls -> sample_dim
fact_calls -> variant_dim -> gene_dim

Return: call_id, sample_id, tissue, gene_symbol, impact, genotype
Sort by call_id ascending.
```

### Gold answer

|   call_id | sample_id   | tissue      | gene_symbol   | impact   | genotype   |
|----------:|:------------|:------------|:--------------|:---------|:-----------|
|         1 | S1          | mature_leaf | NDHB          | moderate | 0/1        |
|         2 | S1          | mature_leaf | NDHB          | high     | 1/1        |
|         3 | S2          | mature_leaf | NDHB          | moderate | 0/0        |
|         4 | S2          | mature_leaf | NDHK          | high     | 0/1        |
|         5 | S3          | young_leaf  | PGR5          | low      | 0/1        |
|         7 | S4          | young_leaf  | NDHK          | high     | 0/0        |

### JSON answer

```json
{
  "case_id": "pass2.query1",
  "columns": [
    "call_id",
    "sample_id",
    "tissue",
    "gene_symbol",
    "impact",
    "genotype"
  ],
  "rows": [
    [
      1,
      "S1",
      "mature_leaf",
      "NDHB",
      "moderate",
      "0/1"
    ],
    [
      2,
      "S1",
      "mature_leaf",
      "NDHB",
      "high",
      "1/1"
    ],
    [
      3,
      "S2",
      "mature_leaf",
      "NDHB",
      "moderate",
      "0/0"
    ],
    [
      4,
      "S2",
      "mature_leaf",
      "NDHK",
      "high",
      "0/1"
    ],
    [
      5,
      "S3",
      "young_leaf",
      "PGR5",
      "low",
      "0/1"
    ],
    [
      7,
      "S4",
      "young_leaf",
      "NDHK",
      "high",
      "0/0"
    ]
  ]
}
```

## pass2.query2

- pass: 2
- language: sql
- difficulty: medium
- standard_instructions_id: sql_v1

### Prompt

```text
Left join fact_calls across the full snowflake.
Return: call_id, sample_id, plant_line_id, tissue, variant_id, gene_symbol
Keep all fact rows.
Sort by call_id ascending.
```

### Gold answer

|   call_id | sample_id   | plant_line_id   | tissue      | variant_id   | gene_symbol   |
|----------:|:------------|:----------------|:------------|:-------------|:--------------|
|         1 | S1          | Line_A          | mature_leaf | V1           | NDHB          |
|         2 | S1          | Line_A          | mature_leaf | V2           | NDHB          |
|         3 | S2          | Line_B          | mature_leaf | V1           | NDHB          |
|         4 | S2          | Line_B          | mature_leaf | V3           | NDHK          |
|         5 | S3          | Line_C          | young_leaf  | V4           | PGR5          |
|         6 | S3          | Line_C          | young_leaf  | V5           |               |
|         7 | S4          | Line_D          | young_leaf  | V3           | NDHK          |
|         8 | S999        |                 |             | V2           | NDHB          |
|         9 | S2          | Line_B          | mature_leaf | V999         |               |

### JSON answer

```json
{
  "case_id": "pass2.query2",
  "columns": [
    "call_id",
    "sample_id",
    "plant_line_id",
    "tissue",
    "variant_id",
    "gene_symbol"
  ],
  "rows": [
    [
      1,
      "S1",
      "Line_A",
      "mature_leaf",
      "V1",
      "NDHB"
    ],
    [
      2,
      "S1",
      "Line_A",
      "mature_leaf",
      "V2",
      "NDHB"
    ],
    [
      3,
      "S2",
      "Line_B",
      "mature_leaf",
      "V1",
      "NDHB"
    ],
    [
      4,
      "S2",
      "Line_B",
      "mature_leaf",
      "V3",
      "NDHK"
    ],
    [
      5,
      "S3",
      "Line_C",
      "young_leaf",
      "V4",
      "PGR5"
    ],
    [
      6,
      "S3",
      "Line_C",
      "young_leaf",
      "V5",
      null
    ],
    [
      7,
      "S4",
      "Line_D",
      "young_leaf",
      "V3",
      "NDHK"
    ],
    [
      8,
      "S999",
      null,
      null,
      "V2",
      "NDHB"
    ],
    [
      9,
      "S2",
      "Line_B",
      "mature_leaf",
      "V999",
      null
    ]
  ]
}
```

## pass2.query3

- pass: 2
- language: sql
- difficulty: medium
- standard_instructions_id: sql_v1

### Prompt

```text
Perform a FULL OUTER JOIN between fact_calls and variant_dim on variant_id.
Return:
- variant_id as the coalesced key
- call_id
- sample_id
- impact

Sort by variant_id ascending, then call_id ascending.
```

### Gold answer

| variant_id   |   call_id | sample_id   | impact   |
|:-------------|----------:|:------------|:---------|
| V1           |         1 | S1          | moderate |
| V1           |         3 | S2          | moderate |
| V2           |         2 | S1          | high     |
| V2           |         8 | S999        | high     |
| V3           |         4 | S2          | high     |
| V3           |         7 | S4          | high     |
| V4           |         5 | S3          | low      |
| V5           |         6 | S3          | modifier |
| V6           |       nan |             | moderate |
| V999         |         9 | S2          |          |

### JSON answer

```json
{
  "case_id": "pass2.query3",
  "columns": [
    "variant_id",
    "call_id",
    "sample_id",
    "impact"
  ],
  "rows": [
    [
      "V1",
      1,
      "S1",
      "moderate"
    ],
    [
      "V1",
      3,
      "S2",
      "moderate"
    ],
    [
      "V2",
      2,
      "S1",
      "high"
    ],
    [
      "V2",
      8,
      "S999",
      "high"
    ],
    [
      "V3",
      4,
      "S2",
      "high"
    ],
    [
      "V3",
      7,
      "S4",
      "high"
    ],
    [
      "V4",
      5,
      "S3",
      "low"
    ],
    [
      "V5",
      6,
      "S3",
      "modifier"
    ],
    [
      "V6",
      null,
      null,
      "moderate"
    ],
    [
      "V999",
      9,
      "S2",
      null
    ]
  ]
}
```

## pass2.query4

- pass: 2
- language: sql
- difficulty: medium
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join fact_calls to sample_dim and variant_dim.
Count calls by condition and impact, and compute average qual.
Return: condition, impact, call_count, avg_qual
Sort by condition ascending, then impact ascending.
Round avg_qual to 3 decimals.
```

### Gold answer

| condition   | impact   |   call_count |   avg_qual |
|:------------|:---------|-------------:|-----------:|
| control     | high     |            2 |         84 |
| control     | moderate |            1 |         95 |
| drought     | low      |            1 |         70 |
| drought     | modifier |            1 |         92 |
| high_light  | high     |            1 |         87 |
| high_light  | moderate |            1 |         99 |

### JSON answer

```json
{
  "case_id": "pass2.query4",
  "columns": [
    "condition",
    "impact",
    "call_count",
    "avg_qual"
  ],
  "rows": [
    [
      "control",
      "high",
      2,
      84.0
    ],
    [
      "control",
      "moderate",
      1,
      95.0
    ],
    [
      "drought",
      "low",
      1,
      70.0
    ],
    [
      "drought",
      "modifier",
      1,
      92.0
    ],
    [
      "high_light",
      "high",
      1,
      87.0
    ],
    [
      "high_light",
      "moderate",
      1,
      99.0
    ]
  ]
}
```

## pass2.query5

- pass: 2
- language: sql
- difficulty: medium
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join fact_calls to variant_dim and gene_dim.
Compute VAF = alt_reads / total_reads.
Return average VAF and maximum qual by gene_symbol.
Columns: gene_symbol, avg_vaf, max_qual
Sort by avg_vaf descending, then gene_symbol ascending.
Round avg_vaf to 3 decimals.
```

### Gold answer

| gene_symbol   |   avg_vaf |   max_qual |
|:--------------|----------:|-----------:|
| PGR5          |     0.5   |         70 |
| NDHB          |     0.459 |         99 |
| NDHK          |     0.25  |         88 |

### JSON answer

```json
{
  "case_id": "pass2.query5",
  "columns": [
    "gene_symbol",
    "avg_vaf",
    "max_qual"
  ],
  "rows": [
    [
      "PGR5",
      0.5,
      70
    ],
    [
      "NDHB",
      0.459,
      99
    ],
    [
      "NDHK",
      0.25,
      88
    ]
  ]
}
```

## pass2.query6

- pass: 2
- language: sql
- difficulty: medium
- standard_instructions_id: sql_v1

### Prompt

```text
Use complete inner joins across all four tables.
For each tissue, compute:
- distinct_genes
- avg_expr_ndhb

Return: tissue, distinct_genes, avg_expr_ndhb
Sort by tissue ascending.
Round avg_expr_ndhb to 3 decimals.
```

### Gold answer

| tissue      |   distinct_genes |   avg_expr_ndhb |
|:------------|-----------------:|----------------:|
| mature_leaf |                2 |             750 |
| young_leaf  |                2 |             500 |

### JSON answer

```json
{
  "case_id": "pass2.query6",
  "columns": [
    "tissue",
    "distinct_genes",
    "avg_expr_ndhb"
  ],
  "rows": [
    [
      "mature_leaf",
      2,
      750.0
    ],
    [
      "young_leaf",
      2,
      500.0
    ]
  ]
}
```

## pass2.query7

- pass: 2
- language: sql
- difficulty: medium
- standard_instructions_id: sql_v1

### Prompt

```text
Use sample_dim as the preserving table.
For each sample, count high-impact calls and compute average alt_reads among only high-impact calls.
Return: sample_id, tissue, high_impact_call_count, avg_alt_reads_high
Include samples with zero high-impact calls.
Sort by high_impact_call_count descending, then sample_id ascending.
Round avg_alt_reads_high to 3 decimals.
```

### Gold answer

| sample_id   | tissue      |   high_impact_call_count |   avg_alt_reads_high |
|:------------|:------------|-------------------------:|---------------------:|
| S1          | mature_leaf |                        1 |                   28 |
| S2          | mature_leaf |                        1 |                   10 |
| S4          | young_leaf  |                        1 |                    0 |
| S3          | young_leaf  |                        0 |                  nan |
| S5          | root        |                        0 |                  nan |

### JSON answer

```json
{
  "case_id": "pass2.query7",
  "columns": [
    "sample_id",
    "tissue",
    "high_impact_call_count",
    "avg_alt_reads_high"
  ],
  "rows": [
    [
      "S1",
      "mature_leaf",
      1,
      28.0
    ],
    [
      "S2",
      "mature_leaf",
      1,
      10.0
    ],
    [
      "S4",
      "young_leaf",
      1,
      0.0
    ],
    [
      "S3",
      "young_leaf",
      0,
      null
    ],
    [
      "S5",
      "root",
      0,
      null
    ]
  ]
}
```

## pass2.query8

- pass: 2
- language: sql
- difficulty: medium
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join fact_calls to variant_dim and gene_dim.
For each gene_symbol, compute:
- total_alt_reads
- avg_qual
- max_alt_reads

Return: gene_symbol, total_alt_reads, avg_qual, max_alt_reads
Sort by total_alt_reads descending, then gene_symbol ascending.
Round avg_qual to 3 decimals.
```

### Gold answer

| gene_symbol   |   total_alt_reads |   avg_qual |   max_alt_reads |
|:--------------|------------------:|-----------:|----------------:|
| NDHB          |                54 |      85.25 |              28 |
| NDHK          |                10 |      84    |              10 |
| PGR5          |                 9 |      70    |               9 |

### JSON answer

```json
{
  "case_id": "pass2.query8",
  "columns": [
    "gene_symbol",
    "total_alt_reads",
    "avg_qual",
    "max_alt_reads"
  ],
  "rows": [
    [
      "NDHB",
      54,
      85.25,
      28
    ],
    [
      "NDHK",
      10,
      84.0,
      10
    ],
    [
      "PGR5",
      9,
      70.0,
      9
    ]
  ]
}
```

## pass3.query1

- pass: 3
- language: sql
- difficulty: hard
- standard_instructions_id: sql_v1

### Prompt

```text
Left join fact_calls across the full snowflake and classify each fact row into one join_status using this logic:

- COMPLETE_CHAIN: sample, variant, and gene all matched
- MISSING_SAMPLE: sample missing but variant and gene matched
- MISSING_GENE: variant matched but gene missing
- MISSING_VARIANT: variant missing

Return: call_id, sample_id, variant_id, join_status
Sort by call_id ascending.
```

### Gold answer

|   call_id | sample_id   | variant_id   | join_status     |
|----------:|:------------|:-------------|:----------------|
|         1 | S1          | V1           | COMPLETE_CHAIN  |
|         2 | S1          | V2           | COMPLETE_CHAIN  |
|         3 | S2          | V1           | COMPLETE_CHAIN  |
|         4 | S2          | V3           | COMPLETE_CHAIN  |
|         5 | S3          | V4           | COMPLETE_CHAIN  |
|         6 | S3          | V5           | MISSING_GENE    |
|         7 | S4          | V3           | COMPLETE_CHAIN  |
|         8 | S999        | V2           | MISSING_SAMPLE  |
|         9 | S2          | V999         | MISSING_VARIANT |

### JSON answer

```json
{
  "case_id": "pass3.query1",
  "columns": [
    "call_id",
    "sample_id",
    "variant_id",
    "join_status"
  ],
  "rows": [
    [
      1,
      "S1",
      "V1",
      "COMPLETE_CHAIN"
    ],
    [
      2,
      "S1",
      "V2",
      "COMPLETE_CHAIN"
    ],
    [
      3,
      "S2",
      "V1",
      "COMPLETE_CHAIN"
    ],
    [
      4,
      "S2",
      "V3",
      "COMPLETE_CHAIN"
    ],
    [
      5,
      "S3",
      "V4",
      "COMPLETE_CHAIN"
    ],
    [
      6,
      "S3",
      "V5",
      "MISSING_GENE"
    ],
    [
      7,
      "S4",
      "V3",
      "COMPLETE_CHAIN"
    ],
    [
      8,
      "S999",
      "V2",
      "MISSING_SAMPLE"
    ],
    [
      9,
      "S2",
      "V999",
      "MISSING_VARIANT"
    ]
  ]
}
```

## pass3.query2

- pass: 3
- language: sql
- difficulty: hard
- standard_instructions_id: sql_v1

### Prompt

```text
Using only complete-chain matched rows, group by tissue and gene_symbol.
Compute:
- call_count
- sum_alt_reads
- avg_vaf where VAF = alt_reads / total_reads
- max_qual

Return: tissue, gene_symbol, call_count, sum_alt_reads, avg_vaf, max_qual
Sort by tissue ascending, then gene_symbol ascending.
Round avg_vaf to 3 decimals.
```

### Gold answer

| tissue      | gene_symbol   |   call_count |   sum_alt_reads |   avg_vaf |   max_qual |
|:------------|:--------------|-------------:|----------------:|----------:|-----------:|
| mature_leaf | NDHB          |            3 |              40 |     0.467 |         99 |
| mature_leaf | NDHK          |            1 |              10 |     0.5   |         80 |
| young_leaf  | NDHK          |            1 |               0 |     0     |         88 |
| young_leaf  | PGR5          |            1 |               9 |     0.5   |         70 |

### JSON answer

```json
{
  "case_id": "pass3.query2",
  "columns": [
    "tissue",
    "gene_symbol",
    "call_count",
    "sum_alt_reads",
    "avg_vaf",
    "max_qual"
  ],
  "rows": [
    [
      "mature_leaf",
      "NDHB",
      3,
      40,
      0.467,
      99
    ],
    [
      "mature_leaf",
      "NDHK",
      1,
      10,
      0.5,
      80
    ],
    [
      "young_leaf",
      "NDHK",
      1,
      0,
      0.0,
      88
    ],
    [
      "young_leaf",
      "PGR5",
      1,
      9,
      0.5,
      70
    ]
  ]
}
```

## pass3.query3

- pass: 3
- language: sql
- difficulty: hard
- standard_instructions_id: sql_v1

### Prompt

```text
Start from gene_dim and left join to variant_dim, then fact_calls.
Return one row per gene with:
gene_symbol, pathway, observed_call_count, total_alt_reads

Count matched fact rows per gene.
Include genes with zero observed calls.
Sort by observed_call_count descending, then gene_symbol ascending.
Round total_alt_reads to 3 decimals if needed.
```

### Gold answer

| gene_symbol   | pathway                 |   observed_call_count |   total_alt_reads |
|:--------------|:------------------------|----------------------:|------------------:|
| NDHB          | chloroplast_NDH_complex |                     4 |                54 |
| NDHK          | chloroplast_NDH_complex |                     2 |                10 |
| PGR5          | cyclic_electron_flow    |                     1 |                 9 |
| NDHT          | chlororespiration       |                     0 |                 0 |
| PGR1B         | PSI_photoprotection     |                     0 |                 0 |

### JSON answer

```json
{
  "case_id": "pass3.query3",
  "columns": [
    "gene_symbol",
    "pathway",
    "observed_call_count",
    "total_alt_reads"
  ],
  "rows": [
    [
      "NDHB",
      "chloroplast_NDH_complex",
      4,
      54.0
    ],
    [
      "NDHK",
      "chloroplast_NDH_complex",
      2,
      10.0
    ],
    [
      "PGR5",
      "cyclic_electron_flow",
      1,
      9.0
    ],
    [
      "NDHT",
      "chlororespiration",
      0,
      0.0
    ],
    [
      "PGR1B",
      "PSI_photoprotection",
      0,
      0.0
    ]
  ]
}
```

## pass3.query4

- pass: 3
- language: sql
- difficulty: hard
- standard_instructions_id: sql_v1

### Prompt

```text
Inner join fact_calls to sample_dim and variant_dim.
Filter to impact = 'high'.
For each condition, compute:
- high_impact_call_count
- avg_qual
- avg_alt_reads

Return: condition, high_impact_call_count, avg_qual, avg_alt_reads
Sort by condition ascending.
Round decimal outputs to 3 decimals.
```

### Gold answer

| condition   |   high_impact_call_count |   avg_qual |   avg_alt_reads |
|:------------|-------------------------:|-----------:|----------------:|
| control     |                        2 |         84 |               5 |
| high_light  |                        1 |         87 |              28 |

### JSON answer

```json
{
  "case_id": "pass3.query4",
  "columns": [
    "condition",
    "high_impact_call_count",
    "avg_qual",
    "avg_alt_reads"
  ],
  "rows": [
    [
      "control",
      2,
      84.0,
      5.0
    ],
    [
      "high_light",
      1,
      87.0,
      28.0
    ]
  ]
}
```

## pass3.query5

- pass: 3
- language: sql
- difficulty: hard
- standard_instructions_id: sql_v1

### Prompt

```text
Using sample_dim as the preserving table, count genotype classes per sample.
Compute:
- heterozygous_calls where genotype = '0/1'
- homozygous_alt_calls where genotype = '1/1'
- mean_nonref_qual over only non-reference calls where genotype in ('0/1','1/1')

Return: sample_id, heterozygous_calls, homozygous_alt_calls, mean_nonref_qual
Include samples with zero calls.
Sort by sample_id ascending.
Round mean_nonref_qual to 3 decimals.
```

### Gold answer

| sample_id   |   heterozygous_calls |   homozygous_alt_calls |   mean_nonref_qual |
|:------------|---------------------:|-----------------------:|-------------------:|
| S1          |                    1 |                      1 |               93   |
| S2          |                    2 |                      0 |               67.5 |
| S3          |                    1 |                      1 |               81   |
| S4          |                    0 |                      0 |              nan   |
| S5          |                    0 |                      0 |              nan   |

### JSON answer

```json
{
  "case_id": "pass3.query5",
  "columns": [
    "sample_id",
    "heterozygous_calls",
    "homozygous_alt_calls",
    "mean_nonref_qual"
  ],
  "rows": [
    [
      "S1",
      1,
      1,
      93.0
    ],
    [
      "S2",
      2,
      0,
      67.5
    ],
    [
      "S3",
      1,
      1,
      81.0
    ],
    [
      "S4",
      0,
      0,
      null
    ],
    [
      "S5",
      0,
      0,
      null
    ]
  ]
}
```

## pass3.query6

- pass: 3
- language: sql
- difficulty: hard
- standard_instructions_id: sql_v1

### Prompt

```text
Using only complete-chain matched rows, compute total_alt_reads and avg_vaf by tissue and gene_symbol.
Within each tissue, rank genes by total_alt_reads descending using dense rank.
Return: tissue, gene_symbol, total_alt_reads, avg_vaf, rank_in_tissue
Sort by tissue ascending, then rank_in_tissue ascending, then gene_symbol ascending.
Round avg_vaf to 3 decimals.
```

### Gold answer

| tissue      | gene_symbol   |   total_alt_reads |   avg_vaf |   rank_in_tissue |
|:------------|:--------------|------------------:|----------:|-----------------:|
| mature_leaf | NDHB          |                40 |     0.467 |                1 |
| mature_leaf | NDHK          |                10 |     0.5   |                2 |
| young_leaf  | PGR5          |                 9 |     0.5   |                1 |
| young_leaf  | NDHK          |                 0 |     0     |                2 |

### JSON answer

```json
{
  "case_id": "pass3.query6",
  "columns": [
    "tissue",
    "gene_symbol",
    "total_alt_reads",
    "avg_vaf",
    "rank_in_tissue"
  ],
  "rows": [
    [
      "mature_leaf",
      "NDHB",
      40,
      0.467,
      1
    ],
    [
      "mature_leaf",
      "NDHK",
      10,
      0.5,
      2
    ],
    [
      "young_leaf",
      "PGR5",
      9,
      0.5,
      1
    ],
    [
      "young_leaf",
      "NDHK",
      0,
      0.0,
      2
    ]
  ]
}
```

## pass3.query7

- pass: 3
- language: sql
- difficulty: hard
- standard_instructions_id: sql_v1

### Prompt

```text
Find unused dimension rows across both branches using anti-join logic.
Return: object_type, object_id, reason

Use these rules:
- sample_dim rows with no fact_calls => no_fact_calls
- variant_dim rows with no fact_calls => no_fact_calls
- gene_dim rows with variants but no fact_calls through those variants => no_fact_calls_through_variants
- gene_dim rows with no variants at all => no_variants_attached

Sort by object_type ascending, then object_id ascending.
```

### Gold answer

| object_type   | object_id   | reason                         |
|:--------------|:------------|:-------------------------------|
| gene          | G4          | no_fact_calls_through_variants |
| gene          | G5          | no_variants_attached           |
| sample        | S5          | no_fact_calls                  |
| variant       | V6          | no_fact_calls                  |

### JSON answer

```json
{
  "case_id": "pass3.query7",
  "columns": [
    "object_type",
    "object_id",
    "reason"
  ],
  "rows": [
    [
      "gene",
      "G4",
      "no_fact_calls_through_variants"
    ],
    [
      "gene",
      "G5",
      "no_variants_attached"
    ],
    [
      "sample",
      "S5",
      "no_fact_calls"
    ],
    [
      "variant",
      "V6",
      "no_fact_calls"
    ]
  ]
}
```

## pass3.query8

- pass: 3
- language: sql
- difficulty: hard
- standard_instructions_id: sql_v1

### Prompt

```text
Using complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0'.
Group by condition and gene_role.
Return: condition, gene_role, non_reference_call_count, mean_vaf
Sort by condition ascending, then gene_role ascending.
Round mean_vaf to 3 decimals.
```

### Gold answer

| condition   | gene_role        |   non_reference_call_count |   mean_vaf |
|:------------|:-----------------|---------------------------:|-----------:|
| control     | ndh_membrane_arm |                          1 |        0.5 |
| drought     | pgr_regulator    |                          1 |        0.5 |
| high_light  | ndh_membrane_arm |                          2 |        0.7 |

### JSON answer

```json
{
  "case_id": "pass3.query8",
  "columns": [
    "condition",
    "gene_role",
    "non_reference_call_count",
    "mean_vaf"
  ],
  "rows": [
    [
      "control",
      "ndh_membrane_arm",
      1,
      0.5
    ],
    [
      "drought",
      "pgr_regulator",
      1,
      0.5
    ],
    [
      "high_light",
      "ndh_membrane_arm",
      2,
      0.7
    ]
  ]
}
```

## pass4.query1

- pass: 4
- language: python
- difficulty: extra_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas, create a reconciliation summary with exactly these metrics:

- fact_rows_total
- complete_chain_rows
- fact_rows_missing_sample
- fact_rows_missing_variant
- fact_rows_missing_gene
- unused_samples
- unused_variants
- genes_with_no_variants

Return: metric, value
Preserve this exact row order.
```

### Gold answer

| metric                    |   value |
|:--------------------------|--------:|
| fact_rows_total           |       9 |
| complete_chain_rows       |       6 |
| fact_rows_missing_sample  |       1 |
| fact_rows_missing_variant |       1 |
| fact_rows_missing_gene    |       1 |
| unused_samples            |       1 |
| unused_variants           |       1 |
| genes_with_no_variants    |       1 |

### JSON answer

```json
{
  "case_id": "pass4.query1",
  "columns": [
    "metric",
    "value"
  ],
  "rows": [
    [
      "fact_rows_total",
      9
    ],
    [
      "complete_chain_rows",
      6
    ],
    [
      "fact_rows_missing_sample",
      1
    ],
    [
      "fact_rows_missing_variant",
      1
    ],
    [
      "fact_rows_missing_gene",
      1
    ],
    [
      "unused_samples",
      1
    ],
    [
      "unused_variants",
      1
    ],
    [
      "genes_with_no_variants",
      1
    ]
  ]
}
```

## pass4.query2

- pass: 4
- language: python
- difficulty: extra_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas and complete-chain matched rows only, group by condition and pathway.
Compute:
- call_count
- total_alt_reads
- mean_qual
- avg_expr_ndhb

Return: condition, pathway, call_count, total_alt_reads, mean_qual, avg_expr_ndhb
Sort by condition ascending, then total_alt_reads descending, then pathway ascending.
Round decimal outputs to 3 decimals.
```

### Gold answer

| condition   | pathway                 |   call_count |   total_alt_reads |   mean_qual |   avg_expr_ndhb |
|:------------|:------------------------|-------------:|------------------:|------------:|----------------:|
| control     | chloroplast_NDH_complex |            3 |                10 |      87.667 |         233.333 |
| drought     | cyclic_electron_flow    |            1 |                 9 |      70     |         900     |
| high_light  | chloroplast_NDH_complex |            2 |                40 |      93     |        1200     |

### JSON answer

```json
{
  "case_id": "pass4.query2",
  "columns": [
    "condition",
    "pathway",
    "call_count",
    "total_alt_reads",
    "mean_qual",
    "avg_expr_ndhb"
  ],
  "rows": [
    [
      "control",
      "chloroplast_NDH_complex",
      3,
      10,
      87.667,
      233.333
    ],
    [
      "drought",
      "cyclic_electron_flow",
      1,
      9,
      70.0,
      900.0
    ],
    [
      "high_light",
      "chloroplast_NDH_complex",
      2,
      40,
      93.0,
      1200.0
    ]
  ]
}
```

## pass4.query3

- pass: 4
- language: python
- difficulty: extra_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas and complete-chain non-reference rows only where genotype <> '0/0',
group by batch and gene_role.
Compute:
- non_reference_calls
- avg_qual
- max_vaf
- mean_expr_pgr5

Return: batch, gene_role, non_reference_calls, avg_qual, max_vaf, mean_expr_pgr5
Sort by batch ascending, then gene_role ascending.
Round decimal outputs to 3 decimals.
```

### Gold answer

| batch   | gene_role        |   non_reference_calls |   avg_qual |   max_vaf |   mean_expr_pgr5 |
|:--------|:-----------------|----------------------:|-----------:|----------:|-----------------:|
| B1      | ndh_membrane_arm |                     3 |     88.667 |       1   |              700 |
| B2      | pgr_regulator    |                     1 |     70     |       0.5 |              700 |

### JSON answer

```json
{
  "case_id": "pass4.query3",
  "columns": [
    "batch",
    "gene_role",
    "non_reference_calls",
    "avg_qual",
    "max_vaf",
    "mean_expr_pgr5"
  ],
  "rows": [
    [
      "B1",
      "ndh_membrane_arm",
      3,
      88.667,
      1.0,
      700.0
    ],
    [
      "B2",
      "pgr_regulator",
      1,
      70.0,
      0.5,
      700.0
    ]
  ]
}
```

## pass4.query4

- pass: 4
- language: python
- difficulty: extra_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas and complete-chain matched rows only, find genes observed in both:
- control
- at least one non-control condition

Return:
- gene_symbol
- control_calls
- non_control_calls
- total_alt_reads

Sort by total_alt_reads descending, then gene_symbol ascending.
```

### Gold answer

| gene_symbol   |   control_calls |   non_control_calls |   total_alt_reads |
|:--------------|----------------:|--------------------:|------------------:|
| NDHB          |               1 |                   2 |                40 |

### JSON answer

```json
{
  "case_id": "pass4.query4",
  "columns": [
    "gene_symbol",
    "control_calls",
    "non_control_calls",
    "total_alt_reads"
  ],
  "rows": [
    [
      "NDHB",
      1,
      2,
      40
    ]
  ]
}
```

## pass4.query5

- pass: 4
- language: python
- difficulty: extra_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas, start from gene_dim and left join to variant_dim, then fact_calls, then sample_dim.
Return one row per gene with:
- gene_symbol
- variant_count
- call_count
- distinct_matched_sample_count
- distinct_tissue_count
- avg_matched_expression

For distinct_matched_sample_count, count only sample_dim matches and exclude orphan fact sample keys.
For avg_matched_expression, use the matched expression mapping from the instructions and average across matched sample-call rows only.
Sort by gene_symbol ascending.
Round avg_matched_expression to 3 decimals.
```

### Gold answer

| gene_symbol   |   variant_count |   call_count |   distinct_matched_sample_count |   distinct_tissue_count |   avg_matched_expression |
|:--------------|----------------:|-------------:|--------------------------------:|------------------------:|-------------------------:|
| NDHB          |               2 |            4 |                               2 |                       1 |                      900 |
| NDHK          |               1 |            2 |                               2 |                       2 |                       70 |
| NDHT          |               1 |            0 |                               0 |                       0 |                      nan |
| PGR1B         |               0 |            0 |                               0 |                       0 |                      nan |
| PGR5          |               1 |            1 |                               1 |                       1 |                      700 |

### JSON answer

```json
{
  "case_id": "pass4.query5",
  "columns": [
    "gene_symbol",
    "variant_count",
    "call_count",
    "distinct_matched_sample_count",
    "distinct_tissue_count",
    "avg_matched_expression"
  ],
  "rows": [
    [
      "NDHB",
      2,
      4,
      2,
      1,
      900.0
    ],
    [
      "NDHK",
      1,
      2,
      2,
      2,
      70.0
    ],
    [
      "NDHT",
      1,
      0,
      0,
      0,
      null
    ],
    [
      "PGR1B",
      0,
      0,
      0,
      0,
      null
    ],
    [
      "PGR5",
      1,
      1,
      1,
      1,
      700.0
    ]
  ]
}
```

## pass4.query6

- pass: 4
- language: python
- difficulty: extra_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas, compute sample-level burden.
Use complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0'
and impact IN ('high', 'moderate').

For each sample in sample_dim, compute:
- burden_genes = count of distinct genes meeting that rule
- mean_log2_marker_expr = mean(log2(expr_ndhb+1), log2(expr_pgr5+1), log2(expr_ndhk+1))

Return: sample_id, tissue, burden_genes, mean_log2_marker_expr
Include samples with zero burden.
Sort by burden_genes descending, then sample_id ascending.
Round mean_log2_marker_expr to 3 decimals.
```

### Gold answer

| sample_id   | tissue      |   burden_genes |   mean_log2_marker_expr |
|:------------|:------------|---------------:|------------------------:|
| S1          | mature_leaf |              1 |                   9.038 |
| S2          | mature_leaf |              1 |                   7.903 |
| S3          | young_leaf  |              0 |                   8.688 |
| S4          | young_leaf  |              0 |                   6.993 |
| S5          | root        |              0 |                   3.977 |

### JSON answer

```json
{
  "case_id": "pass4.query6",
  "columns": [
    "sample_id",
    "tissue",
    "burden_genes",
    "mean_log2_marker_expr"
  ],
  "rows": [
    [
      "S1",
      "mature_leaf",
      1,
      9.038
    ],
    [
      "S2",
      "mature_leaf",
      1,
      7.903
    ],
    [
      "S3",
      "young_leaf",
      0,
      8.688
    ],
    [
      "S4",
      "young_leaf",
      0,
      6.993
    ],
    [
      "S5",
      "root",
      0,
      3.977
    ]
  ]
}
```

## pass4.query7

- pass: 4
- language: python
- difficulty: extra_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas, build a single orphan-key report using concat/union-style logic.
Return: source_table, key_value, orphan_type

Include:
- fact_calls.sample_id values missing in sample_dim
- fact_calls.variant_id values missing in variant_dim
- variant_dim.gene_id values missing in gene_dim
- sample_dim.sample_id rows unused by fact_calls
- variant_dim.variant_id rows unused by fact_calls
- gene_dim.gene_id rows with no variants attached

Sort by source_table ascending, then key_value ascending.
```

### Gold answer

| source_table           | key_value   | orphan_type            |
|:-----------------------|:------------|:-----------------------|
| fact_calls.sample_id   | S999        | missing_in_sample_dim  |
| fact_calls.variant_id  | V999        | missing_in_variant_dim |
| gene_dim.gene_id       | G5          | no_variants_attached   |
| sample_dim.sample_id   | S5          | unused_dimension_row   |
| variant_dim.gene_id    | G999        | missing_in_gene_dim    |
| variant_dim.variant_id | V6          | unused_dimension_row   |

### JSON answer

```json
{
  "case_id": "pass4.query7",
  "columns": [
    "source_table",
    "key_value",
    "orphan_type"
  ],
  "rows": [
    [
      "fact_calls.sample_id",
      "S999",
      "missing_in_sample_dim"
    ],
    [
      "fact_calls.variant_id",
      "V999",
      "missing_in_variant_dim"
    ],
    [
      "gene_dim.gene_id",
      "G5",
      "no_variants_attached"
    ],
    [
      "sample_dim.sample_id",
      "S5",
      "unused_dimension_row"
    ],
    [
      "variant_dim.gene_id",
      "G999",
      "missing_in_gene_dim"
    ],
    [
      "variant_dim.variant_id",
      "V6",
      "unused_dimension_row"
    ]
  ]
}
```

## pass4.query8

- pass: 4
- language: python
- difficulty: extra_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas, produce a final presentation table for all non-reference complete-chain calls only.
Filter to genotype <> '0/0'.

Return these columns in this exact order:
call_id, plant_line_id, tissue, condition, gene_symbol, pathway, variant_id, impact, genotype, alt_reads, total_reads, vaf, matched_expr_count, log2_matched_expr, qual

Use the matched expression mapping from the instructions.
Sort by:
condition ascending,
tissue ascending,
gene_symbol ascending,
variant_id ascending,
call_id ascending.

Round vaf and log2_matched_expr to 3 decimals.
```

### Gold answer

|   call_id | plant_line_id   | tissue      | condition   | gene_symbol   | pathway                 | variant_id   | impact   | genotype   |   alt_reads |   total_reads |   vaf |   matched_expr_count |   log2_matched_expr |   qual |
|----------:|:----------------|:------------|:------------|:--------------|:------------------------|:-------------|:---------|:-----------|------------:|--------------:|------:|---------------------:|--------------------:|-------:|
|         4 | Line_B          | mature_leaf | control     | NDHK          | chloroplast_NDH_complex | V3           | high     | 0/1        |          10 |            20 |   0.5 |                   90 |               6.508 |     80 |
|         5 | Line_C          | young_leaf  | drought     | PGR5          | cyclic_electron_flow    | V4           | low      | 0/1        |           9 |            18 |   0.5 |                  700 |               9.453 |     70 |
|         1 | Line_A          | mature_leaf | high_light  | NDHB          | chloroplast_NDH_complex | V1           | moderate | 0/1        |          12 |            30 |   0.4 |                 1200 |              10.23  |     99 |
|         2 | Line_A          | mature_leaf | high_light  | NDHB          | chloroplast_NDH_complex | V2           | high     | 1/1        |          28 |            28 |   1   |                 1200 |              10.23  |     87 |

### JSON answer

```json
{
  "case_id": "pass4.query8",
  "columns": [
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
    "qual"
  ],
  "rows": [
    [
      4,
      "Line_B",
      "mature_leaf",
      "control",
      "NDHK",
      "chloroplast_NDH_complex",
      "V3",
      "high",
      "0/1",
      10,
      20,
      0.5,
      90,
      6.508,
      80
    ],
    [
      5,
      "Line_C",
      "young_leaf",
      "drought",
      "PGR5",
      "cyclic_electron_flow",
      "V4",
      "low",
      "0/1",
      9,
      18,
      0.5,
      700,
      9.453,
      70
    ],
    [
      1,
      "Line_A",
      "mature_leaf",
      "high_light",
      "NDHB",
      "chloroplast_NDH_complex",
      "V1",
      "moderate",
      "0/1",
      12,
      30,
      0.4,
      1200,
      10.23,
      99
    ],
    [
      2,
      "Line_A",
      "mature_leaf",
      "high_light",
      "NDHB",
      "chloroplast_NDH_complex",
      "V2",
      "high",
      "1/1",
      28,
      28,
      1.0,
      1200,
      10.23,
      87
    ]
  ]
}
```

## pass5.query1

- pass: 5
- language: python
- difficulty: extreme_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas and sample_dim only, compute these expression features for every sample:
- log2_expr_ndhb = log2(expr_ndhb + 1)
- log2_expr_pgr5 = log2(expr_pgr5 + 1)
- log2_expr_ndhk = log2(expr_ndhk + 1)
- ndh_module_ratio = (expr_ndhb + expr_ndhk) / (expr_ndhb + expr_pgr5 + expr_ndhk)

Return: sample_id, tissue, log2_expr_ndhb, log2_expr_pgr5, log2_expr_ndhk, ndh_module_ratio
Sort by sample_id ascending.
Round all derived decimals to 3 decimals.
```

### Gold answer

| sample_id   | tissue      |   log2_expr_ndhb |   log2_expr_pgr5 |   log2_expr_ndhk |   ndh_module_ratio |
|:------------|:------------|-----------------:|-----------------:|-----------------:|-------------------:|
| S1          | mature_leaf |           10.23  |            9.646 |            7.238 |              0.628 |
| S2          | mature_leaf |            8.234 |            8.969 |            6.508 |              0.438 |
| S3          | young_leaf  |            9.815 |            9.453 |            6.794 |              0.591 |
| S4          | young_leaf  |            6.658 |            8.647 |            5.672 |              0.273 |
| S5          | root        |            4.392 |            4.954 |            2.585 |              0.455 |

### JSON answer

```json
{
  "case_id": "pass5.query1",
  "columns": [
    "sample_id",
    "tissue",
    "log2_expr_ndhb",
    "log2_expr_pgr5",
    "log2_expr_ndhk",
    "ndh_module_ratio"
  ],
  "rows": [
    [
      "S1",
      "mature_leaf",
      10.23,
      9.646,
      7.238,
      0.628
    ],
    [
      "S2",
      "mature_leaf",
      8.234,
      8.969,
      6.508,
      0.438
    ],
    [
      "S3",
      "young_leaf",
      9.815,
      9.453,
      6.794,
      0.591
    ],
    [
      "S4",
      "young_leaf",
      6.658,
      8.647,
      5.672,
      0.273
    ],
    [
      "S5",
      "root",
      4.392,
      4.954,
      2.585,
      0.455
    ]
  ]
}
```

## pass5.query2

- pass: 5
- language: python
- difficulty: extreme_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas and complete-chain matched rows only, map matched expression by gene_symbol using the standard mapping.
Compute:
- matched_expr_count
- log2_matched_expr = log2(matched_expr_count + 1)
- vaf = alt_reads / total_reads
- expr_weighted_vaf = vaf * log2_matched_expr

Return: call_id, gene_symbol, matched_expr_count, log2_matched_expr, vaf, expr_weighted_vaf
Sort by call_id ascending.
Round derived decimals to 3 decimals.
```

### Gold answer

|   call_id | gene_symbol   |   matched_expr_count |   log2_matched_expr |   vaf |   expr_weighted_vaf |
|----------:|:--------------|---------------------:|--------------------:|------:|--------------------:|
|         1 | NDHB          |                 1200 |              10.23  |   0.4 |               4.092 |
|         2 | NDHB          |                 1200 |              10.23  |   1   |              10.23  |
|         3 | NDHB          |                  300 |               8.234 |   0   |               0     |
|         4 | NDHK          |                   90 |               6.508 |   0.5 |               3.254 |
|         5 | PGR5          |                  700 |               9.453 |   0.5 |               4.727 |
|         7 | NDHK          |                   50 |               5.672 |   0   |               0     |

### JSON answer

```json
{
  "case_id": "pass5.query2",
  "columns": [
    "call_id",
    "gene_symbol",
    "matched_expr_count",
    "log2_matched_expr",
    "vaf",
    "expr_weighted_vaf"
  ],
  "rows": [
    [
      1,
      "NDHB",
      1200,
      10.23,
      0.4,
      4.092
    ],
    [
      2,
      "NDHB",
      1200,
      10.23,
      1.0,
      10.23
    ],
    [
      3,
      "NDHB",
      300,
      8.234,
      0.0,
      0.0
    ],
    [
      4,
      "NDHK",
      90,
      6.508,
      0.5,
      3.254
    ],
    [
      5,
      "PGR5",
      700,
      9.453,
      0.5,
      4.727
    ],
    [
      7,
      "NDHK",
      50,
      5.672,
      0.0,
      0.0
    ]
  ]
}
```

## pass5.query3

- pass: 5
- language: python
- difficulty: extreme_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas and complete-chain matched rows only, group by condition and gene_symbol.
Compute:
- n_calls
- mean_matched_expr
- median_matched_expr
- pop_std_matched_expr using ddof=0

Return: condition, gene_symbol, n_calls, mean_matched_expr, median_matched_expr, pop_std_matched_expr
Sort by condition ascending, then gene_symbol ascending.
Round decimal outputs to 3 decimals.
```

### Gold answer

| condition   | gene_symbol   |   n_calls |   mean_matched_expr |   median_matched_expr |   pop_std_matched_expr |
|:------------|:--------------|----------:|--------------------:|----------------------:|-----------------------:|
| control     | NDHB          |         1 |                 300 |                   300 |                      0 |
| control     | NDHK          |         2 |                  70 |                    70 |                     20 |
| drought     | PGR5          |         1 |                 700 |                   700 |                      0 |
| high_light  | NDHB          |         2 |                1200 |                  1200 |                      0 |

### JSON answer

```json
{
  "case_id": "pass5.query3",
  "columns": [
    "condition",
    "gene_symbol",
    "n_calls",
    "mean_matched_expr",
    "median_matched_expr",
    "pop_std_matched_expr"
  ],
  "rows": [
    [
      "control",
      "NDHB",
      1,
      300.0,
      300.0,
      0.0
    ],
    [
      "control",
      "NDHK",
      2,
      70.0,
      70.0,
      20.0
    ],
    [
      "drought",
      "PGR5",
      1,
      700.0,
      700.0,
      0.0
    ],
    [
      "high_light",
      "NDHB",
      2,
      1200.0,
      1200.0,
      0.0
    ]
  ]
}
```

## pass5.query4

- pass: 5
- language: python
- difficulty: extreme_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas and sample_dim only, define:
- stress_group = 'stress' for conditions high_light or drought
- stress_group = 'control' for condition control

For each gene marker (NDHB, NDHK, PGR5), compute:
- stress_mean_log2
- control_mean_log2
- delta_log2_stress_minus_control

Use:
- NDHB from expr_ndhb
- NDHK from expr_ndhk
- PGR5 from expr_pgr5

Apply log2(x + 1) before averaging.
Return: gene_symbol, stress_mean_log2, control_mean_log2, delta_log2_stress_minus_control
Sort by gene_symbol ascending.
Round decimal outputs to 3 decimals.
```

### Gold answer

| gene_symbol   |   stress_mean_log2 |   control_mean_log2 |   delta_log2_stress_minus_control |
|:--------------|-------------------:|--------------------:|----------------------------------:|
| NDHB          |              8.146 |               7.446 |                             0.7   |
| NDHK          |              5.539 |               6.09  |                            -0.551 |
| PGR5          |              8.018 |               8.808 |                            -0.79  |

### JSON answer

```json
{
  "case_id": "pass5.query4",
  "columns": [
    "gene_symbol",
    "stress_mean_log2",
    "control_mean_log2",
    "delta_log2_stress_minus_control"
  ],
  "rows": [
    [
      "NDHB",
      8.146,
      7.446,
      0.7
    ],
    [
      "NDHK",
      5.539,
      6.09,
      -0.551
    ],
    [
      "PGR5",
      8.018,
      8.808,
      -0.79
    ]
  ]
}
```

## pass5.query5

- pass: 5
- language: python
- difficulty: extreme_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas and complete-chain non-reference rows only where genotype <> '0/0',
group by pathway and tissue.
Compute:
- non_reference_calls
- mean_vaf
- mean_log2_matched_expr
- burden_score = sum(vaf * log2(matched_expr_count + 1))

Return: pathway, tissue, non_reference_calls, mean_vaf, mean_log2_matched_expr, burden_score
Sort by pathway ascending, then tissue ascending.
Round decimal outputs to 3 decimals.
```

### Gold answer

| pathway                 | tissue      |   non_reference_calls |   mean_vaf |   mean_log2_matched_expr |   burden_score |
|:------------------------|:------------|----------------------:|-----------:|-------------------------:|---------------:|
| chloroplast_NDH_complex | mature_leaf |                     3 |      0.633 |                    8.989 |         17.576 |
| cyclic_electron_flow    | young_leaf  |                     1 |      0.5   |                    9.453 |          4.727 |

### JSON answer

```json
{
  "case_id": "pass5.query5",
  "columns": [
    "pathway",
    "tissue",
    "non_reference_calls",
    "mean_vaf",
    "mean_log2_matched_expr",
    "burden_score"
  ],
  "rows": [
    [
      "chloroplast_NDH_complex",
      "mature_leaf",
      3,
      0.633,
      8.989,
      17.576
    ],
    [
      "cyclic_electron_flow",
      "young_leaf",
      1,
      0.5,
      9.453,
      4.727
    ]
  ]
}
```

## pass5.query6

- pass: 5
- language: python
- difficulty: extreme_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas and sample_dim only, compute population z-scores for each expression marker:
- z_ndhb from expr_ndhb
- z_pgr5 from expr_pgr5
- z_ndhk from expr_ndhk

Use population standard deviation with ddof=0.

Then compute:
- photosynthesis_expr_z_mean = mean(z_ndhb, z_pgr5, z_ndhk)

Return: sample_id, z_ndhb, z_pgr5, z_ndhk, photosynthesis_expr_z_mean
Sort by photosynthesis_expr_z_mean descending, then sample_id ascending.
Round decimal outputs to 3 decimals.
```

### Gold answer

| sample_id   |   z_ndhb |   z_pgr5 |   z_ndhk |   photosynthesis_expr_z_mean |
|:------------|---------:|---------:|---------:|-----------------------------:|
| S1          |    1.497 |    1.17  |    1.384 |                        1.351 |
| S3          |    0.852 |    0.798 |    0.582 |                        0.744 |
| S2          |   -0.439 |    0.052 |    0.181 |                       -0.069 |
| S4          |   -0.869 |   -0.321 |   -0.622 |                       -0.604 |
| S5          |   -1.041 |   -1.7   |   -1.525 |                       -1.422 |

### JSON answer

```json
{
  "case_id": "pass5.query6",
  "columns": [
    "sample_id",
    "z_ndhb",
    "z_pgr5",
    "z_ndhk",
    "photosynthesis_expr_z_mean"
  ],
  "rows": [
    [
      "S1",
      1.497,
      1.17,
      1.384,
      1.351
    ],
    [
      "S3",
      0.852,
      0.798,
      0.582,
      0.744
    ],
    [
      "S2",
      -0.439,
      0.052,
      0.181,
      -0.069
    ],
    [
      "S4",
      -0.869,
      -0.321,
      -0.622,
      -0.604
    ],
    [
      "S5",
      -1.041,
      -1.7,
      -1.525,
      -1.422
    ]
  ]
}
```

## pass5.query7

- pass: 5
- language: python
- difficulty: extreme_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas and complete-chain matched rows only, create a condition-level integrative summary.
For each condition, compute:
- distinct_genes_observed
- mean_matched_expr
- cv_matched_expr = population_std(matched_expr_count, ddof=0) / mean(matched_expr_count)
- mean_vaf

Return: condition, distinct_genes_observed, mean_matched_expr, cv_matched_expr, mean_vaf
Sort by condition ascending.
Round decimal outputs to 3 decimals.
```

### Gold answer

| condition   |   distinct_genes_observed |   mean_matched_expr |   cv_matched_expr |   mean_vaf |
|:------------|--------------------------:|--------------------:|------------------:|-----------:|
| control     |                         2 |             146.667 |             0.748 |      0.167 |
| drought     |                         1 |             700     |             0     |      0.5   |
| high_light  |                         1 |            1200     |             0     |      0.7   |

### JSON answer

```json
{
  "case_id": "pass5.query7",
  "columns": [
    "condition",
    "distinct_genes_observed",
    "mean_matched_expr",
    "cv_matched_expr",
    "mean_vaf"
  ],
  "rows": [
    [
      "control",
      2,
      146.667,
      0.748,
      0.167
    ],
    [
      "drought",
      1,
      700.0,
      0.0,
      0.5
    ],
    [
      "high_light",
      1,
      1200.0,
      0.0,
      0.7
    ]
  ]
}
```

## pass5.query8

- pass: 5
- language: python
- difficulty: extreme_hard
- standard_instructions_id: python_v1

### Prompt

```text
Using pandas, compute a plant-photosynthesis burden table at sample level.

Start from sample_dim and left join in complete-chain non-reference calls where genotype <> '0/0'.
For each sample, compute:
- non_reference_complete_chain_calls
- high_or_moderate_nonref_calls where impact IN ('high','moderate')
- total_marker_expr = expr_ndhb + expr_pgr5 + expr_ndhk
- log2_total_marker_expr = log2(total_marker_expr + 1)
- photosynthesis_variant_pressure = high_or_moderate_nonref_calls * log2_total_marker_expr

Return:
sample_id, tissue, non_reference_complete_chain_calls, high_or_moderate_nonref_calls, total_marker_expr, log2_total_marker_expr, photosynthesis_variant_pressure

Include samples with zero calls.
Sort by photosynthesis_variant_pressure descending, then sample_id ascending.
Round decimal outputs to 3 decimals.
```

### Gold answer

| sample_id   | tissue      |   non_reference_complete_chain_calls |   high_or_moderate_nonref_calls |   total_marker_expr |   log2_total_marker_expr |   photosynthesis_variant_pressure |
|:------------|:------------|-------------------------------------:|--------------------------------:|--------------------:|-------------------------:|----------------------------------:|
| S1          | mature_leaf |                                    2 |                               2 |                2150 |                   11.071 |                            22.142 |
| S2          | mature_leaf |                                    1 |                               1 |                 890 |                    9.799 |                             9.799 |
| S3          | young_leaf  |                                    1 |                               0 |                1710 |                   10.741 |                             0     |
| S4          | young_leaf  |                                    0 |                               0 |                 550 |                    9.106 |                             0     |
| S5          | root        |                                    0 |                               0 |                  55 |                    5.807 |                             0     |

### JSON answer

```json
{
  "case_id": "pass5.query8",
  "columns": [
    "sample_id",
    "tissue",
    "non_reference_complete_chain_calls",
    "high_or_moderate_nonref_calls",
    "total_marker_expr",
    "log2_total_marker_expr",
    "photosynthesis_variant_pressure"
  ],
  "rows": [
    [
      "S1",
      "mature_leaf",
      2,
      2,
      2150,
      11.071,
      22.142
    ],
    [
      "S2",
      "mature_leaf",
      1,
      1,
      890,
      9.799,
      9.799
    ],
    [
      "S3",
      "young_leaf",
      1,
      0,
      1710,
      10.741,
      0.0
    ],
    [
      "S4",
      "young_leaf",
      0,
      0,
      550,
      9.106,
      0.0
    ],
    [
      "S5",
      "root",
      0,
      0,
      55,
      5.807,
      0.0
    ]
  ]
}
```
