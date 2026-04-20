# AIBioBench Pass 2 Analysis

Pass 2 contains eight medium SQL-style tasks over the same plant/variant snowflake. It stresses full-chain joins, full outer joins, conditional aggregation, VAF arithmetic, and dimension-preserving summaries.

## Model Summary

| Model | Exact | Accuracy | Mean Cell Accuracy | Row Count Match | Wall Time | Mean Gen TPS |
|---|---:|---:|---:|---:|---:|---:|
| Gemma 31B 64k | 4/8 | 50.0% | 83.9% | 87.5% | 344.0s | 3.67 |
| Gemma 31B 256k | 4/8 | 50.0% | 83.9% | 87.5% | 371.4s | 3.25 |
| Qwen 36B 256k | 2/8 | 25.0% | 61.9% | 62.5% | 233.6s | 8.90 |
| Gemma 26B 256k | 2/8 | 25.0% | 58.9% | 50.0% | 87.9s | 14.85 |
| Gemma 26B 64k | 2/8 | 25.0% | 57.2% | 50.0% | 78.7s | 16.41 |
| Qwen 36B 64k | 1/8 | 12.5% | 56.4% | 37.5% | 206.2s | 10.28 |
| Qwen Coder 30B 256k | 0/8 | 0.0% | 47.0% | 37.5% | 98.5s | 14.49 |
| Qwen Coder 30B 64k | 0/8 | 0.0% | 46.7% | 37.5% | 82.9s | 17.18 |
| Phi4 Mini 128k | 0/8 | 0.0% | 32.0% | 25.0% | 90.5s | 19.25 |

## Case Summary

| Query | Exact Models | Mean Cell Accuracy | Row Count Mismatches | Same Count But Wrong | Dominant Failure |
|---|---:|---:|---:|---:|---|
| Q1 | 0/9 | 67.4% | 9 | 0 | row_count_mismatch |
| Q2 | 5/9 | 91.6% | 1 | 3 | exact |
| Q3 | 6/9 | 69.4% | 3 | 0 | exact |
| Q4 | 0/9 | 50.4% | 4 | 5 | same_count_wrong_values |
| Q5 | 0/9 | 17.6% | 7 | 2 | row_count_mismatch |
| Q6 | 2/9 | 37.3% | 6 | 1 | row_count_mismatch |
| Q7 | 2/9 | 82.2% | 0 | 7 | same_count_wrong_values |
| Q8 | 0/9 | 53.2% | 4 | 5 | same_count_wrong_values |

## Query Notes

- **Q1**: Complete inner join across sample, variant, and gene dimensions; common failures leak V5/G999, S999, or V999 rows that should be removed.
- **Q2**: Fact-preserving left join across the full snowflake; models must keep all fact rows and insert nulls only where dimensions are missing.
- **Q3**: Full outer join between fact_calls and variant_dim; the hard parts are preserving orphan V6 and fact-only V999 while sorting coalesced keys.
- **Q4**: Condition-by-impact aggregation after inner joining sample and variant dimensions; common failures undercount control/high and miss fact-row weighting.
- **Q5**: VAF summary by gene after variant and gene joins; models often misapply the VAF denominator, drop/keep the wrong fact rows, or add unmatched genes.
- **Q6**: Complete four-table inner joins by tissue; failures usually include root/S5, G999, or compute expression over samples instead of joined calls.
- **Q7**: Sample-preserving conditional aggregate; the key trap is counting zero-alt high-impact calls and keeping zero-call samples.
- **Q8**: Gene-level read and quality summary; errors cluster around NDHB totals, NDHK average quality, and leakage of unmatched genes.
