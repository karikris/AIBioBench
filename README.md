# AIBioBench

AIBioBench is a local benchmark suite for comparing LLMs on deterministic table-returning tasks over a small bioinformatics-style snowflake dataset.

The current repository is centered on the `photosynthesis_snowflake_v2` benchmark. It contains:

- a benchmark runner for local Ollama models
- 50 benchmark cases across SQL and Python/pandas passes
- gold answers and schemas
- per-pass and cross-pass analysis scripts
- a Kaggle publishing script for syncing the merged v2 results bundle

## Benchmark Structure

The active benchmark manifest is [benchmark_manifest.json](benchmark_manifest.json).

The current v2 benchmark has:

- `50` cases total
- `5` passes
- `3` default repeats per case
- SQL passes:
  - Pass 1: easy SQL
  - Pass 2: medium SQL
  - Pass 3: hard SQL
- Python passes:
  - Pass 4: extra-hard Python/pandas
  - Pass 5: extreme-hard Python/pandas

Core benchmark files:

- [benchmark_manifest.json](benchmark_manifest.json)
- [benchmark_cases.jsonl](benchmark_cases.jsonl)
- [gold_answers.jsonl](gold_answers.jsonl)
- [shared_dataset.json](shared_dataset.json)
- [results_template.jsonl](results_template.jsonl)
- [benchmark_case.schema.json](benchmark_case.schema.json)
- [gold_answer.schema.json](gold_answer.schema.json)
- [run_result.schema.json](run_result.schema.json)
- [standard_instructions.json](standard_instructions.json)

The flat CSV source tables used by the benchmark are:

- [fact_calls.csv](fact_calls.csv)
- [sample_dim.csv](sample_dim.csv)
- [variant_dim.csv](variant_dim.csv)
- [gene_dim.csv](gene_dim.csv)

All 50 query texts are collected in [QUERIES.md](QUERIES.md).

## Main Scripts

- [aibiobench.py](aibiobench.py)
  - Runs benchmark cases against local models.
  - Uses `benchmark_manifest.json` by default.
  - Writes raw result files and aggregate CSV summaries.
  - By default, appends into the latest matching results bundle under `results/`.

- [aibiobench-results.py](aibiobench-results.py)
  - Stages and publishes the current v2 results bundle to Kaggle.
  - Defaults to uploading the full bundle, including analysis subfolders.
  - Reads `KAGGLE_API_TOKEN` from `TOKENS.md`.

- [scripts/pass1_analysis.py](scripts/pass1_analysis.py)
- [scripts/pass2_analysis.py](scripts/pass2_analysis.py)
- [scripts/pass3_analysis.py](scripts/pass3_analysis.py)
- [scripts/pass4_analysis.py](scripts/pass4_analysis.py)
- [scripts/pass5_analysis.py](scripts/pass5_analysis.py)
  - Generate pass-specific CSV, Markdown, PNG, and SVG analyses.

- [scripts/pass123_overall_analysis.py](scripts/pass123_overall_analysis.py)
- [scripts/pass45_overall_analysis.py](scripts/pass45_overall_analysis.py)
- [scripts/all_passes_overview_analysis.py](scripts/all_passes_overview_analysis.py)
  - Generate combined analyses across multiple passes.

- [scripts/merge_results_bundle.py](scripts/merge_results_bundle.py)
  - Unions one results bundle into another and regenerates summary files.

## Running The Benchmark

Requirements:

- Python 3
- Ollama available locally
- benchmark models already pulled into Ollama

Basic examples:

```bash
python3 aibiobench.py --dry-run
python3 aibiobench.py --models qwen3.6-27b-sqlbench:latest
python3 aibiobench.py --models qwen3.6-27b-sqlbench:latest --passes 1 2 3
python3 aibiobench.py --models qwen3.6-27b-sqlbench:latest --limit 5 --dry-run
```

Useful runner flags:

- `--models`: override the default model list from the manifest
- `--passes`: run only selected passes
- `--case-ids`: run explicit case ids
- `--limit`: cap the selected case list after filtering
- `--repeats`: override the default repeat count
- `--output-dir`: force a specific output directory
- `--no-append-output`: create a fresh timestamped results directory instead of merging into the shared bundle
- `--bundle-dir-name`: override the shared bundle basename when appending
- `--dry-run`: print the selected cases without executing model calls

Current output behavior:

- By default, `aibiobench.py` appends into the latest matching v2 bundle inside `results/`.
- If no matching bundle exists, it creates a new timestamped bundle.
- The root files written by the runner include:
  - `detailed_results.csv`
  - `detailed_results.jsonl`
  - `run_results.jsonl`
  - `run_meta.json`
  - `summary_by_model.csv`
  - `summary_by_model_pass.csv`
  - failure-family and repeatability summaries

## Re-running Analyses

The analysis scripts operate on an existing results bundle.

Example:

```bash
RESULTS_DIR=results/photosynthesis_snowflake_v2__<timestamp>

python3 scripts/pass1_analysis.py "$RESULTS_DIR"
python3 scripts/pass2_analysis.py "$RESULTS_DIR"
python3 scripts/pass3_analysis.py "$RESULTS_DIR"
python3 scripts/pass4_analysis.py "$RESULTS_DIR"
python3 scripts/pass5_analysis.py "$RESULTS_DIR"

python3 scripts/pass123_overall_analysis.py "$RESULTS_DIR"
python3 scripts/pass45_overall_analysis.py "$RESULTS_DIR"
python3 scripts/all_passes_overview_analysis.py "$RESULTS_DIR"
```

Each script writes its outputs into a subfolder inside the chosen results bundle, for example:

- `pass1_analysis/`
- `pass45_overall_analysis/`
- `all_passes_overview_analysis/`

The generated artifacts typically include:

- summary CSVs
- Markdown notes or reports
- PNG visual reports
- SVG copies of the charts

## Publishing To Kaggle

The current Kaggle dataset target is:

- `https://www.kaggle.com/datasets/kristofferkari/aiobiobench-results`

The publisher script defaults to the full v2 results bundle, including analysis subfolders.

Examples:

```bash
python3 aibiobench-results.py --dry-run
python3 aibiobench-results.py
python3 aibiobench-results.py --root-only
```

Notes:

- `TOKENS.md` is expected to contain `KAGGLE_API_TOKEN=...`
- the script stages files into a temporary directory before publishing
- `--root-only` restores the older behavior of uploading only top-level files from the bundle

## Results And Git Tracking

Local benchmark output is intentionally not tracked in Git.

Ignored paths:

- `results/`
- `test results/`
- `TOKENS.md`

That means the repository tracks the benchmark definitions and scripts, while result bundles remain local unless you explicitly publish them elsewhere, such as Kaggle.

## Current Repo State

The repository now reflects the merged v2 workflow:

- benchmark runs append into a shared v2 results bundle by default
- per-pass and combined analysis scripts use dynamic model and attempt counts
- the Kaggle publisher uploads the full v2 bundle, not just root files
- `QUERIES.md` documents the full prompt set

## Acknowledgements

This project was developed with appreciation for the Plant Energy and Biotechnology Lab at Monash University and Dr Ermakova, Group Leader / Senior Lecturer, whose research environment helped inspire this work.

## Contributing

Suggestions are welcome on:

- benchmark design
- new cases and datasets
- scoring improvements
- analysis and reporting improvements
- reproducibility and validation

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Contact

Kris Kari  
toffe.kari@gmail.com
