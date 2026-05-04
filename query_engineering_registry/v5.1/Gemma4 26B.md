# Gemma 4 26B — exact improved query prompts for AIBioBench v5

## Gemma 4 26B universal rules for all 5 passes

Before producing the final table/output:



1\. Treat the task as a strict table-construction problem: return exactly the requested rows, columns, values, and column order.

2\. Establish the eligible row set before calculating any metric or derived value.

3\. Keep valid observations unless the query explicitly asks for DISTINCT values, deduplication, or one row per entity.

4\. Exclude orphan or incomplete-chain rows when the task requires an INNER, complete-chain, or matched-only result.

5\. When a table is explicitly preserved, keep that table’s rows as the output frame and use NULL for unmatched fields.

6\. Aggregate at the requested grain; do not mix call-level, sample-level, variant-level, gene-level, or group-level denominators.

7\. Use full precision until the final output; round only final decimal values to 3 places where requested.

8\. Apply the requested final sort after all joins, filters, aggregations, derived columns, rounding, and projection.

9\. Return only the requested final table/output; do not include intermediate tables, helper columns, debug frames, or reasoning output.

## Gemma 4 26B SQL-specific rules for Passes 1–3

10\. Identify the requested join path before writing the query:

&#x20;   - `fact\\\_calls -> sample\\\_dim`

&#x20;   - `fact\\\_calls -> variant\\\_dim`

&#x20;   - `fact\\\_calls -> variant\\\_dim -> gene\\\_dim`

&#x20;   - full snowflake path where required



11\. Use the requested SQL join logic exactly:

&#x20;   - INNER and complete-chain tasks are strict eligibility filters

&#x20;   - LEFT, RIGHT, FULL OUTER, and dimension-preserving tasks preserve the requested side



12\. For call-count tasks, count joined `fact\\\_calls` rows unless the query explicitly requests distinct samples, variants, genes, or groups.



13\. When grouping by `impact`, preserve every impact class present after the join, including `low`, `modifier`, `moderate`, and `high`.



14\. For condition-impact, tissue, pathway, gene, and sample summaries, calculate all grouped metrics from one consistent grouped row set.



15\. For conditional SQL metrics such as high-impact calls or non-reference calls, build the required joined row set first, then apply the condition inside the metric.



16\. For SQL VAF summaries, calculate row-level `alt\\\_reads / total\\\_reads` first, then average those row-level VAF values when a mean is requested.



17\. Avoid sample-level counting or distinct counting when the query asks for joined fact-call grain.



18\. Use the final `ORDER BY` exactly as requested after all projection and derived SQL values are complete.



## Gemma 4 26B Python-specific rules for Passes 4–5



Before producing the Python/pandas final table:

10\. Choose the correct pandas base frame before calculating metrics:

&#x20;  - sample-only frame for expression-only sample tasks

&#x20;  - preserving sample frame for sample-level burden tasks

&#x20;  - preserving gene frame for gene-level summaries

&#x20;  - complete-chain frame for matched fact/sample/variant/gene tasks

&#x20;  - complete-chain non-reference frame for genotype-filtered tasks

&#x20;  - separate orphan slices for orphan-report tasks

11\. Build the DataFrame first, derive row-level helper columns second, aggregate third, and project/sort last.

12\. Keep valid non-reference rows, high/moderate rows, and repeated valid calls unless the query explicitly removes them.

13\. Compute non\_reference\_calls only from genotype-filtered rows where genotype is not 0/0.

14\. Use the exact matched-expression mapping:

&#x20;  - NDHB -> expr\_ndhb

&#x20;  - NDHK -> expr\_ndhk

&#x20;  - PGR5 -> expr\_pgr5

&#x20;  - all other genes -> NULL

15\. Reuse the same mapped matched-expression series consistently for mean\_matched\_expr, mean\_log2\_matched\_expr, CV, burden, and signal calculations.

16\. Compute VAF row-wise as alt\_reads / total\_reads before calculating mean\_vaf.

17\. Use numpy.log2(x + 1) for every requested log2 expression transform.

18\. Use population standard deviation with ddof=0 for population standard deviation, CV, and z-score tasks.

19\. Do not mix metrics from different grouped frames when calculating mean\_vaf, mean\_matched\_expr, CV, burden scores, or expression-weighted signals.

20\. Keep row-level products and grouped products separate: use sum of row-level products only when requested, and product of grouped means only when requested.

21\. Hide helper columns from the final output unless the query explicitly requests them.

\---

## pass1.query1

Inner join fact\_calls to sample\_dim on sample\_id.
Return: call\_id, sample\_id, tissue, condition, genotype
Sort by call\_id ascending.



Gemma 4 26B addendum:

Use a true inner join to sample\_dim. Keep every fact row whose sample\_id exists in sample\_dim, including duplicate or repeated valid sample calls. Do not drop valid joined calls. Project only requested columns and sort by call\_id ASC after projection.

\---

## pass1.query2

