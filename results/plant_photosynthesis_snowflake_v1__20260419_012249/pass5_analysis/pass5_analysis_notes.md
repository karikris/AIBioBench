# AIBioBench Pass 5 Analysis

Pass 5 contains eight extreme-hard Python/pandas tasks in the completed run. It stresses expression transforms, matched-expression mapping, population statistics, z-scores, coefficients of variation, ranking, and decision-support burden scores.

## Model Summary

| Model | Exact | Accuracy | Mean Cell Accuracy | Row Count Match | Wall Time | Mean Gen TPS |
|---|---:|---:|---:|---:|---:|---:|
| Gemma 31B 256k | 0/8 | 0.0% | 48.2% | 100.0% | 682.9s | 3.16 |
| Gemma 31B 64k | 0/8 | 0.0% | 43.5% | 87.5% | 642.1s | 3.41 |
| Qwen 36B 64k | 0/8 | 0.0% | 34.7% | 75.0% | 236.6s | 11.05 |
| Gemma 26B 64k | 0/8 | 0.0% | 33.4% | 50.0% | 110.6s | 15.26 |
| Gemma 26B 256k | 0/8 | 0.0% | 33.3% | 50.0% | 121.7s | 14.78 |
| Qwen 36B 256k | 0/8 | 0.0% | 32.1% | 62.5% | 297.9s | 9.04 |
| Qwen Coder 30B 256k | 0/8 | 0.0% | 30.7% | 62.5% | 164.4s | 12.66 |
| Qwen Coder 30B 64k | 0/8 | 0.0% | 30.5% | 62.5% | 137.6s | 15.22 |
| Phi4 Mini 128k | 0/8 | 0.0% | 10.4% | 12.5% | 57.3s | 19.72 |

## Case Summary

| Query | Exact Models | Mean Cell Accuracy | Row Count Mismatches | Same Count But Wrong | Dominant Failure |
|---|---:|---:|---:|---:|---|
| Q1 | 0/9 | 37.0% | 1 | 8 | same_count_wrong_values |
| Q2 | 0/9 | 38.8% | 7 | 2 | row_count_mismatch |
| Q3 | 0/9 | 34.7% | 8 | 1 | row_count_mismatch |
| Q4 | 0/9 | 23.1% | 1 | 8 | same_count_wrong_values |
| Q5 | 0/9 | 32.5% | 5 | 4 | row_count_mismatch |
| Q6 | 0/9 | 17.8% | 3 | 6 | same_count_wrong_values |
| Q7 | 0/9 | 35.6% | 1 | 8 | same_count_wrong_values |
| Q8 | 0/9 | 44.4% | 1 | 8 | same_count_wrong_values |

## Query Notes

- **Q1**: Sample-only expression feature engineering; failures usually come from log2 transforms, ratio denominators, or rounding.
- **Q2**: Complete-chain matched expression and weighted VAF per call; models must map gene-specific expression and keep only matched calls.
- **Q3**: Condition/gene statistical summary; hard parts are complete-chain filtering, expression mapping, median, and population standard deviation.
- **Q4**: Stress-vs-control log2 marker deltas; failures tend to average before transforming or group high_light/drought incorrectly.
- **Q5**: Non-reference pathway/tissue burden score; models must combine complete-chain filtering, VAF, log2 expression, and grouped summation.
- **Q6**: Sample-level expression z-scores; models must use population standard deviation and sort by the derived mean score.
- **Q7**: Condition-level integrative summary; the coefficient of variation and mean VAF require correct complete-chain fact-row weighting.
- **Q8**: Sample-level photosynthesis burden table; failures usually involve preserving zero-call samples and applying the high/moderate pressure formula.
