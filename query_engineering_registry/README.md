# Query Engineering Registry

This registry records query prompt evolution and v5 runtime prompt composition.

## Runs

- `runs/v2/`: v2 case/query snapshot from git history.
- `runs/v3/`: v3 case/query snapshot from git history.
- `runs/v4/`: v4 case/query snapshot with task-specific prompt guidance.
- `runs/v5/`: v5 shared base query snapshot; prompts match v2/v3 base query wording.

## v5 Runtime Prompt Parts

- `v5/model_query_guidance.json`: model-specific addenda keyed by model and case.
- `v5/prompt_parts_preview.jsonl`: five-part prompt preview without dataset tables.
- `v5/model_query_guidance_summary.csv`: compact audit table.
- `v5/source_failure_points_by_case.csv`: combined v2/v3/v4 failure-point source table.

When the manifest enables `query_engineering`, the runner now builds a five-part prompt:

1. `standard_base_instructions`: shared SQL/Python benchmark rules from `standard_instructions.json`.
2. `standard_model_instruction`: a concise model-specific standard warning, either read from the registry or derived from the model profile.
3. `query_base_context`: benchmark metadata, schema, dataset tables, base query text, and required output columns.
4. `query_model_guidance`: model-and-query-specific guidance keyed by model and case.
5. `query_model_footer`: a short model-specific final self-check footer, either read from the registry or derived from the model profile.

Addenda are derived from v2/v3/v4 failures and avoid embedding complete gold answer rows, expected row counts, or row identifiers.
The source failure-point CSV keeps detailed audit labels; those labels are sanitized before becoming runtime guidance.

Current registry id: `photosynthesis_snowflake_v5_model_query_guidance`