Inner join fact\_calls to variant\_dim on variant\_id.
Return: call\_id, variant\_id, variant\_class, impact, qual
Sort by qual descending, then call\_id ascending.

Gemma 4 26B addendum:
Use a true inner join to variant\_dim and exclude fact rows without a matching variant. Do not keep missing-variant fact rows. Preserve every valid joined variant call. After projection, explicitly sort by qual DESC, then call\_id ASC.

\---

## pass1.query3

Left join fact\_calls to sample\_dim on sample\_id.
Return: call\_id, sample\_id, tissue, batch, expr\_ndhb
Keep all fact rows.
Sort by call\_id ascending.

Gemma 4 26B addendum:
fact\_calls is the preserving table. Keep every fact row exactly once. For unmatched samples, keep the fact row and use NULL for missing sample\_dim fields. Do not fill sample-derived cells from another row. Sort only after the final projection.

\---

## pass1.query4

Use a RIGHT JOIN from fact\_calls to sample\_dim, or an equivalent reversed LEFT JOIN.
Return one row per sample with:
sample\_id, tissue, call\_count, avg\_qual
Include samples with zero calls.
Sort by sample\_id ascending.
Round avg\_qual to 3 decimals.

Gemma 4 26B addendum:
Use sample\_dim as the preserving table. Return one row per sample. call\_count counts matched fact rows, not distinct variants or distinct samples. avg\_qual is computed only from matched fact rows for that sample. Keep zero-call samples and round avg\_qual only at output.

\---

## pass1.query5

Inner join fact\_calls to variant\_dim, then to gene\_dim.
Return: call\_id, variant\_id, gene\_symbol, pathway
Sort by call\_id ascending.

Gemma 4 26B addendum:
Use two sequential inner joins. A fact row must match variant\_dim and then gene\_dim to survive. Drop incomplete variant-to-gene chains. Do not keep rows after the first join if the second join fails. Sort by call\_id ASC after projection.

\---

## pass1.query6

Inner join fact\_calls to variant\_dim.
Count calls by impact and also compute average qual.
Return: impact, call\_count, avg\_qual
Sort by call\_count descending, then impact ascending.
Round avg\_qual to 3 decimals.

Gemma 4 26B addendum:
Aggregate at fact-call grain after the inner join. Keep all impact categories present in the joined data, including low and modifier. call\_count counts every joined call row. avg\_qual must be computed from the same rows used for call\_count. Sort after final rounding.

\---

## pass1.query7

Inner join fact\_calls to sample\_dim.
Compute average, minimum, and maximum qual by tissue.
Return: tissue, avg\_qual, min\_qual, max\_qual
Sort by avg\_qual descending.
Round avg\_qual to 3 decimals.

Gemma 4 26B addendum:
Aggregate by tissue over joined fact-call rows, not distinct samples. avg\_qual, min\_qual, and max\_qual must all come from the same tissue-specific joined row set. Do not compute sample-level averages first. Round avg\_qual only at final output.

\---

## pass1.query8

Inner join fact\_calls to sample\_dim.
For each condition, compute:

call\_count

avg\_expr\_pgr5
Return: condition, call\_count, avg\_expr\_pgr5
Sort by condition ascending.
Round avg\_expr\_pgr5 to 3 decimals.

Gemma 4 26B addendum:
Compute at joined fact-call grain. If one sample contributes multiple fact rows, its expr\_pgr5 contributes once per joined fact row. Do not count samples instead of calls. Do not leak unmatched sample rows into condition groups. Sort by condition ASC after rounding.

\---

## pass1.query9

Decision screen for sample quality.
Inner join fact\_calls to sample\_dim and variant\_dim.
For each condition, compute:

total\_calls

avg\_qual

high\_impact\_calls where impact = 'high'
Return: condition, total\_calls, avg\_qual, high\_impact\_calls
Sort by condition ascending.
Round avg\_qual to 3 decimals.

Gemma 4 26B addendum:
First build the joined fact/sample/variant row set. total\_calls and avg\_qual use all joined rows per condition. high\_impact\_calls counts only rows from that joined frame where impact = 'high'. Do not compute high-impact counts before the variant join. Sort by condition ASC.

\---

## pass1.query10

Simple anomaly audit.
Left join fact\_calls to variant\_dim on variant\_id.
Return: call\_id, variant\_id, impact, variant\_match\_status
Set variant\_match\_status to MATCHED when variant\_dim matched, else MISSING\_VARIANT.
Keep all fact rows.
Sort by call\_id ascending.

Gemma 4 26B addendum:
Preserve every fact row. Set MATCHED only when the variant\_dim join succeeds; otherwise set MISSING\_VARIANT and leave variant\_dim-derived fields NULL. Do not label matched variants as missing. Sort by call\_id ASC after classification.

\---

## pass2.query1

Inner join across all four tables:
fact\_calls -> sample\_dim
fact\_calls -> variant\_dim -> gene\_dim
Return: call\_id, sample\_id, tissue, gene\_symbol, impact, genotype
Sort by call\_id ascending.

