# AIBioBench Pass 3 Analysis

Pass 3 contains eight hard SQL-style tasks over the plant/variant snowflake. It stresses join-status classification, complete-chain aggregation, dimension-preserving audits, ranking, anti-join logic, and decision-support grouping.

## Model Summary

| Model | Exact | Accuracy | Mean Cell Accuracy | Row Count Match | Wall Time | Mean Gen TPS |
|---|---:|---:|---:|---:|---:|---:|
| Gemma 31B 64k | 2/8 | 25.0% | 85.9% | 87.5% | 313.5s | 3.63 |
| Gemma 31B 256k | 2/8 | 25.0% | 85.9% | 87.5% | 333.8s | 3.18 |
| Gemma 26B 64k | 1/8 | 12.5% | 56.1% | 62.5% | 82.1s | 15.69 |
| Gemma 26B 256k | 1/8 | 12.5% | 55.7% | 62.5% | 97.9s | 14.16 |
| Qwen 36B 64k | 0/8 | 0.0% | 59.8% | 50.0% | 181.8s | 10.34 |
| Qwen 36B 256k | 0/8 | 0.0% | 57.5% | 37.5% | 200.8s | 9.11 |
| Qwen Coder 30B 256k | 0/8 | 0.0% | 53.2% | 37.5% | 98.3s | 13.43 |
| Qwen Coder 30B 64k | 0/8 | 0.0% | 42.2% | 37.5% | 76.5s | 16.57 |
| Phi4 Mini 128k | 0/8 | 0.0% | 25.1% | 25.0% | 63.6s | 20.21 |

## Case Summary

| Query | Exact Models | Mean Cell Accuracy | Row Count Mismatches | Same Count But Wrong | Dominant Failure |
|---|---:|---:|---:|---:|---|
| Q1 | 2/9 | 90.7% | 1 | 6 | same_count_wrong_values |
| Q2 | 0/9 | 58.8% | 5 | 4 | row_count_mismatch |
| Q3 | 0/9 | 66.1% | 1 | 8 | same_count_wrong_values |
| Q4 | 0/9 | 37.5% | 6 | 3 | row_count_mismatch |
| Q5 | 2/9 | 86.2% | 1 | 6 | same_count_wrong_values |
| Q6 | 0/9 | 48.9% | 6 | 3 | row_count_mismatch |
| Q7 | 2/9 | 44.8% | 4 | 3 | row_count_mismatch |
| Q8 | 0/9 | 30.3% | 9 | 0 | row_count_mismatch |

## Query Notes

- **Q1**: Full snowflake left join with row-level join_status classification; failures usually confuse MISSING_GENE, MISSING_SAMPLE, and MISSING_VARIANT edge rows.
- **Q2**: Complete-chain tissue/gene aggregation with VAF arithmetic; failures cluster around excluding incomplete chains and averaging VAF per fact row.
- **Q3**: Gene-preserving coverage audit; models must include zero-call genes and count fact rows through variants without inventing missing genes.
- **Q4**: High-impact condition summary after sample and variant joins; common errors are missing zero-alt high-impact calls or using the wrong denominator.
- **Q5**: Sample-preserving genotype-class summary; failures usually mishandle S5, reference calls, or non-reference quality averaging.
- **Q6**: Complete-chain tissue/gene ranking; models must aggregate first, then dense-rank within tissue and preserve the requested sort order.
- **Q7**: Anti-join audit across sample, variant, and gene dimensions; failures tend to miss unused dimension rows or assign the wrong reason.
- **Q8**: Decision-support grouping over complete-chain non-reference calls; errors come from leaking reference calls or grouping by the wrong gene role.
