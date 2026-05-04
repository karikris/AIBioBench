# AIBioBench v5 — 50 Task-Specific Query Prompt Templates
This Markdown file rewrites all 50 AIBioBench tasks into compact, task-specific prompt templates. Each template uses the same structure: **Output requirements**, **Task**, **Execution rules**, **Self-check before final answer**, **CSV tables**, and **Target-model addendum**.
Use only the CSV tables named in each query section. Omitting unused tables is intentional: it reduces context load and lowers the chance of irrelevant joins.
## Common JSON Contract
Every task returns only valid JSON in this shape:
```json
{"columns": ["..."], "rows": [[...], ...]}
```
- Do not output SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- Use JSON `null` for missing values.
- Preserve the exact column order and final row order requested by the task.
## Model-Specific Task Agendas
Use only the agenda for the target model. These are concise task-specific summaries distilled from each model file’s first three rule sections and its matching footer checks.
### Qwen3.6 27B
- **Core agenda:** Lock row set first; preserve valid rows; enforce complete-chain eligibility; aggregate at requested grain; sort last.
- **SQL agenda:** Identify join path; treat inner/complete-chain as filters; preserving joins preserve side; compute VAF row-wise; avoid mixed groups.
- **Pandas agenda:** Choose base frame first; compute row-level helpers before aggregation; use exact expression mapping; ddof=0; keep row/group products separate.
- **Footer focus:** Check exact columns, row-set locking, orphan/incomplete exclusion, duplicate preservation, group consistency, row-wise VAF, sort/rounding drift.
### Qwen3.6
- **Core agenda:** Lock exact row set; do not drop valid joined rows; avoid duplicate collapse; aggregate at requested grain; final sort last.
- **SQL agenda:** Use requested join path/type; preserve requested side for outer joins; avoid leaking orphan rows; compute group cells from one row set.
- **Pandas agenda:** Build exact frame before filters/derivations; preserve sample-start tasks; exclude incomplete chains; map expression exactly; avoid premature rounding.
- **Footer focus:** Check exact columns, repeated row preservation, orphan/incomplete exclusion, no sample leakage, joined fact-call grain, row-wise VAF, same-group max/avg/counts.
### Qwen3 Coder 30B
- **Core agenda:** Keep benchmark narrow; build exact row set; do not invent labels or helper rows; preserve valid rows; sort after all calculations.
- **SQL agenda:** Create only requested joins/filters/groups; preserve only when asked; count fact rows; conditional counts after joins; final ORDER BY exact.
- **Pandas agenda:** Minimal pandas output; choose correct base frame; derive row-level formulas before grouping; preserve zero-count dimensions where requested.
- **Footer focus:** Check no invented rows/groups/labels, correct base frame, row-level formulas first, exact mapping, no mixed row/group products, final sort/rounding.
### Phi-4 Mini
- **Core agenda:** Treat task as strict table construction; establish eligible row set first; no invented helper rows; preserve/Exclude rows exactly as requested.
- **SQL agenda:** Use exact join type; grouped metrics from one row set; conditional counts after joins; no wrong-row cell copying; final ORDER BY exact.
- **Pandas agenda:** Choose frame by task type; use clear merge/filter/derive/aggregate/project/sort pipeline; separate row-level and grouped formulas.
- **Footer focus:** Check exact join type, preserving side, correct grouped row set, no wrong-row copied cells, exact mapping/log/ddof, zero-count rows when requested.
### Gemma 4 26B
- **Core agenda:** Return exact rows/columns/values; establish eligible row set; preserve observations unless distinct is requested; sort last.
- **SQL agenda:** Identify join path; exact join logic; count fact rows; preserve impact categories present; conditional metrics after joined row set.
- **Pandas agenda:** Choose pandas base frame; keep valid non-reference/high/moderate/repeated calls; reuse mapped expression series; avoid mixed grouped frames.
- **Footer focus:** Check every valid joined/repeated row, incomplete-chain removal, all impact classes present, same grouped row set, expression mapping reuse, no mixed frames.
### Gemma 4 31B
- **Core agenda:** Lock row set; aggregate at requested grain; avoid duplicate collapse unless requested; round final decimals only; re-sort after projection.
- **SQL agenda:** Use exact join type/path; inner/complete-chain filters; preserving joins preserve requested table; call counts use fact rows.
- **Pandas agenda:** Build correct base DataFrame; compute row-level helpers before aggregation; use exact expression mapping; separate row products from grouped products.
- **Footer focus:** Check stable row sets, repeated valid calls, same grouped metrics, row-level helpers, exact mapping/log/ddof, decision/weighted metrics from intended means.
## pass1.query1 — SQL — Inner join fact_calls to sample_dim on sample_id. Return: call_id, sample_id, tissue, cond
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "sample_id", "tissue", "condition", "genotype"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, sample_id, tissue, condition, genotype.
- Do not add rounding rules that the task did not request.

Task:
Inner join fact_calls to sample_dim on sample_id.
Return: call_id, sample_id, tissue, condition, genotype
Sort by call_id ascending.

Execution rules:
1. Use a true inner join to sample_dim.
2. Keep every fact row whose sample_id exists in sample_dim, including repeated valid calls for the same sample.
3. Do not drop valid joined calls.
4. Project only requested columns and sort by call_id ASC after projection.

Self-check before final answer:
1. Are the columns exactly ["call_id", "sample_id", "tissue", "condition", "genotype"]?
2. Did I follow the row-set rule: Use a true inner join to sample_dim.
3. Did I follow the calculation/projection rule: Keep every fact row whose sample_id exists in sample_dim, including repeated valid calls for the same sample.
4. Did I apply the final sort exactly: Sort by call_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6:** Use a true inner join to sample_dim. Keep every fact row whose sample_id exists in sample_dim, including repeated valid calls for the same sample. Do not drop valid joined calls. Project only requested columns and sort by call_id ASC after projection.
- **Gemma 4 26B:** Use a true inner join to sample_dim. Keep every fact row whose sample_id exists in sample_dim, including duplicate or repeated valid sample calls. Do not drop valid joined calls. Project only requested columns and sort by call_id ASC after projection.
- **Gemma 4 31B:** This query was historically stable. Keep it simple: perform only the requested inner join, preserve every fact row with a matching sample, project only requested columns, and sort by call_id ascending after projection.
- **Phi-4 Mini:** Use a true inner join to sample_dim. Exclude fact rows whose sample_id is missing from sample_dim. Keep every valid joined fact row, including repeated calls for the same sample. Do not leak orphan sample rows into the result. Project only requested columns and sort by call_id ASC after projection.
- **Qwen3 Coder 30B:** Use a true inner join to sample_dim. Exclude fact rows whose sample_id is missing from sample_dim. Keep every valid joined fact row, including repeated calls for the same sample. Project only requested columns and sort by call_id ASC after projection.

## pass1.query2 — SQL — Inner join fact_calls to variant_dim on variant_id. Return: call_id, variant_id, variant_c
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "variant_id", "variant_class", "impact", "qual"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, variant_id, variant_class, impact, qual.
- Do not add rounding rules that the task did not request.

Task:
Inner join fact_calls to variant_dim on variant_id.
Return: call_id, variant_id, variant_class, impact, qual
Sort by qual descending, then call_id ascending.

Execution rules:
1. Use a true inner join to variant_dim and exclude fact rows without a matching variant.
2. Do not keep missing-variant fact rows.
3. Preserve every valid joined variant call.
4. After projection, explicitly sort by qual DESC, then call_id ASC.

Self-check before final answer:
1. Are the columns exactly ["call_id", "variant_id", "variant_class", "impact", "qual"]?
2. Did I follow the row-set rule: Use a true inner join to variant_dim and exclude fact rows without a matching variant.
3. Did I follow the calculation/projection rule: Do not keep missing-variant fact rows.
4. Did I apply the final sort exactly: Sort by qual descending, then call_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use a true inner join to variant_dim and exclude fact rows without a matching variant. Do not keep missing-variant fact rows. Preserve every valid joined variant call. After projection, explicitly sort by qual DESC, then call_id ASC.
- **Gemma 4 31B:** Use a true inner join to variant_dim and exclude fact rows without a matching variant. Do not keep missing-variant fact rows. After projection, explicitly sort by qual DESC, then call_id ASC; do not rely on input order.

## pass1.query3 — SQL — Left join fact_calls to sample_dim on sample_id. Return: call_id, sample_id, tissue, batch
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "sample_id", "tissue", "batch", "expr_ndhb"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, sample_id, tissue, batch, expr_ndhb.
- Do not add rounding rules that the task did not request.

Task:
Left join fact_calls to sample_dim on sample_id.
Return: call_id, sample_id, tissue, batch, expr_ndhb
Keep all fact rows.
Sort by call_id ascending.

Execution rules:
1. fact_calls is the preserving table.
2. Keep every fact row exactly once.
3. For unmatched samples, keep the fact row and use NULL for missing sample_dim fields.
4. Do not borrow tissue, batch, or expression cells from another sample.
5. Sort by call_id ASC after projection.

Self-check before final answer:
1. Are the columns exactly ["call_id", "sample_id", "tissue", "batch", "expr_ndhb"]?
2. Did I follow the row-set rule: fact_calls is the preserving table.
3. Did I follow the calculation/projection rule: Keep every fact row exactly once.
4. Did I apply the final sort exactly: Sort by call_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B:** fact_calls is the preserving table. Keep every fact row exactly once. For unmatched samples, keep the fact row and use NULL for missing sample_dim fields. Do not borrow tissue, batch, or expression cells from another sample. Sort by call_id ASC after projection.
- **Gemma 4 26B:** fact_calls is the preserving table. Keep every fact row exactly once. For unmatched samples, keep the fact row and use NULL for missing sample_dim fields. Do not fill sample-derived cells from another row. Sort only after the final projection.
- **Gemma 4 31B:** This query was historically stable. Preserve every fact_calls row exactly once. For unmatched samples, keep the fact row and use NULL for missing sample_dim fields. Sort only after the final projection.
- **Phi-4 Mini:** fact_calls is the preserving table. Keep every fact row exactly once, including unmatched sample rows. For unmatched samples, keep the fact row and use NULL for missing sample_dim fields. Do not borrow tissue, batch, or expression cells from another sample. Sort by call_id ASC after projection.