Gemma 4 26B addendum:
Use complete-chain inner joins only. A row must match sample\_dim, variant\_dim, and gene\_dim to survive. Preserve all valid complete-chain calls; do not drop valid rows after the full join. Do not keep partial-chain rows. Sort by call\_id ASC.

\---

## pass2.query2

Left join fact\_calls across the full snowflake.
Return: call\_id, sample\_id, plant\_line\_id, tissue, variant\_id, gene\_symbol
Keep all fact rows.
Sort by call\_id ascending.

Gemma 4 26B addendum:
fact\_calls is the preserving table. Keep all fact rows exactly once across both snowflake branches. Use NULL for missing sample, variant, or gene fields. Do not silently convert this into an inner join. Sort by call\_id ASC after projection.

\---

## pass2.query3

Perform a FULL OUTER JOIN between fact\_calls and variant\_dim on variant\_id.
Return:

variant\_id as the coalesced key

call\_id

sample\_id

impact
Sort by variant\_id ascending, then call\_id ascending.

Gemma 4 26B addendum:
Use a true full outer join or a correct union-based emulation. Keep fact-only and variant-only rows. Coalesce variant\_id once and use that coalesced key for output and sorting. Do not duplicate matched rows. Sort by variant\_id ASC, then call\_id ASC.

\---

## pass2.query4

Inner join fact\_calls to sample\_dim and variant\_dim.
Count calls by condition and impact, and compute average qual.
Return: condition, impact, call\_count, avg\_qual
Sort by condition ascending, then impact ascending.
Round avg\_qual to 3 decimals.

Gemma 4 26B addendum:
Aggregate over the joined fact/sample/variant rows. Group exactly by condition and impact. Preserve all impact categories present after the join, including low and modifier. call\_count and avg\_qual must come from the same grouped rows. Sort after final rounding.

\---

## pass2.query5

Inner join fact\_calls to variant\_dim and gene\_dim.
Compute VAF = alt\_reads / total\_reads.
Return average VAF and maximum qual by gene\_symbol.
Columns: gene\_symbol, avg\_vaf, max\_qual
Sort by avg\_vaf descending, then gene\_symbol ascending.
Round avg\_vaf to 3 decimals.

Gemma 4 26B addendum:
Compute VAF per joined call row first as alt\_reads / total\_reads. Then average those per-row VAF values by gene\_symbol. Do not calculate VAF from summed reads unless explicitly requested. max\_qual must come from the same joined gene-specific rows. Sort after aggregation.

\---

## pass2.query6

Use complete inner joins across all four tables.
For each tissue, compute:

distinct\_genes

avg\_expr\_ndhb
Return: tissue, distinct\_genes, avg\_expr\_ndhb
Sort by tissue ascending.
Round avg\_expr\_ndhb to 3 decimals.

Gemma 4 26B addendum:
Use only complete-chain rows. distinct\_genes counts unique gene\_symbol values per tissue after the complete join. avg\_expr\_ndhb is averaged over the complete-chain joined call rows, not distinct samples. Round only at final output and sort by tissue ASC.

\---

## pass2.query7

Use sample\_dim as the preserving table.
For each sample, count high-impact calls and compute average alt\_reads among only high-impact calls.
Return: sample\_id, tissue, high\_impact\_call\_count, avg\_alt\_reads\_high
Include samples with zero high-impact calls.
Sort by high\_impact\_call\_count descending, then sample\_id ascending.
Round avg\_alt\_reads\_high to 3 decimals.

Gemma 4 26B addendum:
Preserve all samples from sample\_dim. Count only joined calls whose impact is high. Include high-impact rows even when alt\_reads is zero. avg\_alt\_reads\_high averages alt\_reads only across high-impact rows. Keep zero-count samples with NULL average. Sort after final aggregation.

\---

## pass2.query8

Inner join fact\_calls to variant\_dim and gene\_dim.
For each gene\_symbol, compute:

total\_alt\_reads

avg\_qual

max\_alt\_reads
Return: gene\_symbol, total\_alt\_reads, avg\_qual, max\_alt\_reads
Sort by total\_alt\_reads descending, then gene\_symbol ascending.
Round avg\_qual to 3 decimals.

Gemma 4 26B addendum:
Use the joined fact/variant/gene rows only. total\_alt\_reads is the sum over all joined call rows per gene, not distinct variants. avg\_qual and max\_alt\_reads must be computed from the same grouped rows. Re-apply total\_alt\_reads DESC, gene\_symbol ASC after rounding.

\---

## pass2.query9

Decision-oriented pathway summary.
Use complete inner joins across all four tables.
For each condition and pathway, compute:

call\_count

mean\_vaf where VAF = alt\_reads / total\_reads

distinct\_samples
Return: condition, pathway, call\_count, mean\_vaf, distinct\_samples
Sort by condition ascending, then pathway ascending.
Round mean\_vaf to 3 decimals.

Gemma 4 26B addendum:
Use only complete-chain rows. Group exactly by condition and pathway from that complete frame. call\_count counts fact-call rows. Compute VAF per row, then average VAF values inside each group. distinct\_samples counts unique matched samples in the same group. Do not add absent condition-pathway groups.

