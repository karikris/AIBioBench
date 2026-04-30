# Query Engineering Registry

This registry records query prompt evolution and v5 runtime prompt composition.

## Runs

- `runs/v2/`: v2 case/query snapshot from git history.
- `runs/v3/`: v3 case/query snapshot from git history.
- `runs/v4/`: v4 case/query snapshot with task-specific prompt guidance.
- `runs/v5/`: v5 shared base query snapshot; prompts match v2/v3 base query wording.

## v5 Runtime Addenda

- `v5/model_query_guidance.json`: model-specific addenda keyed by model and case.
- `v5/prompt_parts_preview.jsonl`: base query and addendum parts without dataset tables.
- `v5/model_query_guidance_summary.csv`: compact audit table.
- `v5/source_failure_points_by_case.csv`: combined v2/v3/v4 failure-point source table.

The runner appends the addendum after the base task text only when the manifest enables `query_engineering`.
Addenda are derived from v2/v3/v4 failures and avoid embedding complete gold answer rows, expected row counts, or row identifiers.
The source failure-point CSV keeps detailed audit labels; those labels are sanitized before becoming runtime guidance.

Current registry id: `photosynthesis_snowflake_v5_model_query_guidance`