## pass1.query4 — SQL — Use a RIGHT JOIN from fact_calls to sample_dim, or an equivalent reversed LEFT JOIN. Retur
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["sample_id", "tissue", "call_count", "avg_qual"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: sample_id, tissue, call_count, avg_qual.
- Round avg_qual to 3 decimals.

Task:
Use a RIGHT JOIN from fact_calls to sample_dim, or an equivalent reversed LEFT JOIN.
Return one row per sample with:
sample_id, tissue, call_count, avg_qual
Include samples with zero calls.
Sort by sample_id ascending.
Round avg_qual to 3 decimals.

Execution rules:
1. Use sample_dim as the preserving table.
2. Return one row per sample.
3. call_count counts matched fact rows, not distinct variants or distinct samples.
4. avg_qual is computed only from matched fact rows for that sample.
5. Keep zero-call samples and round avg_qual only at output.

Self-check before final answer:
1. Are the columns exactly ["sample_id", "tissue", "call_count", "avg_qual"]?
2. Did I follow the row-set rule: Use sample_dim as the preserving table.
3. Did I follow the calculation/projection rule: Return one row per sample.
4. Did I apply the final sort exactly: Sort by sample_id ascending.
5. Did I round only at final output: Round avg_qual to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use sample_dim as the preserving table. Return one row per sample. call_count counts matched fact rows, not distinct variants or distinct samples. avg_qual is computed only from matched fact rows for that sample. Keep zero-call samples and round avg_qual only at output.
- **Gemma 4 31B:** Use sample_dim as the preserving table. Count matched fact rows per sample; zero-call samples must remain with call_count = 0. Compute avg_qual only from matched fact rows, leave it NULL when there are no calls, and round only after the aggregation.

## pass1.query5 — SQL — Inner join fact_calls to variant_dim, then to gene_dim. Return: call_id, variant_id, gene_
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "variant_id", "gene_symbol", "pathway"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, variant_id, gene_symbol, pathway.
- Do not add rounding rules that the task did not request.

Task:
Inner join fact_calls to variant_dim, then to gene_dim.
Return: call_id, variant_id, gene_symbol, pathway
Sort by call_id ascending.

Execution rules:
1. Use two sequential inner joins.
2. A fact row must match variant_dim and then gene_dim to survive.
3. Drop incomplete variant-to-gene chains.
4. Do not keep rows after the first join if the second join fails.
5. Sort by call_id ASC after projection.

Self-check before final answer:
1. Are the columns exactly ["call_id", "variant_id", "gene_symbol", "pathway"]?
2. Did I follow the row-set rule: Use two sequential inner joins.
3. Did I follow the calculation/projection rule: A fact row must match variant_dim and then gene_dim to survive.
4. Did I apply the final sort exactly: Sort by call_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use two sequential inner joins. A fact row must match variant_dim and then gene_dim to survive. Drop incomplete variant-to-gene chains. Do not keep rows after the first join if the second join fails. Sort by call_id ASC after projection.
- **Gemma 4 31B:** Use two sequential inner joins. A fact row must survive both the variant join and the gene join to appear. Do not keep incomplete-chain rows where the variant exists but the gene branch does not match. Sort by call_id ASC after projection.

## pass1.query6 — SQL — Inner join fact_calls to variant_dim. Count calls by impact and also compute average qual
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["impact", "call_count", "avg_qual"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: impact, call_count, avg_qual.
- Round avg_qual to 3 decimals.

Task:
Inner join fact_calls to variant_dim.
Count calls by impact and also compute average qual.
Return: impact, call_count, avg_qual
Sort by call_count descending, then impact ascending.
Round avg_qual to 3 decimals.

Execution rules:
1. Aggregate at fact-call grain after the inner join.
2. Count every joined call row, including repeated variants within the same impact class.
3. Keep every impact category present in the joined data.
4. avg_qual must be computed from the same rows used for call_count.
5. Sort after final rounding.

Self-check before final answer:
1. Are the columns exactly ["impact", "call_count", "avg_qual"]?
2. Did I follow the row-set rule: Aggregate at fact-call grain after the inner join.
3. Did I follow the calculation/projection rule: Count every joined call row, including repeated variants within the same impact class.
4. Did I apply the final sort exactly: Sort by call_count descending, then impact ascending.
5. Did I round only at final output: Round avg_qual to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini:** Aggregate at fact-call grain after the inner join. Count every joined call row, including repeated variants within the same impact class. Keep every impact category present in the joined data. avg_qual must be computed from the same rows used for call_count. Sort after final rounding.
- **Gemma 4 26B:** Aggregate at fact-call grain after the inner join. Keep all impact categories present in the joined data, including low and modifier. call_count counts every joined call row. avg_qual must be computed from the same rows used for call_count. Sort after final rounding.
- **Gemma 4 31B:** Aggregate at fact-call grain after the inner join. Count every joined call row, including repeated variants within the same impact class. Compute avg_qual from the same joined rows used for call_count. Re-check high-impact counts before sorting.

## pass1.query7 — SQL — Inner join fact_calls to sample_dim. Compute average, minimum, and maximum qual by tissue
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["tissue", "avg_qual", "min_qual", "max_qual"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: tissue, avg_qual, min_qual, max_qual.
- Round avg_qual to 3 decimals.

Task:
Inner join fact_calls to sample_dim.
Compute average, minimum, and maximum qual by tissue.
Return: tissue, avg_qual, min_qual, max_qual
Sort by avg_qual descending.
Round avg_qual to 3 decimals.

Execution rules:
1. Aggregate by tissue over joined fact-call rows, not distinct samples.
2. avg_qual, min_qual, and max_qual must all come from the same tissue-specific joined row set.
3. Do not compute sample-level averages first.
4. Round avg_qual only at final output.

Self-check before final answer:
1. Are the columns exactly ["tissue", "avg_qual", "min_qual", "max_qual"]?
2. Did I follow the row-set rule: Aggregate by tissue over joined fact-call rows, not distinct samples.
3. Did I follow the calculation/projection rule: avg_qual, min_qual, and max_qual must all come from the same tissue-specific joined row set.
4. Did I apply the final sort exactly: Sort by avg_qual descending.
5. Did I round only at final output: Round avg_qual to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Aggregate by tissue over joined fact-call rows, not distinct samples. avg_qual, min_qual, and max_qual must all come from the same tissue-specific joined row set. Do not compute sample-level averages first. Round avg_qual only at final output.
- **Gemma 4 31B:** Aggregate by tissue over joined fact-call rows, not distinct samples. avg_qual, min_qual, and max_qual must all come from the same joined row set. Round avg_qual only at final output and re-apply avg_qual DESC sorting.

## pass1.query8 — SQL — Inner join fact_calls to sample_dim. For each condition, compute:
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition", "call_count", "avg_expr_pgr5"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition, call_count, avg_expr_pgr5.
- Round avg_expr_pgr5 to 3 decimals.

Task:
Inner join fact_calls to sample_dim.
For each condition, compute:

* call_count
* avg_expr_pgr5
Return: condition, call_count, avg_expr_pgr5
Sort by condition ascending.
Round avg_expr_pgr5 to 3 decimals.

Execution rules:
1. Compute at joined fact-call grain.
2. If one sample contributes multiple fact rows, its expr_pgr5 contributes once per joined fact row.
3. Do not count samples instead of calls.
4. Do not leak unmatched or unused sample rows into condition groups.
5. Sort by condition ASC after rounding.

Self-check before final answer:
1. Are the columns exactly ["condition", "call_count", "avg_expr_pgr5"]?
2. Did I follow the row-set rule: Compute at joined fact-call grain.
3. Did I follow the calculation/projection rule: If one sample contributes multiple fact rows, its expr_pgr5 contributes once per joined fact row.
4. Did I apply the final sort exactly: Sort by condition ascending.
5. Did I round only at final output: Round avg_expr_pgr5 to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini:** Compute at joined fact-call grain. If one sample contributes multiple fact rows, its expr_pgr5 contributes once per joined fact row. Do not count samples instead of calls. Do not leak unmatched or unused sample rows into condition groups. Sort by condition ASC after rounding.
- **Gemma 4 26B:** Compute at joined fact-call grain. If one sample contributes multiple fact rows, its expr_pgr5 contributes once per joined fact row. Do not count samples instead of calls. Do not leak unmatched sample rows into condition groups. Sort by condition ASC after rounding.
- **Gemma 4 31B:** Compute at fact-call grain after joining to sample_dim. If one sample contributes multiple calls, its expr_pgr5 contributes once per joined call row. Do not average distinct samples unless explicitly requested. Sort by condition ASC after rounding.

## pass1.query9 — SQL — Decision screen for sample quality. Inner join fact_calls to sample_dim and variant_dim
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition", "total_calls", "avg_qual", "high_impact_calls"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition, total_calls, avg_qual, high_impact_calls.
- Round avg_qual to 3 decimals.

Task:
Decision screen for sample quality.
Inner join fact_calls to sample_dim and variant_dim.
For each condition, compute:

* total_calls
* avg_qual
* high_impact_calls where impact = 'high'
Return: condition, total_calls, avg_qual, high_impact_calls
Sort by condition ascending.
Round avg_qual to 3 decimals.

Execution rules:
1. First build the joined fact/sample/variant row set.
2. total_calls and avg_qual use all joined rows per condition.
3. high_impact_calls counts only rows from that joined frame where impact = 'high'.
4. Do not compute high-impact counts before the variant join.
5. Sort by condition ASC.

Self-check before final answer:
1. Are the columns exactly ["condition", "total_calls", "avg_qual", "high_impact_calls"]?
2. Did I follow the row-set rule: First build the joined fact/sample/variant row set.
3. Did I follow the calculation/projection rule: total_calls and avg_qual use all joined rows per condition.
4. Did I apply the final sort exactly: Sort by condition ascending.
5. Did I round only at final output: Round avg_qual to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** First build the joined fact/sample/variant row set. total_calls and avg_qual use all joined rows per condition. high_impact_calls counts only rows from that joined frame where impact = 'high'. Do not compute high-impact counts before the variant join. Sort by condition ASC.
- **Gemma 4 31B:** First build the joined fact/sample/variant row set. total_calls and avg_qual use all joined rows per condition. high_impact_calls counts only joined rows where impact = 'high'. Do not count high-impact rows before the variant join.

## pass1.query10 — SQL — Simple anomaly audit. Left join fact_calls to variant_dim on variant_id
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "variant_id", "impact", "variant_match_status"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, variant_id, impact, variant_match_status.
- Do not add rounding rules that the task did not request.

Task:
Simple anomaly audit.
Left join fact_calls to variant_dim on variant_id.
Return: call_id, variant_id, impact, variant_match_status
Set variant_match_status to MATCHED when variant_dim matched, else MISSING_VARIANT.
Keep all fact rows.
Sort by call_id ascending.

Execution rules:
1. Preserve every fact row.
2. Set MATCHED only when the variant_dim join succeeds; otherwise set MISSING_VARIANT and leave variant_dim-derived fields NULL.
3. Do not label matched variants as missing.
4. Sort by call_id ASC after classification.

Self-check before final answer:
1. Are the columns exactly ["call_id", "variant_id", "impact", "variant_match_status"]?
2. Did I follow the row-set rule: Preserve every fact row.
3. Did I follow the calculation/projection rule: Set MATCHED only when the variant_dim join succeeds; otherwise set MISSING_VARIANT and leave variant_dim-derived fields NULL.
4. Did I apply the final sort exactly: Sort by call_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Preserve every fact row. Set MATCHED only when the variant_dim join succeeds; otherwise set MISSING_VARIANT and leave variant_dim-derived fields NULL. Do not label matched variants as missing. Sort by call_id ASC after classification.
- **Gemma 4 31B:** This query was historically stable. Preserve every fact row. Set MATCHED only when the variant_dim join succeeds; otherwise set MISSING_VARIANT and leave variant_dim-derived fields NULL. Sort by call_id ASC.

## pass2.query1 — SQL — Inner join across all four tables: fact_calls -> sample_dim
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "sample_id", "tissue", "gene_symbol", "impact", "genotype"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, sample_id, tissue, gene_symbol, impact, genotype.
- Do not add rounding rules that the task did not request.

Task:
Inner join across all four tables:
fact_calls -> sample_dim
fact_calls -> variant_dim -> gene_dim
Return: call_id, sample_id, tissue, gene_symbol, impact, genotype
Sort by call_id ascending.

Execution rules:
1. Use complete-chain inner joins only.
2. A row must match sample_dim, variant_dim, and gene_dim to survive.
3. Preserve all valid complete-chain calls.
4. Do not keep partial-chain rows and do not drop valid complete-chain rows.
5. Sort by call_id ASC.

Self-check before final answer:
1. Are the columns exactly ["call_id", "sample_id", "tissue", "gene_symbol", "impact", "genotype"]?
2. Did I follow the row-set rule: Use complete-chain inner joins only.
3. Did I follow the calculation/projection rule: A row must match sample_dim, variant_dim, and gene_dim to survive.
4. Did I apply the final sort exactly: Sort by call_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini:** Use complete-chain inner joins only. A row must match sample_dim, variant_dim, and gene_dim to survive. Preserve all valid complete-chain calls. Do not keep partial-chain rows and do not drop valid complete-chain rows. Sort by call_id ASC.
- **Gemma 4 26B:** Use complete-chain inner joins only. A row must match sample_dim, variant_dim, and gene_dim to survive. Preserve all valid complete-chain calls; do not drop valid rows after the full join. Do not keep partial-chain rows. Sort by call_id ASC.
- **Gemma 4 31B:** This query was historically stable. Use complete-chain inner joins only. A row must match sample_dim, variant_dim, and gene_dim to survive. Do not keep orphan or incomplete-chain rows. Sort by call_id ASC after projection.

## pass2.query2 — SQL — Left join fact_calls across the full snowflake. Return: call_id, sample_id, plant_line_id,
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "sample_id", "plant_line_id", "tissue", "variant_id", "gene_symbol"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, sample_id, plant_line_id, tissue, variant_id, gene_symbol.
- Do not add rounding rules that the task did not request.

Task:
Left join fact_calls across the full snowflake.
Return: call_id, sample_id, plant_line_id, tissue, variant_id, gene_symbol
Keep all fact rows.
Sort by call_id ascending.

Execution rules:
1. fact_calls is the preserving table.
2. Keep all fact rows exactly once across both snowflake branches.
3. Use NULL for missing sample, variant, or gene fields.
4. Do not silently convert this into an inner join.
5. Sort by call_id ASC after projection.

Self-check before final answer:
1. Are the columns exactly ["call_id", "sample_id", "plant_line_id", "tissue", "variant_id", "gene_symbol"]?
2. Did I follow the row-set rule: fact_calls is the preserving table.
3. Did I follow the calculation/projection rule: Keep all fact rows exactly once across both snowflake branches.
4. Did I apply the final sort exactly: Sort by call_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** fact_calls is the preserving table. Keep all fact rows exactly once across both snowflake branches. Use NULL for missing sample, variant, or gene fields. Do not silently convert this into an inner join. Sort by call_id ASC after projection.
- **Gemma 4 31B:** This query was historically stable. fact_calls is the preserving table. Keep all fact rows exactly once, even when sample, variant, or gene branches are missing. Use NULL for unmatched dimension values and sort by call_id ASC.

## pass2.query3 — SQL — Perform a FULL OUTER JOIN between fact_calls and variant_dim on variant_id. Return:
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["variant_id", "call_id", "sample_id", "impact"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: variant_id, call_id, sample_id, impact.
- Do not add rounding rules that the task did not request.

Task:
Perform a FULL OUTER JOIN between fact_calls and variant_dim on variant_id.
Return:

* variant_id as the coalesced key
* call_id
* sample_id
* impact
Sort by variant_id ascending, then call_id ascending.

Execution rules:
1. Use a true full outer join or a correct union-based emulation.
2. Keep fact-only and variant-only rows.
3. Coalesce variant_id once and use that coalesced key for output and sorting.
4. Do not duplicate matched rows.
5. Sort by variant_id ASC, then call_id ASC.

Self-check before final answer:
1. Are the columns exactly ["variant_id", "call_id", "sample_id", "impact"]?
2. Did I follow the row-set rule: Use a true full outer join or a correct union-based emulation.
3. Did I follow the calculation/projection rule: Keep fact-only and variant-only rows.
4. Did I apply the final sort exactly: Sort by variant_id ascending, then call_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use a true full outer join or a correct union-based emulation. Keep fact-only and variant-only rows. Coalesce variant_id once and use that coalesced key for output and sorting. Do not duplicate matched rows. Sort by variant_id ASC, then call_id ASC.
- **Gemma 4 31B:** This query was historically stable. Use a true full outer join or a correct union-based emulation. Coalesce the variant_id key once. Keep unmatched fact rows and unused variants without duplication. Apply the requested two-key sort last.

## pass2.query4 — SQL — Inner join fact_calls to sample_dim and variant_dim. Count calls by condition and impact,
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition", "impact", "call_count", "avg_qual"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition, impact, call_count, avg_qual.
- Round avg_qual to 3 decimals.

Task:
Inner join fact_calls to sample_dim and variant_dim.
Count calls by condition and impact, and compute average qual.
Return: condition, impact, call_count, avg_qual
Sort by condition ascending, then impact ascending.
Round avg_qual to 3 decimals.

Execution rules:
1. Aggregate over the joined fact/sample/variant rows.
2. Group exactly by condition and impact.
3. Preserve every condition-impact group present after the join.
4. call_count and avg_qual must come from the same grouped rows.
5. Do not reuse condition-only or impact-only averages.
6. Sort after final rounding.

Self-check before final answer:
1. Are the columns exactly ["condition", "impact", "call_count", "avg_qual"]?
2. Did I follow the row-set rule: Aggregate over the joined fact/sample/variant rows.
3. Did I follow the calculation/projection rule: Group exactly by condition and impact.
4. Did I apply the final sort exactly: Sort by condition ascending, then impact ascending.
5. Did I round only at final output: Round avg_qual to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini:** Aggregate over the joined fact/sample/variant rows. Group exactly by condition and impact. Preserve every condition-impact group present after the join. call_count and avg_qual must come from the same grouped rows. Do not reuse condition-only or impact-only averages. Sort after final rounding.
- **Gemma 4 26B:** Aggregate over the joined fact/sample/variant rows. Group exactly by condition and impact. Preserve all impact categories present after the join, including low and modifier. call_count and avg_qual must come from the same grouped rows. Sort after final rounding.
- **Gemma 4 31B:** Aggregate over the joined fact/sample/variant rows. Group exactly by condition and impact. Count every joined call row in each bucket. Compute avg_qual from that same bucket; do not reuse averages from a broader condition-only or impact-only grouping.

## pass2.query5 — SQL — Inner join fact_calls to variant_dim and gene_dim. Compute VAF = alt_reads / total_reads
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["gene_symbol", "avg_vaf", "max_qual"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: gene_symbol, avg_vaf, max_qual.
- Round avg_vaf to 3 decimals.

Task:
Inner join fact_calls to variant_dim and gene_dim.
Compute VAF = alt_reads / total_reads.
Return average VAF and maximum qual by gene_symbol.
Columns: gene_symbol, avg_vaf, max_qual
Sort by avg_vaf descending, then gene_symbol ascending.
Round avg_vaf to 3 decimals.

Execution rules:
1. Compute VAF per joined call row first as alt_reads / total_reads.
2. Then average those per-row VAF values by gene_symbol.
3. Do not calculate VAF from summed reads unless explicitly requested.
4. max_qual must come from the same joined gene-specific rows.
5. Sort after aggregation.

Self-check before final answer:
1. Are the columns exactly ["gene_symbol", "avg_vaf", "max_qual"]?
2. Did I follow the row-set rule: Compute VAF per joined call row first as alt_reads / total_reads.
3. Did I follow the calculation/projection rule: Then average those per-row VAF values by gene_symbol.
4. Did I apply the final sort exactly: Sort by avg_vaf descending, then gene_symbol ascending.
5. Did I round only at final output: Round avg_vaf to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Compute VAF per joined call row first as alt_reads / total_reads. Then average those per-row VAF values by gene_symbol. Do not calculate VAF from summed reads unless explicitly requested. max_qual must come from the same joined gene-specific rows. Sort after aggregation.
- **Gemma 4 31B:** Compute VAF per joined call row first as alt_reads / total_reads. Then average those per-row VAF values by gene_symbol. max_qual must come from the same joined row set. Do not calculate VAF from summed reads unless explicitly requested.

## pass2.query6 — SQL — Use complete inner joins across all four tables. For each tissue, compute:
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["tissue", "distinct_genes", "avg_expr_ndhb"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: tissue, distinct_genes, avg_expr_ndhb.
- Round avg_expr_ndhb to 3 decimals.

Task:
Use complete inner joins across all four tables.
For each tissue, compute:

* distinct_genes
* avg_expr_ndhb
Return: tissue, distinct_genes, avg_expr_ndhb
Sort by tissue ascending.
Round avg_expr_ndhb to 3 decimals.

Execution rules:
1. Use only complete-chain rows.
2. distinct_genes counts unique gene_symbol values per tissue after the complete join.
3. avg_expr_ndhb is averaged over complete-chain joined call rows, not distinct samples.
4. Round only at final output and sort by tissue ASC.

Self-check before final answer:
1. Are the columns exactly ["tissue", "distinct_genes", "avg_expr_ndhb"]?
2. Did I follow the row-set rule: Use only complete-chain rows.
3. Did I follow the calculation/projection rule: distinct_genes counts unique gene_symbol values per tissue after the complete join.
4. Did I apply the final sort exactly: Sort by tissue ascending.
5. Did I round only at final output: Round avg_expr_ndhb to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini:** Use only complete-chain rows. distinct_genes counts unique gene_symbol values per tissue after the complete join. avg_expr_ndhb is averaged over complete-chain joined call rows, not distinct samples. Round only at final output and sort by tissue ASC.
- **Gemma 4 26B:** Use only complete-chain rows. distinct_genes counts unique gene_symbol values per tissue after the complete join. avg_expr_ndhb is averaged over the complete-chain joined call rows, not distinct samples. Round only at final output and sort by tissue ASC.
- **Gemma 4 31B:** This query was historically stable. Use only complete-chain rows. distinct_genes counts unique gene_symbol values per tissue. avg_expr_ndhb is averaged over the complete-chain joined call rows, not distinct samples. Round only at final output.

## pass2.query7 — SQL — Use sample_dim as the preserving table. For each sample, count high-impact calls and compu
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["sample_id", "tissue", "high_impact_call_count", "avg_alt_reads_high"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: sample_id, tissue, high_impact_call_count, avg_alt_reads_high.
- Round avg_alt_reads_high to 3 decimals.

Task:
Use sample_dim as the preserving table.
For each sample, count high-impact calls and compute average alt_reads among only high-impact calls.
Return: sample_id, tissue, high_impact_call_count, avg_alt_reads_high
Include samples with zero high-impact calls.
Sort by high_impact_call_count descending, then sample_id ascending.
Round avg_alt_reads_high to 3 decimals.

Execution rules:
1. Preserve all samples from sample_dim.
2. Count only joined calls whose impact is high.
3. Include all valid high-impact rows, even repeated variants and zero-alt rows.
4. avg_alt_reads_high averages alt_reads only across high-impact rows.
5. Keep zero-count samples with NULL average.
6. Sort after final aggregation.

Self-check before final answer:
1. Are the columns exactly ["sample_id", "tissue", "high_impact_call_count", "avg_alt_reads_high"]?
2. Did I follow the row-set rule: Preserve all samples from sample_dim.
3. Did I follow the calculation/projection rule: Count only joined calls whose impact is high.
4. Did I apply the final sort exactly: Sort by high_impact_call_count descending, then sample_id ascending.
5. Did I round only at final output: Round avg_alt_reads_high to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B:** Preserve all samples from sample_dim. Count only joined calls whose impact is high. Include all valid high-impact rows, even repeated variants and zero-alt rows. avg_alt_reads_high averages alt_reads only across high-impact rows. Keep zero-count samples with NULL average. Sort after final aggregation.
- **Gemma 4 26B:** Preserve all samples from sample_dim. Count only joined calls whose impact is high. Include high-impact rows even when alt_reads is zero. avg_alt_reads_high averages alt_reads only across high-impact rows. Keep zero-count samples with NULL average. Sort after final aggregation.
- **Gemma 4 31B:** Preserve all samples from sample_dim. Count only joined calls whose impact is high. avg_alt_reads_high must average alt_reads only across high-impact calls; if a sample has zero high-impact calls, keep the row and use NULL for the average. Do not drop zero-count samples.
- **Phi-4 Mini:** Preserve all samples from sample_dim. Count only joined calls whose impact is high. Include all valid high-impact rows, including repeated variants and zero-alt rows. avg_alt_reads_high averages alt_reads only across high-impact rows. Keep zero-count samples with NULL average. Sort after final aggregation.

## pass2.query8 — SQL — Inner join fact_calls to variant_dim and gene_dim. For each gene_symbol, compute:
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["gene_symbol", "total_alt_reads", "avg_qual", "max_alt_reads"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: gene_symbol, total_alt_reads, avg_qual, max_alt_reads.
- Round avg_qual to 3 decimals.

Task:
Inner join fact_calls to variant_dim and gene_dim.
For each gene_symbol, compute:

* total_alt_reads
* avg_qual
* max_alt_reads
Return: gene_symbol, total_alt_reads, avg_qual, max_alt_reads
Sort by total_alt_reads descending, then gene_symbol ascending.
Round avg_qual to 3 decimals.

Execution rules:
1. Use the joined fact/variant/gene rows only.
2. total_alt_reads is the sum over all joined call rows per gene, not distinct variants.
3. avg_qual and max_alt_reads must be computed from the same grouped rows.
4. Re-apply total_alt_reads DESC, gene_symbol ASC after rounding.

Self-check before final answer:
1. Are the columns exactly ["gene_symbol", "total_alt_reads", "avg_qual", "max_alt_reads"]?
2. Did I follow the row-set rule: Use the joined fact/variant/gene rows only.
3. Did I follow the calculation/projection rule: total_alt_reads is the sum over all joined call rows per gene, not distinct variants.
4. Did I apply the final sort exactly: Sort by total_alt_reads descending, then gene_symbol ascending.
5. Did I round only at final output: Round avg_qual to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use the joined fact/variant/gene rows only. total_alt_reads is the sum over all joined call rows per gene, not distinct variants. avg_qual and max_alt_reads must be computed from the same grouped rows. Re-apply total_alt_reads DESC, gene_symbol ASC after rounding.
- **Gemma 4 31B:** Use the joined fact/variant/gene rows only. total_alt_reads is the sum across all joined call rows per gene, not distinct variants. avg_qual and max_alt_reads must be computed from the same grouped rows. Sort after final aggregation.

## pass2.query9 — SQL — Decision-oriented pathway summary. Use complete inner joins across all four tables
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition", "pathway", "call_count", "mean_vaf", "distinct_samples"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition, pathway, call_count, mean_vaf, distinct_samples.
- Round mean_vaf to 3 decimals.

Task:
Decision-oriented pathway summary.
Use complete inner joins across all four tables.
For each condition and pathway, compute:

* call_count
* mean_vaf where VAF = alt_reads / total_reads
* distinct_samples
Return: condition, pathway, call_count, mean_vaf, distinct_samples
Sort by condition ascending, then pathway ascending.
Round mean_vaf to 3 decimals.

Execution rules:
1. Use only complete-chain rows.
2. Group exactly by condition and pathway from that complete frame.
3. call_count counts fact-call rows.
4. Compute VAF per row, then average VAF values inside each group.
5. distinct_samples counts unique matched samples in the same group.
6. Do not add absent condition-pathway groups.

Self-check before final answer:
1. Are the columns exactly ["condition", "pathway", "call_count", "mean_vaf", "distinct_samples"]?
2. Did I follow the row-set rule: Use only complete-chain rows.
3. Did I follow the calculation/projection rule: Group exactly by condition and pathway from that complete frame.
4. Did I apply the final sort exactly: Sort by condition ascending, then pathway ascending.
5. Did I round only at final output: Round mean_vaf to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use only complete-chain rows. Group exactly by condition and pathway from that complete frame. call_count counts fact-call rows. Compute VAF per row, then average VAF values inside each group. distinct_samples counts unique matched samples in the same group. Do not add absent condition-pathway groups.
- **Gemma 4 31B:** Use only complete-chain rows. Group exactly by condition and pathway; do not invent missing condition-pathway combinations. Compute VAF per call row, then average those VAF values within the group. distinct_samples counts unique matched samples within the same group.

## pass2.query10 — SQL — Coverage screen with sample_dim as the preserving table. Left join sample_dim to fact_call
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["sample_id", "tissue", "total_fact_calls", "complete_chain_calls", "incomplete_chain_calls"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: sample_id, tissue, total_fact_calls, complete_chain_calls, incomplete_chain_calls.
- Do not add rounding rules that the task did not request.

Task:
Coverage screen with sample_dim as the preserving table.
Left join sample_dim to fact_calls, then to variant_dim and gene_dim.
For each sample, compute:

* total_fact_calls
* complete_chain_calls
* incomplete_chain_calls
Return: sample_id, tissue, total_fact_calls, complete_chain_calls, incomplete_chain_calls
Sort by sample_id ascending.

Execution rules:
1. Preserve every sample from sample_dim.
2. total_fact_calls counts all joined fact rows for that sample.
3. complete_chain_calls counts rows with both variant and gene matched.
4. incomplete_chain_calls is the remaining fact-call count.
5. Ensure complete + incomplete equals total for each sample.

Self-check before final answer:
1. Are the columns exactly ["sample_id", "tissue", "total_fact_calls", "complete_chain_calls", "incomplete_chain_calls"]?
2. Did I follow the row-set rule: Preserve every sample from sample_dim.
3. Did I follow the calculation/projection rule: total_fact_calls counts all joined fact rows for that sample.
4. Did I apply the final sort exactly: Sort by sample_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Preserve every sample from sample_dim. total_fact_calls counts all joined fact rows for that sample. complete_chain_calls counts rows with both variant and gene matched. incomplete_chain_calls is the remaining fact-call count. Ensure complete + incomplete equals total for each sample.
- **Gemma 4 31B:** This query was historically stable. Preserve every sample from sample_dim. total_fact_calls counts joined fact rows for that sample. complete_chain_calls counts rows with both variant and gene matched. incomplete_chain_calls is the remaining fact-call count after preserving the sample row.

## pass3.query1 — SQL — Left join fact_calls across the full snowflake and classify each fact row into one join_st
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "sample_id", "variant_id", "join_status"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, sample_id, variant_id, join_status.
- Do not add rounding rules that the task did not request.

Task:
Left join fact_calls across the full snowflake and classify each fact row into one join_status using this logic:

* COMPLETE_CHAIN: sample, variant, and gene all matched
* MISSING_SAMPLE: sample missing but variant and gene matched
* MISSING_GENE: variant matched but gene missing
* MISSING_VARIANT: variant missing
Return: call_id, sample_id, variant_id, join_status
Sort by call_id ascending.

Execution rules:
1. Preserve every fact row exactly once.
2. Assign one and only one join_status per row using the stated logic.
3. MISSING_VARIANT takes precedence over gene status when the variant branch is absent.
4. Do not double-count or emit multiple statuses per fact row.
5. Sort by call_id ASC.

Self-check before final answer:
1. Are the columns exactly ["call_id", "sample_id", "variant_id", "join_status"]?
2. Did I follow the row-set rule: Preserve every fact row exactly once.
3. Did I follow the calculation/projection rule: Assign one and only one join_status per row using the stated logic.
4. Did I apply the final sort exactly: Sort by call_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Preserve every fact row exactly once. Assign one and only one join_status per row using the stated logic. MISSING_VARIANT takes precedence over gene status when the variant branch is absent. Do not double-count or emit multiple statuses per fact row. Sort by call_id ASC.
- **Gemma 4 31B:** This query was historically stable. Preserve every fact row exactly once. Assign one and only one join_status per row using the stated priority. Do not let missing variants also become missing genes. Sort by call_id ASC.

## pass3.query2 — SQL — Using only complete-chain matched rows, group by tissue and gene_symbol. Compute:
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["tissue", "gene_symbol", "call_count", "sum_alt_reads", "avg_vaf", "max_qual"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: tissue, gene_symbol, call_count, sum_alt_reads, avg_vaf, max_qual.
- Round avg_vaf to 3 decimals.

Task:
Using only complete-chain matched rows, group by tissue and gene_symbol.
Compute:

* call_count
* sum_alt_reads
* avg_vaf where VAF = alt_reads / total_reads
* max_qual
Return: tissue, gene_symbol, call_count, sum_alt_reads, avg_vaf, max_qual
Sort by tissue ascending, then gene_symbol ascending.
Round avg_vaf to 3 decimals.

Execution rules:
1. Filter to complete-chain rows before grouping.
2. Group exactly by tissue and gene_symbol from the filtered frame.
3. Compute VAF per call row, then average those values.
4. call_count, sum_alt_reads, avg_vaf, and max_qual must all use the same grouped row set.

Self-check before final answer:
1. Are the columns exactly ["tissue", "gene_symbol", "call_count", "sum_alt_reads", "avg_vaf", "max_qual"]?
2. Did I follow the row-set rule: Filter to complete-chain rows before grouping.
3. Did I follow the calculation/projection rule: Group exactly by tissue and gene_symbol from the filtered frame.
4. Did I apply the final sort exactly: Sort by tissue ascending, then gene_symbol ascending.
5. Did I round only at final output: Round avg_vaf to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Filter to complete-chain rows before grouping. Group exactly by tissue and gene_symbol from the filtered frame. Compute VAF per call row, then average those values. call_count, sum_alt_reads, avg_vaf, and max_qual must all use the same grouped row set.
- **Gemma 4 31B:** Filter to complete-chain rows before grouping. Group exactly by tissue and gene_symbol. Compute VAF per call row, then average it. call_count, sum_alt_reads, avg_vaf, and max_qual must all use the same filtered row set.

## pass3.query3 — SQL — Start from gene_dim and left join to variant_dim, then fact_calls. Return one row per gene
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["gene_symbol", "pathway", "observed_call_count", "total_alt_reads"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: gene_symbol, pathway, observed_call_count, total_alt_reads.
- Round total_alt_reads to 3 decimals if needed.

Task:
Start from gene_dim and left join to variant_dim, then fact_calls.
Return one row per gene with:
gene_symbol, pathway, observed_call_count, total_alt_reads
Count matched fact rows per gene.
Include genes with zero observed calls.
Sort by observed_call_count descending, then gene_symbol ascending.
Round total_alt_reads to 3 decimals if needed.

Execution rules:
1. Use gene_dim as the preserving table.
2. Return one row per gene, including genes with zero observed calls.
3. observed_call_count counts matched fact rows only after joining through variants.
4. total_alt_reads sums only those matched fact rows.
5. Do not count variants as calls.

Self-check before final answer:
1. Are the columns exactly ["gene_symbol", "pathway", "observed_call_count", "total_alt_reads"]?
2. Did I follow the row-set rule: Use gene_dim as the preserving table.
3. Did I follow the calculation/projection rule: Return one row per gene, including genes with zero observed calls.
4. Did I apply the final sort exactly: Sort by observed_call_count descending, then gene_symbol ascending.
5. Did I round only at final output: Round total_alt_reads to 3 decimals if needed.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use gene_dim as the preserving table. Return one row per gene, including genes with zero observed calls. observed_call_count counts matched fact rows only after joining through variants. total_alt_reads sums only those matched fact rows. Do not count variants as calls.
- **Gemma 4 31B:** Use gene_dim as the preserving table. Return one row per gene, including genes with variants but no calls and genes with no variants. observed_call_count counts matched fact rows only. total_alt_reads sums only matched fact rows and should be zero or NULL consistently for no-call genes according to the output rules.

## pass3.query4 — SQL — Inner join fact_calls to sample_dim and variant_dim. Filter to impact = 'high'
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition", "high_impact_call_count", "avg_qual", "avg_alt_reads"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition, high_impact_call_count, avg_qual, avg_alt_reads.
- Round decimal outputs to 3 decimals.

Task:
Inner join fact_calls to sample_dim and variant_dim.
Filter to impact = 'high'.
For each condition, compute:

* high_impact_call_count
* avg_qual
* avg_alt_reads
Return: condition, high_impact_call_count, avg_qual, avg_alt_reads
Sort by condition ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Apply the inner joins first, then filter to impact = 'high'.
2. Group by condition over the filtered joined rows.
3. high_impact_call_count, avg_qual, and avg_alt_reads must all use the same high-impact row set.
4. Do not undercount repeated valid high-impact rows.

Self-check before final answer:
1. Are the columns exactly ["condition", "high_impact_call_count", "avg_qual", "avg_alt_reads"]?
2. Did I follow the row-set rule: Apply the inner joins first, then filter to impact = 'high'.
3. Did I follow the calculation/projection rule: Group by condition over the filtered joined rows.
4. Did I apply the final sort exactly: Sort by condition ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Apply the inner joins first, then filter to impact = 'high'. Group by condition over the filtered joined rows. high_impact_call_count, avg_qual, and avg_alt_reads must all use the same high-impact row set. Do not undercount repeated valid high-impact rows.
- **Gemma 4 31B:** Apply the inner joins first, then filter to impact = 'high'. Group by condition over the filtered joined rows. high_impact_call_count, avg_qual, and avg_alt_reads must all use the same high-impact row set. Re-check the control bucket before final output.

## pass3.query5 — SQL — Using sample_dim as the preserving table, count genotype classes per sample. Compute:
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["sample_id", "heterozygous_calls", "homozygous_alt_calls", "mean_nonref_qual"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: sample_id, heterozygous_calls, homozygous_alt_calls, mean_nonref_qual.
- Round mean_nonref_qual to 3 decimals.

Task:
Using sample_dim as the preserving table, count genotype classes per sample.
Compute:

* heterozygous_calls where genotype = '0/1'
* homozygous_alt_calls where genotype = '1/1'
* mean_nonref_qual over only non-reference calls where genotype in ('0/1','1/1')
Return: sample_id, heterozygous_calls, homozygous_alt_calls, mean_nonref_qual
Include samples with zero calls.
Sort by sample_id ascending.
Round mean_nonref_qual to 3 decimals.

Execution rules:
1. Preserve every sample from sample_dim.
2. Count genotype classes from joined fact rows only.
3. mean_nonref_qual uses only rows with genotype 0/1 or 1/1.
4. Do not include 0/0 rows in the mean.
5. Keep zero-call samples with zero counts and NULL mean.
6. Sort by sample_id ASC.

Self-check before final answer:
1. Are the columns exactly ["sample_id", "heterozygous_calls", "homozygous_alt_calls", "mean_nonref_qual"]?
2. Did I follow the row-set rule: Preserve every sample from sample_dim.
3. Did I follow the calculation/projection rule: Count genotype classes from joined fact rows only.
4. Did I apply the final sort exactly: Sort by sample_id ascending.
5. Did I round only at final output: Round mean_nonref_qual to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Preserve every sample from sample_dim. Count genotype classes from joined fact rows only. mean_nonref_qual uses only rows with genotype 0/1 or 1/1. Do not include 0/0 rows in the mean. Keep zero-call samples with zero counts and NULL mean. Sort by sample_id ASC.
- **Gemma 4 31B:** Preserve every sample from sample_dim. Count genotype classes from joined fact rows only. Do not count reference calls in mean_nonref_qual. Keep zero-call samples with zero counts and NULL mean_nonref_qual. Sort by sample_id ASC.

## pass3.query6 — SQL — Using only complete-chain matched rows, compute total_alt_reads and avg_vaf by tissue and
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["tissue", "gene_symbol", "total_alt_reads", "avg_vaf", "rank_in_tissue"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: tissue, gene_symbol, total_alt_reads, avg_vaf, rank_in_tissue.
- Round avg_vaf to 3 decimals.

Task:
Using only complete-chain matched rows, compute total_alt_reads and avg_vaf by tissue and gene_symbol.
Within each tissue, rank genes by total_alt_reads descending using dense rank.
Return: tissue, gene_symbol, total_alt_reads, avg_vaf, rank_in_tissue
Sort by tissue ascending, then rank_in_tissue ascending, then gene_symbol ascending.
Round avg_vaf to 3 decimals.

Execution rules:
1. Use complete-chain rows only.
2. Aggregate by tissue and gene_symbol before ranking.
3. Compute VAF per row, then average VAF.
4. Dense rank must reset within each tissue and use total_alt_reads DESC.
5. Re-apply tissue ASC, rank ASC, gene_symbol ASC after ranking.

Self-check before final answer:
1. Are the columns exactly ["tissue", "gene_symbol", "total_alt_reads", "avg_vaf", "rank_in_tissue"]?
2. Did I follow the row-set rule: Use complete-chain rows only.
3. Did I follow the calculation/projection rule: Aggregate by tissue and gene_symbol before ranking.
4. Did I apply the final sort exactly: Sort by tissue ascending, then rank_in_tissue ascending, then gene_symbol ascending.
5. Did I round only at final output: Round avg_vaf to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use complete-chain rows only. Aggregate by tissue and gene_symbol before ranking. Compute VAF per row, then average VAF. Dense rank must reset within each tissue and use total_alt_reads DESC. Re-apply tissue ASC, rank ASC, gene_symbol ASC after ranking.
- **Gemma 4 31B:** Use complete-chain rows only. Aggregate by tissue and gene_symbol before ranking. Compute VAF per row, then average it. Dense rank must reset within each tissue and use total_alt_reads DESC. Re-apply the requested final sort after ranking.

## pass3.query7 — SQL — Find unused dimension rows across both branches using anti-join logic. Return: object_type
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["object_type", "object_id", "reason"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: object_type, object_id, reason.
- Do not add rounding rules that the task did not request.

Task:
Find unused dimension rows across both branches using anti-join logic.
Return: object_type, object_id, reason
Use these rules:

* sample_dim rows with no fact_calls => no_fact_calls
* variant_dim rows with no fact_calls => no_fact_calls
* gene_dim rows with variants but no fact_calls through those variants => no_fact_calls_through_variants
* gene_dim rows with no variants at all => no_variants_attached
Sort by object_type ascending, then object_id ascending.

Execution rules:
1. Run each anti-join rule separately, then union the outputs.
2. Use the exact object_type and reason labels from the prompt.
3. Keep gene cases with no variants separate from gene cases with variants but no fact calls.
4. Sort only after the union.

Self-check before final answer:
1. Are the columns exactly ["object_type", "object_id", "reason"]?
2. Did I follow the row-set rule: Run each anti-join rule separately, then union the outputs.
3. Did I follow the calculation/projection rule: Use the exact object_type and reason labels from the prompt.
4. Did I apply the final sort exactly: Sort by object_type ascending, then object_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Run each anti-join rule separately, then union the outputs. Use the exact object_type and reason labels from the prompt. Keep gene cases with no variants separate from gene cases with variants but no fact calls. Sort only after the union.
- **Gemma 4 31B:** This query was historically stable. Use exact object_type and reason labels from the prompt. Keep the anti-join categories separate; do not merge gene cases with no variants and gene cases with variants but no calls. Sort last.

## pass3.query8 — SQL — Using complete-chain matched rows only, filter to non-reference calls where genotype <> '0
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition", "gene_role", "non_reference_call_count", "mean_vaf"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition, gene_role, non_reference_call_count, mean_vaf.
- Round mean_vaf to 3 decimals.

Task:
Using complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0'.
Group by condition and gene_role.
Return: condition, gene_role, non_reference_call_count, mean_vaf
Sort by condition ascending, then gene_role ascending.
Round mean_vaf to 3 decimals.

Execution rules:
1. Filter to complete-chain rows first, then genotype <> '0/0'.
2. Group only by condition and gene_role from the filtered frame.
3. non_reference_call_count counts filtered call rows.
4. Compute VAF per row, then average those values.
5. Do not leak reference or incomplete-chain rows.

Self-check before final answer:
1. Are the columns exactly ["condition", "gene_role", "non_reference_call_count", "mean_vaf"]?
2. Did I follow the row-set rule: Filter to complete-chain rows first, then genotype <> '0/0'.
3. Did I follow the calculation/projection rule: Group only by condition and gene_role from the filtered frame.
4. Did I apply the final sort exactly: Sort by condition ascending, then gene_role ascending.
5. Did I round only at final output: Round mean_vaf to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Filter to complete-chain rows first, then genotype <> '0/0'. Group only by condition and gene_role from the filtered frame. non_reference_call_count counts filtered call rows. Compute VAF per row, then average those values. Do not leak reference or incomplete-chain rows.
- **Gemma 4 31B:** Filter to complete-chain rows first, then genotype <> '0/0'. Group only by condition and gene_role. Compute VAF per filtered call row and average those values. Do not leak reference, orphan, or incomplete-chain rows into the mean_vaf.

## pass3.query9 — SQL — Failure-family audit for operational review. Left join fact_calls across the full snowflak
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition_group", "complete_chain_calls", "missing_sample_calls", "missing_variant_calls", "missing_gene_calls"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition_group, complete_chain_calls, missing_sample_calls, missing_variant_calls, missing_gene_calls.
- Do not add rounding rules that the task did not request.

Task:
Failure-family audit for operational review.
Left join fact_calls across the full snowflake.
Create condition_group = condition when sample matched, else 'UNMATCHED_SAMPLE'.
For each condition_group, compute:

* complete_chain_calls
* missing_sample_calls
* missing_variant_calls
* missing_gene_calls
Return: condition_group, complete_chain_calls, missing_sample_calls, missing_variant_calls, missing_gene_calls
Sort by condition_group ascending.

Execution rules:
1. Preserve all fact rows after the full snowflake left join.
2. First classify each fact row into one status category, then aggregate by condition_group.
3. condition_group is the matched condition when sample exists; otherwise use UNMATCHED_SAMPLE.
4. Do not double-count one row across multiple missing categories.

Self-check before final answer:
1. Are the columns exactly ["condition_group", "complete_chain_calls", "missing_sample_calls", "missing_variant_calls", "missing_gene_calls"]?
2. Did I follow the row-set rule: Preserve all fact rows after the full snowflake left join.
3. Did I follow the calculation/projection rule: First classify each fact row into one status category, then aggregate by condition_group.
4. Did I apply the final sort exactly: Sort by condition_group ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Preserve all fact rows after the full snowflake left join. First classify each fact row into one status category, then aggregate by condition_group. condition_group is the matched condition when sample exists; otherwise use UNMATCHED_SAMPLE. Do not double-count one row across multiple missing categories.
- **Gemma 4 31B:** Preserve all fact rows after the full snowflake left join. First classify each row into its correct missing/complete status, then aggregate by condition_group. condition_group is the matched condition when sample exists; otherwise use UNMATCHED_SAMPLE. Do not double-count one row across multiple missing categories.

## pass3.query10 — SQL — Decision-priority candidate table. Using complete-chain matched rows only, filter to non-r
```text
/no_think

You are completing an automated SQL-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["gene_symbol", "non_reference_calls", "avg_vaf", "avg_matched_expr", "decision_score"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: gene_symbol, non_reference_calls, avg_vaf, avg_matched_expr, decision_score.
- Round decimals to 3 places.

Task:
Decision-priority candidate table.
Using complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0'.
Map matched expression counts using:

* NDHB -> expr_ndhb
* NDHK -> expr_ndhk
* PGR5 -> expr_pgr5
For each gene_symbol, compute:
* non_reference_calls
* avg_vaf
* avg_matched_expr
* decision_score = avg_vaf * avg_matched_expr
Return: gene_symbol, non_reference_calls, avg_vaf, avg_matched_expr, decision_score
Sort by decision_score descending, then gene_symbol ascending.
Round decimals to 3 places.

Execution rules:
1. Use only complete-chain non-reference rows.
2. Apply the matched-expression mapping by gene_symbol before grouping.
3. non_reference_calls counts filtered call rows.
4. Compute VAF per row, average VAF and matched expression by gene, then compute decision_score from the final grouped averages.
5. Sort last.

Self-check before final answer:
1. Are the columns exactly ["gene_symbol", "non_reference_calls", "avg_vaf", "avg_matched_expr", "decision_score"]?
2. Did I follow the row-set rule: Use only complete-chain non-reference rows.
3. Did I follow the calculation/projection rule: Apply the matched-expression mapping by gene_symbol before grouping.
4. Did I apply the final sort exactly: Sort by decision_score descending, then gene_symbol ascending.
5. Did I round only at final output: Round decimals to 3 places.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use only complete-chain non-reference rows. Apply the matched-expression mapping by gene_symbol before grouping. non_reference_calls counts filtered call rows. Compute VAF per row, average VAF and matched expression by gene, then compute decision_score from the final grouped averages. Sort last.
- **Gemma 4 31B:** Use only complete-chain non-reference rows. Apply the matched-expression mapping by gene_symbol before grouping. Compute VAF per call row, average VAF and matched expression by gene, then compute decision_score from the final grouped averages. Sort after rounding checks.

## pass4.query1 — PANDAS — Using pandas, create a reconciliation summary with exactly these metrics: fact_rows_total
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["metric", "value"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: metric, value.
- Do not add rounding rules that the task did not request.

Task:
Using pandas, create a reconciliation summary with exactly these metrics:

* fact_rows_total
* complete_chain_rows
* fact_rows_missing_sample
* fact_rows_missing_variant
* fact_rows_missing_gene
* unused_samples
* unused_variants
* genes_with_no_variants
Return: metric, value
Preserve this exact row order.

Execution rules:
1. Compute each reconciliation metric from its correct source grain.
2. fact-row metrics start from fact_calls.
3. unused sample, variant, and gene metrics start from the relevant dimension table.
4. Do not reuse a single filtered frame for all metrics.
5. Preserve the metric row order exactly.

Self-check before final answer:
1. Are the columns exactly ["metric", "value"]?
2. Did I follow the row-set rule: Compute each reconciliation metric from its correct source grain.
3. Did I follow the calculation/projection rule: fact-row metrics start from fact_calls.
4. Did I preserve the exact requested row order?
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Compute each reconciliation metric from its correct source grain. fact-row metrics start from fact_calls. unused sample, variant, and gene metrics start from the relevant dimension table. Do not reuse a single filtered frame for all metrics. Preserve the metric row order exactly.
- **Gemma 4 31B:** Compute each reconciliation metric from the correct source grain. Do not reuse one filtered frame for all metrics. fact-row metrics start from fact_calls; unused dimension metrics start from the relevant dimension table. Preserve the metric row order exactly as listed.

## pass4.query2 — PANDAS — Using pandas and complete-chain matched rows only, group by condition and pathway. Compute
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition", "pathway", "call_count", "total_alt_reads", "mean_qual", "avg_expr_ndhb"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition, pathway, call_count, total_alt_reads, mean_qual, avg_expr_ndhb.
- Round decimal outputs to 3 decimals.

Task:
Using pandas and complete-chain matched rows only, group by condition and pathway.
Compute:

* call_count
* total_alt_reads
* mean_qual
* avg_expr_ndhb
Return: condition, pathway, call_count, total_alt_reads, mean_qual, avg_expr_ndhb
Sort by condition ascending, then total_alt_reads descending, then pathway ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Build the complete-chain pandas frame first and only then group by condition and pathway.
2. call_count, total_alt_reads, mean_qual, and avg_expr_ndhb must all use that same complete-chain row set.
3. Do not add absent condition-pathway groups.
4. Sort after aggregation.

Self-check before final answer:
1. Are the columns exactly ["condition", "pathway", "call_count", "total_alt_reads", "mean_qual", "avg_expr_ndhb"]?
2. Did I follow the row-set rule: Build the complete-chain pandas frame first and only then group by condition and pathway.
3. Did I follow the calculation/projection rule: call_count, total_alt_reads, mean_qual, and avg_expr_ndhb must all use that same complete-chain row set.
4. Did I apply the final sort exactly: Sort by condition ascending, then total_alt_reads descending, then pathway ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Build the complete-chain pandas frame first and only then group by condition and pathway. call_count, total_alt_reads, mean_qual, and avg_expr_ndhb must all use that same complete-chain row set. Do not add absent condition-pathway groups. Sort after aggregation.
- **Gemma 4 31B:** Build the complete-chain pandas frame first and only then group by condition and pathway. call_count, total_alt_reads, mean_qual, and avg_expr_ndhb must all use that same complete-chain row set. Do not add condition-pathway groups that are absent after filtering.

## pass4.query3 — PANDAS — Using pandas and complete-chain non-reference rows only where genotype <> '0/0', group by
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["batch", "gene_role", "non_reference_calls", "avg_qual", "max_vaf", "mean_expr_pgr5"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: batch, gene_role, non_reference_calls, avg_qual, max_vaf, mean_expr_pgr5.
- Round decimal outputs to 3 decimals.

Task:
Using pandas and complete-chain non-reference rows only where genotype <> '0/0', group by batch and gene_role.
Compute:

* non_reference_calls
* avg_qual
* max_vaf
* mean_expr_pgr5
Return: batch, gene_role, non_reference_calls, avg_qual, max_vaf, mean_expr_pgr5
Sort by batch ascending, then gene_role ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Filter in this order: complete-chain rows first, then genotype <> '0/0'.
2. Group only by batch and gene_role from the filtered rows.
3. Compute VAF per row before max_vaf.
4. non_reference_calls, avg_qual, max_vaf, and mean_expr_pgr5 must use the same filtered frame.

Self-check before final answer:
1. Are the columns exactly ["batch", "gene_role", "non_reference_calls", "avg_qual", "max_vaf", "mean_expr_pgr5"]?
2. Did I follow the row-set rule: Filter in this order: complete-chain rows first, then genotype <> '0/0'.
3. Did I follow the calculation/projection rule: Group only by batch and gene_role from the filtered rows.
4. Did I apply the final sort exactly: Sort by batch ascending, then gene_role ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Filter in this order: complete-chain rows first, then genotype <> '0/0'. Group only by batch and gene_role from the filtered rows. Compute VAF per row before max_vaf. non_reference_calls, avg_qual, max_vaf, and mean_expr_pgr5 must use the same filtered frame.
- **Gemma 4 31B:** Filter in this order: complete-chain rows first, then genotype <> '0/0'. Group only by batch and gene_role from the filtered rows. Compute VAF per row before max_vaf. Do not leak reference rows, incomplete-chain rows, or invalid batch/role groups.

## pass4.query4 — PANDAS — Using pandas and complete-chain matched rows only, find genes observed in both: control
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["gene_symbol", "control_calls", "non_control_calls", "total_alt_reads"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: gene_symbol, control_calls, non_control_calls, total_alt_reads.
- Do not add rounding rules that the task did not request.

Task:
Using pandas and complete-chain matched rows only, find genes observed in both:

* control
* at least one non-control condition
Return:
* gene_symbol
* control_calls
* non_control_calls
* total_alt_reads
Sort by total_alt_reads descending, then gene_symbol ascending.

Execution rules:
1. Use complete-chain rows only.
2. Identify shared genes by requiring at least one control call and at least one non-control call for the same gene.
3. Exclude genes present in only one side.
4. Compute control_calls, non_control_calls, and total_alt_reads after the shared-gene set is fixed.

Self-check before final answer:
1. Are the columns exactly ["gene_symbol", "control_calls", "non_control_calls", "total_alt_reads"]?
2. Did I follow the row-set rule: Use complete-chain rows only.
3. Did I follow the calculation/projection rule: Identify shared genes by requiring at least one control call and at least one non-control call for the same gene.
4. Did I apply the final sort exactly: Sort by total_alt_reads descending, then gene_symbol ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use complete-chain rows only. Identify shared genes by requiring at least one control call and at least one non-control call for the same gene. Exclude genes present in only one side. Compute control_calls, non_control_calls, and total_alt_reads after the shared-gene set is fixed.
- **Gemma 4 31B:** Use complete-chain rows only. Determine shared genes by requiring at least one control call and at least one non-control call for the same gene. Exclude genes present in only one side. Compute control_calls, non_control_calls, and total_alt_reads from the same shared-gene filtered frame.

## pass4.query5 — PANDAS — Using pandas, start from gene_dim and left join to variant_dim, then fact_calls, then samp
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["gene_symbol", "variant_count", "call_count", "distinct_matched_sample_count", "distinct_tissue_count", "avg_matched_expression"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: gene_symbol, variant_count, call_count, distinct_matched_sample_count, distinct_tissue_count, avg_matched_expression.
- Round avg_matched_expression to 3 decimals.

Task:
Using pandas, start from gene_dim and left join to variant_dim, then fact_calls, then sample_dim.
Return one row per gene with:

* gene_symbol
* variant_count
* call_count
* distinct_matched_sample_count
* distinct_tissue_count
* avg_matched_expression
For distinct_matched_sample_count, count only sample_dim matches and exclude orphan fact sample keys.
For avg_matched_expression, use the matched expression mapping from the instructions and average across matched sample-call rows only.
Sort by gene_symbol ascending.
Round avg_matched_expression to 3 decimals.

Execution rules:
1. Use gene_dim as the preserving frame.
2. variant_count counts distinct variants attached to each gene.
3. call_count counts matched fact rows after joining through variants.
4. distinct_matched_sample_count and distinct_tissue_count count only successful sample_dim matches.
5. avg_matched_expression averages mapped expression only across matched sample-call rows.

Self-check before final answer:
1. Are the columns exactly ["gene_symbol", "variant_count", "call_count", "distinct_matched_sample_count", "distinct_tissue_count", "avg_matched_expression"]?
2. Did I follow the row-set rule: Use gene_dim as the preserving frame.
3. Did I follow the calculation/projection rule: variant_count counts distinct variants attached to each gene.
4. Did I apply the final sort exactly: Sort by gene_symbol ascending.
5. Did I round only at final output: Round avg_matched_expression to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use gene_dim as the preserving frame. variant_count counts distinct variants attached to each gene. call_count counts matched fact rows after joining through variants. distinct_matched_sample_count and distinct_tissue_count count only successful sample_dim matches. avg_matched_expression averages mapped expression only across matched sample-call rows.
- **Gemma 4 31B:** Use gene_dim as the preserving frame. variant_count counts distinct variants attached to each gene. call_count counts matched fact rows after joining through variants. For sample and tissue counts, count only successfully matched sample_dim rows. For avg_matched_expression, map by gene_symbol and average only matched sample-call rows.

## pass4.query6 — PANDAS — Using pandas, compute sample-level burden. Use complete-chain matched rows only, filter to
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["sample_id", "tissue", "burden_genes", "mean_log2_marker_expr"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: sample_id, tissue, burden_genes, mean_log2_marker_expr.
- Round mean_log2_marker_expr to 3 decimals.

Task:
Using pandas, compute sample-level burden.
Use complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0' and impact IN ('high', 'moderate').
For each sample in sample_dim, compute:

* burden_genes = count of distinct genes meeting that rule
* mean_log2_marker_expr = mean(log2(expr_ndhb+1), log2(expr_pgr5+1), log2(expr_ndhk+1))
Return: sample_id, tissue, burden_genes, mean_log2_marker_expr
Include samples with zero burden.
Sort by burden_genes descending, then sample_id ascending.
Round mean_log2_marker_expr to 3 decimals.

Execution rules:
1. Preserve every sample from sample_dim.
2. Compute burden_genes from complete-chain, non-reference, high/moderate calls only.
3. Compute mean_log2_marker_expr from each sample's own three expression markers, independent of burden.
4. Include zero-burden samples and sort after final calculations.

Self-check before final answer:
1. Are the columns exactly ["sample_id", "tissue", "burden_genes", "mean_log2_marker_expr"]?
2. Did I follow the row-set rule: Preserve every sample from sample_dim.
3. Did I follow the calculation/projection rule: Compute burden_genes from complete-chain, non-reference, high/moderate calls only.
4. Did I apply the final sort exactly: Sort by burden_genes descending, then sample_id ascending.
5. Did I round only at final output: Round mean_log2_marker_expr to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Preserve every sample from sample_dim. Compute burden_genes from complete-chain, non-reference, high/moderate calls only. Compute mean_log2_marker_expr from each sample's own three expression markers, independent of burden. Include zero-burden samples and sort after final calculations.
- **Gemma 4 31B:** Preserve every sample from sample_dim. Compute burden_genes from complete-chain, non-reference, high/moderate calls only. Compute mean_log2_marker_expr from each sample's own expression markers, independent of burden. Include zero-burden samples and apply the requested sort last.

## pass4.query7 — PANDAS — Using pandas, build a single orphan-key report using concat/union-style logic. Return: sou
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["source_table", "key_value", "orphan_type"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: source_table, key_value, orphan_type.
- Do not add rounding rules that the task did not request.

Task:
Using pandas, build a single orphan-key report using concat/union-style logic.
Return: source_table, key_value, orphan_type
Include:

* fact_calls.sample_id values missing in sample_dim
* fact_calls.variant_id values missing in variant_dim
* variant_dim.gene_id values missing in gene_dim
* sample_dim.sample_id rows unused by fact_calls
* variant_dim.variant_id rows unused by fact_calls
* gene_dim.gene_id rows with no variants attached
Sort by source_table ascending, then key_value ascending.

Execution rules:
1. Create each orphan category separately, then concatenate with exact labels.
2. Keep source_table and orphan_type tied to the specific rule that produced the row.
3. Do not collapse distinct orphan sources into generic labels.
4. Remove only true duplicates within the same category, then sort.

Self-check before final answer:
1. Are the columns exactly ["source_table", "key_value", "orphan_type"]?
2. Did I follow the row-set rule: Create each orphan category separately, then concatenate with exact labels.
3. Did I follow the calculation/projection rule: Keep source_table and orphan_type tied to the specific rule that produced the row.
4. Did I apply the final sort exactly: Sort by source_table ascending, then key_value ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Create each orphan category separately, then concatenate with exact labels. Keep source_table and orphan_type tied to the specific rule that produced the row. Do not collapse distinct orphan sources into generic labels. Remove only true duplicates within the same category, then sort.
- **Gemma 4 31B:** Create each orphan category separately, then concatenate with exact labels. Use precise source_table labels matching the key path, not broad table names. Do not collapse different orphan types together. Remove only true duplicate rows within the same category, then sort as requested.

## pass4.query8 — PANDAS — Using pandas, produce a final presentation table for all non-reference complete-chain call
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "plant_line_id", "tissue", "condition", "gene_symbol", "pathway", "variant_id", "impact", "genotype", "alt_reads", "total_reads", "vaf", "matched_expr_count", "log2_matched_expr", "qual"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, plant_line_id, tissue, condition, gene_symbol, pathway, variant_id, impact, genotype, alt_reads, total_reads, vaf, matched_expr_count, log2_matched_expr, qual.
- Round vaf and log2_matched_expr to 3 decimals.

Task:
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

Execution rules:
1. Use complete-chain rows only, then filter to genotype <> '0/0'.
2. Preserve the exact requested column order.
3. Compute VAF per row and map matched_expr_count by gene_symbol.
4. Use numpy.log2(matched_expr_count + 1).
5. Re-apply the full five-key sort after derived columns and rounding.

Self-check before final answer:
1. Are the columns exactly ["call_id", "plant_line_id", "tissue", "condition", "gene_symbol", "pathway", "variant_id", "impact", "genotype", "alt_reads", "total_reads", "vaf", "matched_expr_count", "log2_matched_expr", "qual"]?
2. Did I follow the row-set rule: Use complete-chain rows only, then filter to genotype <> '0/0'.
3. Did I follow the calculation/projection rule: Preserve the exact requested column order.
4. Did I apply the final sort exactly: Sort by: condition ascending, tissue ascending, gene_symbol ascending, variant_id ascending, call_id ascending.
5. Did I round only at final output: Round vaf and log2_matched_expr to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use complete-chain rows only, then filter to genotype <> '0/0'. Preserve the exact requested column order. Compute VAF per row and map matched_expr_count by gene_symbol. Use numpy.log2(matched_expr_count + 1). Re-apply the full five-key sort after derived columns and rounding.
- **Gemma 4 31B:** Use complete-chain rows only, then filter non-reference rows. Preserve the exact column order. Compute VAF per row and map matched_expr_count by gene_symbol. Use numpy.log2(matched_expr_count + 1). Re-apply the full five-key sort after all derived columns are calculated.

## pass4.query9 — PANDAS — Using pandas and complete-chain matched rows only, build a pathway reliability summary. Fo
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["pathway", "call_count", "non_reference_rate", "mean_vaf", "mean_matched_expr"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: pathway, call_count, non_reference_rate, mean_vaf, mean_matched_expr.
- Round decimals to 3 places.

Task:
Using pandas and complete-chain matched rows only, build a pathway reliability summary.
For each pathway, compute:

* call_count
* non_reference_rate where genotype <> '0/0'
* mean_vaf
* mean_matched_expr
Return: pathway, call_count, non_reference_rate, mean_vaf, mean_matched_expr
Sort by non_reference_rate descending, then pathway ascending.
Round decimals to 3 places.

Execution rules:
1. Use complete-chain rows only.
2. call_count is all complete-chain calls per pathway.
3. non_reference_rate is non-reference complete-chain calls divided by all complete-chain calls in that pathway.
4. Compute VAF per row.
5. mean_vaf and mean_matched_expr must use the correct complete-chain row set with matched expression mapped by gene_symbol.

Self-check before final answer:
1. Are the columns exactly ["pathway", "call_count", "non_reference_rate", "mean_vaf", "mean_matched_expr"]?
2. Did I follow the row-set rule: Use complete-chain rows only.
3. Did I follow the calculation/projection rule: call_count is all complete-chain calls per pathway.
4. Did I apply the final sort exactly: Sort by non_reference_rate descending, then pathway ascending.
5. Did I round only at final output: Round decimals to 3 places.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use complete-chain rows only. call_count is all complete-chain calls per pathway. non_reference_rate is non-reference complete-chain calls divided by all complete-chain calls in that pathway. Compute VAF per row. mean_vaf and mean_matched_expr must use the correct complete-chain row set with matched expression mapped by gene_symbol.
- **Gemma 4 31B:** Use complete-chain rows only. call_count is all complete-chain calls per pathway. non_reference_rate is non-reference complete-chain calls divided by all complete-chain calls in the pathway. mean_vaf and mean_matched_expr must be computed from the correct complete-chain row set, with matched expression mapped by gene_symbol.

## pass4.query10 — PANDAS — Using pandas, create a repairability audit over all fact rows. Left join fact_calls across
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "sample_id", "variant_id", "join_status", "repairable_by_human"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, sample_id, variant_id, join_status, repairable_by_human.
- Do not add rounding rules that the task did not request.

Task:
Using pandas, create a repairability audit over all fact rows.
Left join fact_calls across the full snowflake and classify join_status using:

* COMPLETE_CHAIN
* MISSING_SAMPLE
* MISSING_GENE
* MISSING_VARIANT
Set repairable_by_human = True only for MISSING_SAMPLE and MISSING_GENE.
Return: call_id, sample_id, variant_id, join_status, repairable_by_human
Sort by call_id ascending.

Execution rules:
1. Preserve all fact rows and classify exactly one join_status per row.
2. Set repairable_by_human to True only for MISSING_SAMPLE and MISSING_GENE, never for COMPLETE_CHAIN or MISSING_VARIANT.
3. Do not overwrite classification after later joins.
4. Sort by call_id ASC.

Self-check before final answer:
1. Are the columns exactly ["call_id", "sample_id", "variant_id", "join_status", "repairable_by_human"]?
2. Did I follow the row-set rule: Preserve all fact rows and classify exactly one join_status per row.
3. Did I follow the calculation/projection rule: Set repairable_by_human to True only for MISSING_SAMPLE and MISSING_GENE, never for COMPLETE_CHAIN or MISSING_VARIANT.
4. Did I apply the final sort exactly: Sort by call_id ascending.
5. Did I avoid unrequested rounding or value formatting changes?
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Preserve all fact rows and classify exactly one join_status per row. Set repairable_by_human to True only for MISSING_SAMPLE and MISSING_GENE, never for COMPLETE_CHAIN or MISSING_VARIANT. Do not overwrite classification after later joins. Sort by call_id ASC.
- **Gemma 4 31B:** This query was historically stable. Preserve all fact rows and classify exactly one join_status per row. Set repairable_by_human to True only for MISSING_SAMPLE and MISSING_GENE, never for COMPLETE_CHAIN or MISSING_VARIANT. Sort by call_id ASC.

## pass5.query1 — PANDAS — Using pandas and sample_dim only, compute these expression features for every sample: log2
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["sample_id", "tissue", "log2_expr_ndhb", "log2_expr_pgr5", "log2_expr_ndhk", "ndh_module_ratio"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: sample_id, tissue, log2_expr_ndhb, log2_expr_pgr5, log2_expr_ndhk, ndh_module_ratio.
- Round all derived decimals to 3 decimals.

Task:
Using pandas and sample_dim only, compute these expression features for every sample:

* log2_expr_ndhb = log2(expr_ndhb + 1)
* log2_expr_pgr5 = log2(expr_pgr5 + 1)
* log2_expr_ndhk = log2(expr_ndhk + 1)
* ndh_module_ratio = (expr_ndhb + expr_ndhk) / (expr_ndhb + expr_pgr5 + expr_ndhk)
Return: sample_id, tissue, log2_expr_ndhb, log2_expr_pgr5, log2_expr_ndhk, ndh_module_ratio
Sort by sample_id ascending.
Round all derived decimals to 3 decimals.

Execution rules:
1. Use sample_dim only; do not join to fact_calls.
2. Compute each log2 feature with numpy.log2(x + 1).
3. Compute ndh_module_ratio from raw expression values, not log-transformed values.
4. Use the same raw denominator for the ratio.
5. Round only after all derived columns are complete.

Self-check before final answer:
1. Are the columns exactly ["sample_id", "tissue", "log2_expr_ndhb", "log2_expr_pgr5", "log2_expr_ndhk", "ndh_module_ratio"]?
2. Did I follow the row-set rule: Use sample_dim only; do not join to fact_calls.
3. Did I follow the calculation/projection rule: Compute each log2 feature with numpy.log2(x + 1).
4. Did I apply the final sort exactly: Sort by sample_id ascending.
5. Did I round only at final output: Round all derived decimals to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use sample_dim only; do not join to fact_calls. Compute each log2 feature with numpy.log2(x + 1). Compute ndh_module_ratio from raw expression values, not log-transformed values. Use the same raw denominator for the ratio. Round only after all derived columns are complete.
- **Gemma 4 31B:** Use sample_dim only; do not join to fact_calls. Compute each log2 feature with numpy.log2(x + 1). Compute ndh_module_ratio from raw expression values, not log-transformed values. Round only after all derived columns are complete.

## pass5.query2 — PANDAS — Using pandas and complete-chain matched rows only, map matched expression by gene_symbol u
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["call_id", "gene_symbol", "matched_expr_count", "log2_matched_expr", "vaf", "expr_weighted_vaf"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: call_id, gene_symbol, matched_expr_count, log2_matched_expr, vaf, expr_weighted_vaf.
- Round derived decimals to 3 decimals.

Task:
Using pandas and complete-chain matched rows only, map matched expression by gene_symbol using the standard mapping.
Compute:

* matched_expr_count
* log2_matched_expr = log2(matched_expr_count + 1)
* vaf = alt_reads / total_reads
* expr_weighted_vaf = vaf * log2_matched_expr
Return: call_id, gene_symbol, matched_expr_count, log2_matched_expr, vaf, expr_weighted_vaf
Sort by call_id ascending.
Round derived decimals to 3 decimals.

Execution rules:
1. Build the complete-chain matched frame first.
2. Exclude incomplete-chain, orphan, and unmatched rows.
3. Map matched_expr_count by gene_symbol before deriving log2_matched_expr.
4. Compute VAF per row, then expr_weighted_vaf per row.
5. Do not average before row-level calculations.
6. Sort by call_id ASC.

Self-check before final answer:
1. Are the columns exactly ["call_id", "gene_symbol", "matched_expr_count", "log2_matched_expr", "vaf", "expr_weighted_vaf"]?
2. Did I follow the row-set rule: Build the complete-chain matched frame first.
3. Did I follow the calculation/projection rule: Exclude incomplete-chain, orphan, and unmatched rows.
4. Did I apply the final sort exactly: Sort by call_id ascending.
5. Did I round only at final output: Round derived decimals to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Build the complete-chain matched frame first. Exclude incomplete-chain, orphan, and unmatched rows. Map matched_expr_count by gene_symbol before deriving log2_matched_expr. Compute VAF per row, then expr_weighted_vaf per row. Do not average before row-level calculations. Sort by call_id ASC.
- **Gemma 4 31B:** Build the complete-chain matched frame first. Do not include incomplete-chain, orphan, or unmatched rows. Map matched_expr_count by gene_symbol, compute log2 with numpy.log2(x + 1), compute VAF per row, then expr_weighted_vaf per row. Sort by call_id ASC after calculations.

## pass5.query3 — PANDAS — Using pandas and complete-chain matched rows only, group by condition and gene_symbol. Com
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition", "gene_symbol", "n_calls", "mean_matched_expr", "median_matched_expr", "pop_std_matched_expr"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition, gene_symbol, n_calls, mean_matched_expr, median_matched_expr, pop_std_matched_expr.
- Round decimal outputs to 3 decimals.

Task:
Using pandas and complete-chain matched rows only, group by condition and gene_symbol.
Compute:

* n_calls
* mean_matched_expr
* median_matched_expr
* pop_std_matched_expr using ddof=0
Return: condition, gene_symbol, n_calls, mean_matched_expr, median_matched_expr, pop_std_matched_expr
Sort by condition ascending, then gene_symbol ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Use complete-chain rows only and map matched expression by gene_symbol before grouping.
2. n_calls counts rows in each condition/gene group.
3. mean, median, and population standard deviation must use the same matched-expression series.
4. Use ddof=0.
5. Sort by condition ASC, gene_symbol ASC after rounding.

Self-check before final answer:
1. Are the columns exactly ["condition", "gene_symbol", "n_calls", "mean_matched_expr", "median_matched_expr", "pop_std_matched_expr"]?
2. Did I follow the row-set rule: Use complete-chain rows only and map matched expression by gene_symbol before grouping.
3. Did I follow the calculation/projection rule: n_calls counts rows in each condition/gene group.
4. Did I apply the final sort exactly: Sort by condition ascending, then gene_symbol ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use complete-chain rows only and map matched expression by gene_symbol before grouping. n_calls counts rows in each condition/gene group. mean, median, and population standard deviation must use the same matched-expression series. Use ddof=0. Sort by condition ASC, gene_symbol ASC after rounding.
- **Gemma 4 31B:** Use complete-chain rows only and map matched expression by gene_symbol before grouping. n_calls counts rows in each condition/gene group. Use population standard deviation with ddof=0. Re-apply condition ASC, gene_symbol ASC after rounding checks.

## pass5.query4 — PANDAS — Using pandas and sample_dim only, define: stress_group = 'stress' for conditions high_ligh
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["gene_symbol", "stress_mean_log2", "control_mean_log2", "delta_log2_stress_minus_control"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: gene_symbol, stress_mean_log2, control_mean_log2, delta_log2_stress_minus_control.
- Round decimal outputs to 3 decimals.

Task:
Using pandas and sample_dim only, define:

* stress_group = 'stress' for conditions high_light or drought
* stress_group = 'control' for condition control
For each gene marker (NDHB, NDHK, PGR5), compute:
* stress_mean_log2
* control_mean_log2
* delta_log2_stress_minus_control
Use:
* NDHB from expr_ndhb
* NDHK from expr_ndhk
* PGR5 from expr_pgr5
Apply log2(x + 1) before averaging.
Return: gene_symbol, stress_mean_log2, control_mean_log2, delta_log2_stress_minus_control
Sort by gene_symbol ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Use sample_dim only.
2. Apply numpy.log2(x + 1) to each sample's marker expression before computing group means.
3. Compute delta as stress_mean_log2 minus control_mean_log2.
4. Do not average raw expression before log transformation.
5. Sort by gene_symbol ASC.

Self-check before final answer:
1. Are the columns exactly ["gene_symbol", "stress_mean_log2", "control_mean_log2", "delta_log2_stress_minus_control"]?
2. Did I follow the row-set rule: Use sample_dim only.
3. Did I follow the calculation/projection rule: Apply numpy.log2(x + 1) to each sample's marker expression before computing group means.
4. Did I apply the final sort exactly: Sort by gene_symbol ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use sample_dim only. Apply numpy.log2(x + 1) to each sample's marker expression before computing group means. Compute delta as stress_mean_log2 minus control_mean_log2. Do not average raw expression before log transformation. Sort by gene_symbol ASC.
- **Gemma 4 31B:** Use sample_dim only. Apply numpy.log2(x + 1) to each sample's marker expression before computing stress and control means. Compute delta as stress_mean_log2 minus control_mean_log2. Do not average raw expression before log transformation.

## pass5.query5 — PANDAS — Using pandas and complete-chain non-reference rows only where genotype <> '0/0', group by
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["pathway", "tissue", "non_reference_calls", "mean_vaf", "mean_log2_matched_expr", "burden_score"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: pathway, tissue, non_reference_calls, mean_vaf, mean_log2_matched_expr, burden_score.
- Round decimal outputs to 3 decimals.

Task:
Using pandas and complete-chain non-reference rows only where genotype <> '0/0', group by pathway and tissue.
Compute:

* non_reference_calls
* mean_vaf
* mean_log2_matched_expr
* burden_score = sum(vaf * log2(matched_expr_count + 1))
Return: pathway, tissue, non_reference_calls, mean_vaf, mean_log2_matched_expr, burden_score
Sort by pathway ascending, then tissue ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Filter to complete-chain non-reference rows first.
2. Compute VAF per row.
3. Map matched_expr_count by gene_symbol and compute log2_matched_expr with numpy.log2(x + 1).
4. mean_vaf and mean_log2_matched_expr are means over filtered rows.
5. burden_score is the sum of per-row vaf * log2_matched_expr.

Self-check before final answer:
1. Are the columns exactly ["pathway", "tissue", "non_reference_calls", "mean_vaf", "mean_log2_matched_expr", "burden_score"]?
2. Did I follow the row-set rule: Filter to complete-chain non-reference rows first.
3. Did I follow the calculation/projection rule: Compute VAF per row.
4. Did I apply the final sort exactly: Sort by pathway ascending, then tissue ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Filter to complete-chain non-reference rows first. Compute VAF per row. Map matched_expr_count by gene_symbol and compute log2_matched_expr with numpy.log2(x + 1). mean_vaf and mean_log2_matched_expr are means over filtered rows. burden_score is the sum of per-row vaf * log2_matched_expr.
- **Gemma 4 31B:** Filter to complete-chain non-reference rows first. Compute VAF per row, map matched_expr_count by gene_symbol, and compute log2_matched_expr with numpy.log2(x + 1). mean_vaf and mean_log2_matched_expr are means over the filtered group; burden_score is the sum of per-row vaf * log2_matched_expr.

## pass5.query6 — PANDAS — Using pandas and sample_dim only, compute population z-scores for each expression marker:
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["sample_id", "z_ndhb", "z_pgr5", "z_ndhk", "photosynthesis_expr_z_mean"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: sample_id, z_ndhb, z_pgr5, z_ndhk, photosynthesis_expr_z_mean.
- Round decimal outputs to 3 decimals.

Task:
Using pandas and sample_dim only, compute population z-scores for each expression marker:

* z_ndhb from expr_ndhb
* z_pgr5 from expr_pgr5
* z_ndhk from expr_ndhk
Use population standard deviation with ddof=0.
Then compute:
* photosynthesis_expr_z_mean = mean(z_ndhb, z_pgr5, z_ndhk)
Return: sample_id, z_ndhb, z_pgr5, z_ndhk, photosynthesis_expr_z_mean
Sort by photosynthesis_expr_z_mean descending, then sample_id ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Use sample_dim only.
2. For each marker, compute population mean and population standard deviation with ddof=0 across all samples.
3. Then compute z-scores from raw marker values.
4. photosynthesis_expr_z_mean is the row-wise mean of the three z-scores.
5. Sort after all z-score columns are complete.

Self-check before final answer:
1. Are the columns exactly ["sample_id", "z_ndhb", "z_pgr5", "z_ndhk", "photosynthesis_expr_z_mean"]?
2. Did I follow the row-set rule: Use sample_dim only.
3. Did I follow the calculation/projection rule: For each marker, compute population mean and population standard deviation with ddof=0 across all samples.
4. Did I apply the final sort exactly: Sort by photosynthesis_expr_z_mean descending, then sample_id ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B / Gemma 4 31B:** Use sample_dim only. For each marker, compute population mean and population standard deviation with ddof=0 across all samples. Then compute z-scores from raw marker values. photosynthesis_expr_z_mean is the row-wise mean of the three z-scores. Sort after all z-score columns are complete.

## pass5.query7 — PANDAS — Using pandas and complete-chain matched rows only, create a condition-level integrative su
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition", "distinct_genes_observed", "mean_matched_expr", "cv_matched_expr", "mean_vaf"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition, distinct_genes_observed, mean_matched_expr, cv_matched_expr, mean_vaf.
- Round decimal outputs to 3 decimals.

Task:
Using pandas and complete-chain matched rows only, create a condition-level integrative summary.
For each condition, compute:

* distinct_genes_observed
* mean_matched_expr
* cv_matched_expr = population_std(matched_expr_count, ddof=0) / mean(matched_expr_count)
* mean_vaf
Return: condition, distinct_genes_observed, mean_matched_expr, cv_matched_expr, mean_vaf
Sort by condition ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Use complete-chain rows only.
2. Map matched expression by gene_symbol before grouping.
3. distinct_genes_observed counts unique gene_symbol values per condition.
4. cv_matched_expr uses population standard deviation with ddof=0 divided by mean_matched_expr from the same grouped series.
5. mean_vaf is mean of per-row VAF.

Self-check before final answer:
1. Are the columns exactly ["condition", "distinct_genes_observed", "mean_matched_expr", "cv_matched_expr", "mean_vaf"]?
2. Did I follow the row-set rule: Use complete-chain rows only.
3. Did I follow the calculation/projection rule: Map matched expression by gene_symbol before grouping.
4. Did I apply the final sort exactly: Sort by condition ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use complete-chain rows only. Map matched expression by gene_symbol before grouping. distinct_genes_observed counts unique gene_symbol values per condition. cv_matched_expr uses population standard deviation with ddof=0 divided by mean_matched_expr from the same grouped series. mean_vaf is mean of per-row VAF.
- **Gemma 4 31B:** Use complete-chain rows only. Map matched expression by gene_symbol before grouping. distinct_genes_observed counts unique gene_symbol values per condition. Compute cv_matched_expr using population standard deviation with ddof=0 divided by the grouped mean_matched_expr. Compute mean_vaf from per-row VAF values.

## pass5.query8 — PANDAS — Using pandas, compute a plant-photosynthesis burden table at sample level. Start from samp
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["sample_id", "tissue", "non_reference_complete_chain_calls", "high_or_moderate_nonref_calls", "total_marker_expr", "log2_total_marker_expr", "photosynthesis_variant_pressure"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: sample_id, tissue, non_reference_complete_chain_calls, high_or_moderate_nonref_calls, total_marker_expr, log2_total_marker_expr, photosynthesis_variant_pressure.
- Round decimal outputs to 3 decimals.

Task:
Using pandas, compute a plant-photosynthesis burden table at sample level.
Start from sample_dim and left join in complete-chain non-reference calls where genotype <> '0/0'.
For each sample, compute:

* non_reference_complete_chain_calls
* high_or_moderate_nonref_calls where impact IN ('high','moderate')
* total_marker_expr = expr_ndhb + expr_pgr5 + expr_ndhk
* log2_total_marker_expr = log2(total_marker_expr + 1)
* photosynthesis_variant_pressure = high_or_moderate_nonref_calls * log2_total_marker_expr
Return:
sample_id, tissue, non_reference_complete_chain_calls, high_or_moderate_nonref_calls, total_marker_expr, log2_total_marker_expr, photosynthesis_variant_pressure
Include samples with zero calls.
Sort by photosynthesis_variant_pressure descending, then sample_id ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Preserve every sample from sample_dim.
2. Left join only the complete-chain non-reference call subset.
3. Count high_or_moderate_nonref_calls only among non-reference complete-chain calls with impact high or moderate.
4. Compute total_marker_expr from sample_dim values, then log2_total_marker_expr, then photosynthesis_variant_pressure.
5. Include zero-call samples.

Self-check before final answer:
1. Are the columns exactly ["sample_id", "tissue", "non_reference_complete_chain_calls", "high_or_moderate_nonref_calls", "total_marker_expr", "log2_total_marker_expr", "photosynthesis_variant_pressure"]?
2. Did I follow the row-set rule: Preserve every sample from sample_dim.
3. Did I follow the calculation/projection rule: Left join only the complete-chain non-reference call subset.
4. Did I apply the final sort exactly: Sort by photosynthesis_variant_pressure descending, then sample_id ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Preserve every sample from sample_dim. Left join only the complete-chain non-reference call subset. Count high_or_moderate_nonref_calls only among non-reference complete-chain calls with impact high or moderate. Compute total_marker_expr from sample_dim values, then log2_total_marker_expr, then photosynthesis_variant_pressure. Include zero-call samples.
- **Gemma 4 31B:** Preserve every sample from sample_dim. Left join only the complete-chain non-reference call subset. Count high_or_moderate_nonref_calls only among non-reference complete-chain calls with impact high or moderate. Compute total_marker_expr from sample_dim values, then log2_total_marker_expr with numpy.log2(total_marker_expr + 1), then pressure.

## pass5.query9 — PANDAS — Using pandas and complete-chain non-reference rows only where genotype <> '0/0', build a c
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["condition", "gene_symbol", "non_reference_calls", "mean_vaf", "mean_log2_matched_expr", "expression_weighted_signal"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: condition, gene_symbol, non_reference_calls, mean_vaf, mean_log2_matched_expr, expression_weighted_signal.
- Round decimal outputs to 3 decimals.

Task:
Using pandas and complete-chain non-reference rows only where genotype <> '0/0', build a condition-by-gene decision summary.
Compute:

* non_reference_calls
* mean_vaf
* mean_log2_matched_expr
* expression_weighted_signal = mean_vaf * mean_log2_matched_expr
Return: condition, gene_symbol, non_reference_calls, mean_vaf, mean_log2_matched_expr, expression_weighted_signal
Sort by expression_weighted_signal descending, then gene_symbol ascending, then condition ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Use only complete-chain non-reference rows.
2. Group exactly by condition and gene_symbol.
3. Compute per-row VAF and per-row log2 matched expression first, then compute grouped means.
4. expression_weighted_signal is mean_vaf * mean_log2_matched_expr from the grouped means, not a sum of row products.
5. Sort last.

Self-check before final answer:
1. Are the columns exactly ["condition", "gene_symbol", "non_reference_calls", "mean_vaf", "mean_log2_matched_expr", "expression_weighted_signal"]?
2. Did I follow the row-set rule: Use only complete-chain non-reference rows.
3. Did I follow the calculation/projection rule: Group exactly by condition and gene_symbol.
4. Did I apply the final sort exactly: Sort by expression_weighted_signal descending, then gene_symbol ascending, then condition ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN fact_calls CSV ---
[full fact_calls CSV here]
--- END fact_calls CSV ---

--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---

--- BEGIN variant_dim CSV ---
[full variant_dim CSV here]
--- END variant_dim CSV ---

--- BEGIN gene_dim CSV ---
[full gene_dim CSV here]
--- END gene_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use only complete-chain non-reference rows. Group exactly by condition and gene_symbol. Compute per-row VAF and per-row log2 matched expression first, then compute grouped means. expression_weighted_signal is mean_vaf * mean_log2_matched_expr from the grouped means, not a sum of row products. Sort last.
- **Gemma 4 31B:** Use only complete-chain non-reference rows. Group exactly by condition and gene_symbol; do not leak reference, incomplete-chain, orphan, or unmatched groups. Compute per-row VAF and log2 matched expression first, then group means. Compute expression_weighted_signal from the grouped means and sort last.

## pass5.query10 — PANDAS — Using pandas and sample_dim only, compute marker composition shares and imbalance. For eac
```text
/no_think

You are completing an automated pandas/numpy-style data analysis benchmark.
Use the CSV tables below as the only source of truth. Do not invent rows, columns, labels, categories, or values.

Output requirements:
- Return only valid JSON.
- Do not include SQL code, Python code, markdown, commentary, diagnostics, or reasoning.
- JSON must have exactly this shape:
  {"columns":["sample_id", "condition", "ndhb_share", "pgr5_share", "ndhk_share", "marker_imbalance"],"rows":[[...],[...]]}
- Use JSON null for missing values.
- Preserve this exact column order: sample_id, condition, ndhb_share, pgr5_share, ndhk_share, marker_imbalance.
- Round decimal outputs to 3 decimals.

Task:
Using pandas and sample_dim only, compute marker composition shares and imbalance.
For each sample, compute:

* ndhb_share = expr_ndhb / (expr_ndhb + expr_pgr5 + expr_ndhk)
* pgr5_share = expr_pgr5 / (expr_ndhb + expr_pgr5 + expr_ndhk)
* ndhk_share = expr_ndhk / (expr_ndhb + expr_pgr5 + expr_ndhk)
* marker_imbalance = max(share) - min(share)
Return: sample_id, condition, ndhb_share, pgr5_share, ndhk_share, marker_imbalance
Sort by marker_imbalance descending, then sample_id ascending.
Round decimal outputs to 3 decimals.

Execution rules:
1. Use sample_dim only.
2. Compute the denominator once from raw marker expressions for each sample.
3. Compute all three shares from the same denominator.
4. marker_imbalance is max(three shares) minus min(three shares).
5. Do not use log-transformed expression for shares.
6. Re-apply marker_imbalance DESC, sample_id ASC after rounding.

Self-check before final answer:
1. Are the columns exactly ["sample_id", "condition", "ndhb_share", "pgr5_share", "ndhk_share", "marker_imbalance"]?
2. Did I follow the row-set rule: Use sample_dim only.
3. Did I follow the calculation/projection rule: Compute the denominator once from raw marker expressions for each sample.
4. Did I apply the final sort exactly: Sort by marker_imbalance descending, then sample_id ascending.
5. Did I round only at final output: Round decimal outputs to 3 decimals.
6. Is the final response JSON only, with JSON null for missing values?

CSV tables:
--- BEGIN sample_dim CSV ---
[full sample_dim CSV here]
--- END sample_dim CSV ---
```

**Target-model addendum — include only the line for the model being run:**

- **Qwen3.6 27B / Qwen3.6 / Qwen3 Coder 30B / Phi-4 Mini / Gemma 4 26B:** Use sample_dim only. Compute the denominator once from raw marker expressions for each sample. Compute all three shares from the same denominator. marker_imbalance is max(three shares) minus min(three shares). Do not use log-transformed expression for shares. Re-apply marker_imbalance DESC, sample_id ASC after rounding.
- **Gemma 4 31B:** Use sample_dim only. Compute the denominator once from raw marker expressions for each sample. Compute all three shares from the same denominator. marker_imbalance is max(three shares) minus min(three shares). Re-apply marker_imbalance DESC, sample_id ASC after rounding checks.