\---

## pass2.query10

Coverage screen with sample\_dim as the preserving table.
Left join sample\_dim to fact\_calls, then to variant\_dim and gene\_dim.
For each sample, compute:

total\_fact\_calls

complete\_chain\_calls

incomplete\_chain\_calls
Return: sample\_id, tissue, total\_fact\_calls, complete\_chain\_calls, incomplete\_chain\_calls
Sort by sample\_id ascending.

Gemma 4 26B addendum:
Preserve every sample from sample\_dim. total\_fact\_calls counts all joined fact rows for that sample. complete\_chain\_calls counts rows with both variant and gene matched. incomplete\_chain\_calls is the remaining fact-call count. Ensure complete + incomplete equals total for each sample.

\---

## pass3.query1

Left join fact\_calls across the full snowflake and classify each fact row into one join\_status using this logic:

COMPLETE\_CHAIN: sample, variant, and gene all matched

MISSING\_SAMPLE: sample missing but variant and gene matched

MISSING\_GENE: variant matched but gene missing

MISSING\_VARIANT: variant missing
Return: call\_id, sample\_id, variant\_id, join\_status
Sort by call\_id ascending.

Gemma 4 26B addendum:
Preserve every fact row exactly once. Assign one and only one join\_status per row using the stated logic. MISSING\_VARIANT takes precedence over gene status when the variant branch is absent. Do not double-count or emit multiple statuses per fact row. Sort by call\_id ASC.

\---

## pass3.query2

Using only complete-chain matched rows, group by tissue and gene\_symbol.
Compute:

call\_count

sum\_alt\_reads

avg\_vaf where VAF = alt\_reads / total\_reads

max\_qual
Return: tissue, gene\_symbol, call\_count, sum\_alt\_reads, avg\_vaf, max\_qual
Sort by tissue ascending, then gene\_symbol ascending.
Round avg\_vaf to 3 decimals.

Gemma 4 26B addendum:
Filter to complete-chain rows before grouping. Group exactly by tissue and gene\_symbol from the filtered frame. Compute VAF per call row, then average those values. call\_count, sum\_alt\_reads, avg\_vaf, and max\_qual must all use the same grouped row set.

\---

## pass3.query3

Start from gene\_dim and left join to variant\_dim, then fact\_calls.
Return one row per gene with:
gene\_symbol, pathway, observed\_call\_count, total\_alt\_reads
Count matched fact rows per gene.
Include genes with zero observed calls.
Sort by observed\_call\_count descending, then gene\_symbol ascending.
Round total\_alt\_reads to 3 decimals if needed.

Gemma 4 26B addendum:
Use gene\_dim as the preserving table. Return one row per gene, including genes with zero observed calls. observed\_call\_count counts matched fact rows only after joining through variants. total\_alt\_reads sums only those matched fact rows. Do not count variants as calls.

\---

## pass3.query4

Inner join fact\_calls to sample\_dim and variant\_dim.
Filter to impact = 'high'.
For each condition, compute:

high\_impact\_call\_count

avg\_qual

avg\_alt\_reads
Return: condition, high\_impact\_call\_count, avg\_qual, avg\_alt\_reads
Sort by condition ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Apply the inner joins first, then filter to impact = 'high'. Group by condition over the filtered joined rows. high\_impact\_call\_count, avg\_qual, and avg\_alt\_reads must all use the same high-impact row set. Do not undercount repeated valid high-impact rows.

\---

## pass3.query5

Using sample\_dim as the preserving table, count genotype classes per sample.
Compute:

heterozygous\_calls where genotype = '0/1'

homozygous\_alt\_calls where genotype = '1/1'

mean\_nonref\_qual over only non-reference calls where genotype in ('0/1','1/1')
Return: sample\_id, heterozygous\_calls, homozygous\_alt\_calls, mean\_nonref\_qual
Include samples with zero calls.
Sort by sample\_id ascending.
Round mean\_nonref\_qual to 3 decimals.

Gemma 4 26B addendum:
Preserve every sample from sample\_dim. Count genotype classes from joined fact rows only. mean\_nonref\_qual uses only rows with genotype 0/1 or 1/1. Do not include 0/0 rows in the mean. Keep zero-call samples with zero counts and NULL mean. Sort by sample\_id ASC.

\---

## pass3.query6

Using only complete-chain matched rows, compute total\_alt\_reads and avg\_vaf by tissue and gene\_symbol.
Within each tissue, rank genes by total\_alt\_reads descending using dense rank.
Return: tissue, gene\_symbol, total\_alt\_reads, avg\_vaf, rank\_in\_tissue
Sort by tissue ascending, then rank\_in\_tissue ascending, then gene\_symbol ascending.
Round avg\_vaf to 3 decimals.

Gemma 4 26B addendum:
Use complete-chain rows only. Aggregate by tissue and gene\_symbol before ranking. Compute VAF per row, then average VAF. Dense rank must reset within each tissue and use total\_alt\_reads DESC. Re-apply tissue ASC, rank ASC, gene\_symbol ASC after ranking.

