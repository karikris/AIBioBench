# AIBioBench Pass 4 Analysis

Pass 4 contains eight extra-hard Python/pandas tasks in the completed run. It stresses reconciliation metrics, complete-chain aggregation, expression mapping, sample burden scoring, orphan-key reporting, and final presentation-table construction.

## Model Summary

| Model | Exact | Accuracy | Mean Cell Accuracy | Row Count Match | Wall Time | Mean Gen TPS |
|---|---:|---:|---:|---:|---:|---:|
| Gemma 31B 64k | 0/8 | 0.0% | 44.2% | 50.0% | 647.7s | 3.56 |
| Gemma 31B 256k | 0/8 | 0.0% | 44.2% | 50.0% | 739.5s | 3.12 |
| Qwen 36B 256k | 0/8 | 0.0% | 40.1% | 25.0% | 281.2s | 9.32 |
| Gemma 26B 256k | 0/8 | 0.0% | 37.1% | 37.5% | 147.5s | 15.04 |
| Qwen 36B 64k | 0/8 | 0.0% | 37.0% | 37.5% | 231.0s | 10.94 |
| Gemma 26B 64k | 0/8 | 0.0% | 33.9% | 37.5% | 94.5s | 16.19 |
| Qwen Coder 30B 256k | 0/8 | 0.0% | 29.9% | 50.0% | 149.5s | 13.19 |
| Qwen Coder 30B 64k | 0/8 | 0.0% | 29.3% | 25.0% | 127.3s | 15.10 |
| Phi4 Mini 128k | 0/8 | 0.0% | 13.9% | 12.5% | 80.8s | 19.78 |

## Case Summary

| Query | Exact Models | Mean Cell Accuracy | Row Count Mismatches | Same Count But Wrong | Dominant Failure |
|---|---:|---:|---:|---:|---|
| Q1 | 0/9 | 78.5% | 0 | 9 | same_count_wrong_values |
| Q2 | 0/9 | 14.1% | 9 | 0 | row_count_mismatch |
| Q3 | 0/9 | 26.7% | 9 | 0 | row_count_mismatch |
| Q4 | 0/9 | 15.3% | 9 | 0 | row_count_mismatch |
| Q5 | 0/9 | 45.9% | 3 | 6 | same_count_wrong_values |
| Q6 | 0/9 | 54.4% | 1 | 8 | same_count_wrong_values |
| Q7 | 0/9 | 23.3% | 6 | 3 | row_count_mismatch |
| Q8 | 0/9 | 16.9% | 9 | 0 | row_count_mismatch |

## Query Notes

- **Q1**: Pandas reconciliation summary; failures indicate weak audit counting across complete chains, missing dimensions, and unused dimension rows.
- **Q2**: Complete-chain condition/pathway aggregation; hard parts are expression mapping, pathway grouping, and exact numeric rounding.
- **Q3**: Complete-chain non-reference batch/gene-role summary; models must filter genotype, compute VAF, and map expression to PGR5 correctly.
- **Q4**: Genes observed in both control and non-control conditions; this is a narrow decision-support filter with one expected row.
- **Q5**: Gene-preserving profile through variant, fact, and sample joins; failures usually mishandle zero-call genes, distinct matched samples, or expression averaging.
- **Q6**: Sample-level burden table; models must filter non-reference high/moderate complete-chain calls while preserving zero-burden samples.
- **Q7**: Union-style orphan-key report; failures tend to miss one source table, duplicate keys, or assign the wrong orphan type.
- **Q8**: Final presentation table; this stresses complete-chain filtering, matched expression mapping, VAF/log2 arithmetic, exact column order, and multi-key sorting.