\---

## pass3.query7

Find unused dimension rows across both branches using anti-join logic.
Return: object\_type, object\_id, reason
Use these rules:

sample\_dim rows with no fact\_calls => no\_fact\_calls

variant\_dim rows with no fact\_calls => no\_fact\_calls

gene\_dim rows with variants but no fact\_calls through those variants => no\_fact\_calls\_through\_variants

gene\_dim rows with no variants at all => no\_variants\_attached
Sort by object\_type ascending, then object\_id ascending.

Gemma 4 26B addendum:
Run each anti-join rule separately, then union the outputs. Use the exact object\_type and reason labels from the prompt. Keep gene cases with no variants separate from gene cases with variants but no fact calls. Sort only after the union.

\---

## pass3.query8

Using complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0'.
Group by condition and gene\_role.
Return: condition, gene\_role, non\_reference\_call\_count, mean\_vaf
Sort by condition ascending, then gene\_role ascending.
Round mean\_vaf to 3 decimals.

Gemma 4 26B addendum:
Filter to complete-chain rows first, then genotype <> '0/0'. Group only by condition and gene\_role from the filtered frame. non\_reference\_call\_count counts filtered call rows. Compute VAF per row, then average those values. Do not leak reference or incomplete-chain rows.

\---

## pass3.query9

Failure-family audit for operational review.
Left join fact\_calls across the full snowflake.
Create condition\_group = condition when sample matched, else 'UNMATCHED\_SAMPLE'.
For each condition\_group, compute:

complete\_chain\_calls

missing\_sample\_calls

missing\_variant\_calls

missing\_gene\_calls
Return: condition\_group, complete\_chain\_calls, missing\_sample\_calls, missing\_variant\_calls, missing\_gene\_calls
Sort by condition\_group ascending.

Gemma 4 26B addendum:
Preserve all fact rows after the full snowflake left join. First classify each fact row into one status category, then aggregate by condition\_group. condition\_group is the matched condition when sample exists; otherwise use UNMATCHED\_SAMPLE. Do not double-count one row across multiple missing categories.

\---

## pass3.query10

Decision-priority candidate table.
Using complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0'.
Map matched expression counts using:

NDHB -> expr\_ndhb

NDHK -> expr\_ndhk

PGR5 -> expr\_pgr5
For each gene\_symbol, compute:

non\_reference\_calls

avg\_vaf

avg\_matched\_expr

decision\_score = avg\_vaf \* avg\_matched\_expr
Return: gene\_symbol, non\_reference\_calls, avg\_vaf, avg\_matched\_expr, decision\_score
Sort by decision\_score descending, then gene\_symbol ascending.
Round decimals to 3 places.

Gemma 4 26B addendum:
Use only complete-chain non-reference rows. Apply the matched-expression mapping by gene\_symbol before grouping. non\_reference\_calls counts filtered call rows. Compute VAF per row, average VAF and matched expression by gene, then compute decision\_score from the final grouped averages. Sort last.

\---

## pass4.query1

Using pandas, create a reconciliation summary with exactly these metrics:

fact\_rows\_total

complete\_chain\_rows

fact\_rows\_missing\_sample

fact\_rows\_missing\_variant

fact\_rows\_missing\_gene

unused\_samples

unused\_variants

genes\_with\_no\_variants
Return: metric, value
Preserve this exact row order.

Gemma 4 26B addendum:
Compute each reconciliation metric from its correct source grain. fact-row metrics start from fact\_calls. unused sample, variant, and gene metrics start from the relevant dimension table. Do not reuse a single filtered frame for all metrics. Preserve the metric row order exactly.

\---

## pass4.query2

Using pandas and complete-chain matched rows only, group by condition and pathway.
Compute:

call\_count

total\_alt\_reads

mean\_qual

avg\_expr\_ndhb
Return: condition, pathway, call\_count, total\_alt\_reads, mean\_qual, avg\_expr\_ndhb
Sort by condition ascending, then total\_alt\_reads descending, then pathway ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Build the complete-chain pandas frame first and only then group by condition and pathway. call\_count, total\_alt\_reads, mean\_qual, and avg\_expr\_ndhb must all use that same complete-chain row set. Do not add absent condition-pathway groups. Sort after aggregation.

\---

## pass4.query3

Using pandas and complete-chain non-reference rows only where genotype <> '0/0', group by batch and gene\_role.
Compute:

non\_reference\_calls

avg\_qual

max\_vaf

mean\_expr\_pgr5
Return: batch, gene\_role, non\_reference\_calls, avg\_qual, max\_vaf, mean\_expr\_pgr5
Sort by batch ascending, then gene\_role ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Filter in this order: complete-chain rows first, then genotype <> '0/0'. Group only by batch and gene\_role from the filtered rows. Compute VAF per row before max\_vaf. non\_reference\_calls, avg\_qual, max\_vaf, and mean\_expr\_pgr5 must use the same filtered frame.

\---

## pass4.query4

Using pandas and complete-chain matched rows only, find genes observed in both:

control

at least one non-control condition
Return:

gene\_symbol

control\_calls

non\_control\_calls

total\_alt\_reads
Sort by total\_alt\_reads descending, then gene\_symbol ascending.

Gemma 4 26B addendum:
Use complete-chain rows only. Identify shared genes by requiring at least one control call and at least one non-control call for the same gene. Exclude genes present in only one side. Compute control\_calls, non\_control\_calls, and total\_alt\_reads after the shared-gene set is fixed.

\---

## pass4.query5

Using pandas, start from gene\_dim and left join to variant\_dim, then fact\_calls, then sample\_dim.
Return one row per gene with:

gene\_symbol

variant\_count

call\_count

distinct\_matched\_sample\_count

distinct\_tissue\_count

avg\_matched\_expression
For distinct\_matched\_sample\_count, count only sample\_dim matches and exclude orphan fact sample keys.
For avg\_matched\_expression, use the matched expression mapping from the instructions and average across matched sample-call rows only.
Sort by gene\_symbol ascending.
Round avg\_matched\_expression to 3 decimals.

Gemma 4 26B addendum:
Use gene\_dim as the preserving frame. variant\_count counts distinct variants attached to each gene. call\_count counts matched fact rows after joining through variants. distinct\_matched\_sample\_count and distinct\_tissue\_count count only successful sample\_dim matches. avg\_matched\_expression averages mapped expression only across matched sample-call rows.

\---

## pass4.query6

Using pandas, compute sample-level burden.
Use complete-chain matched rows only, filter to non-reference calls where genotype <> '0/0' and impact IN ('high', 'moderate').
For each sample in sample\_dim, compute:

burden\_genes = count of distinct genes meeting that rule

mean\_log2\_marker\_expr = mean(log2(expr\_ndhb+1), log2(expr\_pgr5+1), log2(expr\_ndhk+1))
Return: sample\_id, tissue, burden\_genes, mean\_log2\_marker\_expr
Include samples with zero burden.
Sort by burden\_genes descending, then sample\_id ascending.
Round mean\_log2\_marker\_expr to 3 decimals.

Gemma 4 26B addendum:
Preserve every sample from sample\_dim. Compute burden\_genes from complete-chain, non-reference, high/moderate calls only. Compute mean\_log2\_marker\_expr from each sample's own three expression markers, independent of burden. Include zero-burden samples and sort after final calculations.

\---

## pass4.query7

Using pandas, build a single orphan-key report using concat/union-style logic.
Return: source\_table, key\_value, orphan\_type
Include:

fact\_calls.sample\_id values missing in sample\_dim

fact\_calls.variant\_id values missing in variant\_dim

variant\_dim.gene\_id values missing in gene\_dim

sample\_dim.sample\_id rows unused by fact\_calls

variant\_dim.variant\_id rows unused by fact\_calls

gene\_dim.gene\_id rows with no variants attached
Sort by source\_table ascending, then key\_value ascending.

Gemma 4 26B addendum:
Create each orphan category separately, then concatenate with exact labels. Keep source\_table and orphan\_type tied to the specific rule that produced the row. Do not collapse distinct orphan sources into generic labels. Remove only true duplicates within the same category, then sort.

\---

## pass4.query8

Using pandas, produce a final presentation table for all non-reference complete-chain calls only.
Filter to genotype <> '0/0'.
Return these columns in this exact order:
call\_id, plant\_line\_id, tissue, condition, gene\_symbol, pathway, variant\_id, impact, genotype, alt\_reads, total\_reads, vaf, matched\_expr\_count, log2\_matched\_expr, qual
Use the matched expression mapping from the instructions.
Sort by:
condition ascending,
tissue ascending,
gene\_symbol ascending,
variant\_id ascending,
call\_id ascending.
Round vaf and log2\_matched\_expr to 3 decimals.

Gemma 4 26B addendum:
Use complete-chain rows only, then filter to genotype <> '0/0'. Preserve the exact requested column order. Compute VAF per row and map matched\_expr\_count by gene\_symbol. Use numpy.log2(matched\_expr\_count + 1). Re-apply the full five-key sort after derived columns and rounding.

\---

## pass4.query9

Using pandas and complete-chain matched rows only, build a pathway reliability summary.
For each pathway, compute:

call\_count

non\_reference\_rate where genotype <> '0/0'

mean\_vaf

mean\_matched\_expr
Return: pathway, call\_count, non\_reference\_rate, mean\_vaf, mean\_matched\_expr
Sort by non\_reference\_rate descending, then pathway ascending.
Round decimals to 3 places.

Gemma 4 26B addendum:
Use complete-chain rows only. call\_count is all complete-chain calls per pathway. non\_reference\_rate is non-reference complete-chain calls divided by all complete-chain calls in that pathway. Compute VAF per row. mean\_vaf and mean\_matched\_expr must use the correct complete-chain row set with matched expression mapped by gene\_symbol.

\---

## pass4.query10

Using pandas, create a repairability audit over all fact rows.
Left join fact\_calls across the full snowflake and classify join\_status using:

COMPLETE\_CHAIN

MISSING\_SAMPLE

MISSING\_GENE

MISSING\_VARIANT
Set repairable\_by\_human = True only for MISSING\_SAMPLE and MISSING\_GENE.
Return: call\_id, sample\_id, variant\_id, join\_status, repairable\_by\_human
Sort by call\_id ascending.

Gemma 4 26B addendum:
Preserve all fact rows and classify exactly one join\_status per row. Set repairable\_by\_human to True only for MISSING\_SAMPLE and MISSING\_GENE, never for COMPLETE\_CHAIN or MISSING\_VARIANT. Do not overwrite classification after later joins. Sort by call\_id ASC.

\---

## pass5.query1

Using pandas and sample\_dim only, compute these expression features for every sample:

log2\_expr\_ndhb = log2(expr\_ndhb + 1)

log2\_expr\_pgr5 = log2(expr\_pgr5 + 1)

log2\_expr\_ndhk = log2(expr\_ndhk + 1)

ndh\_module\_ratio = (expr\_ndhb + expr\_ndhk) / (expr\_ndhb + expr\_pgr5 + expr\_ndhk)
Return: sample\_id, tissue, log2\_expr\_ndhb, log2\_expr\_pgr5, log2\_expr\_ndhk, ndh\_module\_ratio
Sort by sample\_id ascending.
Round all derived decimals to 3 decimals.

Gemma 4 26B addendum:
Use sample\_dim only; do not join to fact\_calls. Compute each log2 feature with numpy.log2(x + 1). Compute ndh\_module\_ratio from raw expression values, not log-transformed values. Use the same raw denominator for the ratio. Round only after all derived columns are complete.

\---

## pass5.query2

Using pandas and complete-chain matched rows only, map matched expression by gene\_symbol using the standard mapping.
Compute:

matched\_expr\_count

log2\_matched\_expr = log2(matched\_expr\_count + 1)

vaf = alt\_reads / total\_reads

expr\_weighted\_vaf = vaf \* log2\_matched\_expr
Return: call\_id, gene\_symbol, matched\_expr\_count, log2\_matched\_expr, vaf, expr\_weighted\_vaf
Sort by call\_id ascending.
Round derived decimals to 3 decimals.

Gemma 4 26B addendum:
Build the complete-chain matched frame first. Exclude incomplete-chain, orphan, and unmatched rows. Map matched\_expr\_count by gene\_symbol before deriving log2\_matched\_expr. Compute VAF per row, then expr\_weighted\_vaf per row. Do not average before row-level calculations. Sort by call\_id ASC.

\---

## pass5.query3

Using pandas and complete-chain matched rows only, group by condition and gene\_symbol.
Compute:

n\_calls

mean\_matched\_expr

median\_matched\_expr

pop\_std\_matched\_expr using ddof=0
Return: condition, gene\_symbol, n\_calls, mean\_matched\_expr, median\_matched\_expr, pop\_std\_matched\_expr
Sort by condition ascending, then gene\_symbol ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Use complete-chain rows only and map matched expression by gene\_symbol before grouping. n\_calls counts rows in each condition/gene group. mean, median, and population standard deviation must use the same matched-expression series. Use ddof=0. Sort by condition ASC, gene\_symbol ASC after rounding.

\---

## pass5.query4

Using pandas and sample\_dim only, define:

stress\_group = 'stress' for conditions high\_light or drought

stress\_group = 'control' for condition control
For each gene marker (NDHB, NDHK, PGR5), compute:

stress\_mean\_log2

control\_mean\_log2

delta\_log2\_stress\_minus\_control
Use:

NDHB from expr\_ndhb

NDHK from expr\_ndhk

PGR5 from expr\_pgr5
Apply log2(x + 1) before averaging.
Return: gene\_symbol, stress\_mean\_log2, control\_mean\_log2, delta\_log2\_stress\_minus\_control
Sort by gene\_symbol ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Use sample\_dim only. Apply numpy.log2(x + 1) to each sample's marker expression before computing group means. Compute delta as stress\_mean\_log2 minus control\_mean\_log2. Do not average raw expression before log transformation. Sort by gene\_symbol ASC.

\---

## pass5.query5

Using pandas and complete-chain non-reference rows only where genotype <> '0/0', group by pathway and tissue.
Compute:

non\_reference\_calls

mean\_vaf

mean\_log2\_matched\_expr

burden\_score = sum(vaf \* log2(matched\_expr\_count + 1))
Return: pathway, tissue, non\_reference\_calls, mean\_vaf, mean\_log2\_matched\_expr, burden\_score
Sort by pathway ascending, then tissue ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Filter to complete-chain non-reference rows first. Compute VAF per row. Map matched\_expr\_count by gene\_symbol and compute log2\_matched\_expr with numpy.log2(x + 1). mean\_vaf and mean\_log2\_matched\_expr are means over filtered rows. burden\_score is the sum of per-row vaf \* log2\_matched\_expr.

\---

## pass5.query6

Using pandas and sample\_dim only, compute population z-scores for each expression marker:

z\_ndhb from expr\_ndhb

z\_pgr5 from expr\_pgr5

z\_ndhk from expr\_ndhk
Use population standard deviation with ddof=0.
Then compute:

photosynthesis\_expr\_z\_mean = mean(z\_ndhb, z\_pgr5, z\_ndhk)
Return: sample\_id, z\_ndhb, z\_pgr5, z\_ndhk, photosynthesis\_expr\_z\_mean
Sort by photosynthesis\_expr\_z\_mean descending, then sample\_id ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Use sample\_dim only. For each marker, compute population mean and population standard deviation with ddof=0 across all samples. Then compute z-scores from raw marker values. photosynthesis\_expr\_z\_mean is the row-wise mean of the three z-scores. Sort after all z-score columns are complete.

\---

## pass5.query7

Using pandas and complete-chain matched rows only, create a condition-level integrative summary.
For each condition, compute:

distinct\_genes\_observed

mean\_matched\_expr

cv\_matched\_expr = population\_std(matched\_expr\_count, ddof=0) / mean(matched\_expr\_count)

mean\_vaf
Return: condition, distinct\_genes\_observed, mean\_matched\_expr, cv\_matched\_expr, mean\_vaf
Sort by condition ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Use complete-chain rows only. Map matched expression by gene\_symbol before grouping. distinct\_genes\_observed counts unique gene\_symbol values per condition. cv\_matched\_expr uses population standard deviation with ddof=0 divided by mean\_matched\_expr from the same grouped series. mean\_vaf is mean of per-row VAF.

\---

## pass5.query8

Using pandas, compute a plant-photosynthesis burden table at sample level.
Start from sample\_dim and left join in complete-chain non-reference calls where genotype <> '0/0'.
For each sample, compute:

non\_reference\_complete\_chain\_calls

high\_or\_moderate\_nonref\_calls where impact IN ('high','moderate')

total\_marker\_expr = expr\_ndhb + expr\_pgr5 + expr\_ndhk

log2\_total\_marker\_expr = log2(total\_marker\_expr + 1)

photosynthesis\_variant\_pressure = high\_or\_moderate\_nonref\_calls \* log2\_total\_marker\_expr
Return:
sample\_id, tissue, non\_reference\_complete\_chain\_calls, high\_or\_moderate\_nonref\_calls, total\_marker\_expr, log2\_total\_marker\_expr, photosynthesis\_variant\_pressure
Include samples with zero calls.
Sort by photosynthesis\_variant\_pressure descending, then sample\_id ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Preserve every sample from sample\_dim. Left join only the complete-chain non-reference call subset. Count high\_or\_moderate\_nonref\_calls only among non-reference complete-chain calls with impact high or moderate. Compute total\_marker\_expr from sample\_dim values, then log2\_total\_marker\_expr, then photosynthesis\_variant\_pressure. Include zero-call samples.

\---

## pass5.query9

Using pandas and complete-chain non-reference rows only where genotype <> '0/0', build a condition-by-gene decision summary.
Compute:

non\_reference\_calls

mean\_vaf

mean\_log2\_matched\_expr

expression\_weighted\_signal = mean\_vaf \* mean\_log2\_matched\_expr
Return: condition, gene\_symbol, non\_reference\_calls, mean\_vaf, mean\_log2\_matched\_expr, expression\_weighted\_signal
Sort by expression\_weighted\_signal descending, then gene\_symbol ascending, then condition ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Use only complete-chain non-reference rows. Group exactly by condition and gene\_symbol. Compute per-row VAF and per-row log2 matched expression first, then compute grouped means. expression\_weighted\_signal is mean\_vaf \* mean\_log2\_matched\_expr from the grouped means, not a sum of row products. Sort last.

\---

## pass5.query10

Using pandas and sample\_dim only, compute marker composition shares and imbalance.
For each sample, compute:

ndhb\_share = expr\_ndhb / (expr\_ndhb + expr\_pgr5 + expr\_ndhk)

pgr5\_share = expr\_pgr5 / (expr\_ndhb + expr\_pgr5 + expr\_ndhk)

ndhk\_share = expr\_ndhk / (expr\_ndhb + expr\_pgr5 + expr\_ndhk)

marker\_imbalance = max(share) - min(share)
Return: sample\_id, condition, ndhb\_share, pgr5\_share, ndhk\_share, marker\_imbalance
Sort by marker\_imbalance descending, then sample\_id ascending.
Round decimal outputs to 3 decimals.

Gemma 4 26B addendum:
Use sample\_dim only. Compute the denominator once from raw marker expressions for each sample. Compute all three shares from the same denominator. marker\_imbalance is max(three shares) minus min(three shares). Do not use log-transformed expression for shares. Re-apply marker\_imbalance DESC, sample\_id ASC after rounding.

