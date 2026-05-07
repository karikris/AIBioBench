# Query Engineering Registry

This registry records query prompt evolution and v5 runtime prompt composition.

## Runs

- `runs/v2/`: v2 case/query snapshot from git history.
- `runs/v3/`: v3 case/query snapshot from git history.
- `runs/v4/`: v4 case/query snapshot with task-specific prompt guidance.
- `runs/v5/`: v5 shared base query snapshot; prompts match v2/v3 base query wording.
- `runs/v5.1/`: v5.1 manifest and task-specific Markdown prompt snapshot.
- `runs/v6/`: v6 oracle-code control snapshot; prompts use original v2 query text plus a reference SQL/Python code footer.

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

## v5.1 Runtime Prompt Parts

- `v5.1/aibiobench_v51_task_specific_prompts.md`: single Markdown source for common JSON contract, model agendas, all 50 task-specific prompt templates, and target-model addenda.

When the manifest enables v5.1 query engineering, the runner builds a five-part prompt:

1. `common_json_contract`: shared JSON-only output contract.
2. `model_specific_task_agenda`: target model core agenda plus SQL agenda for passes 1-3 or Pandas agenda for passes 4-5.
3. `task_specific_prompt`: fenced task prompt body with only the CSV tables named by that case.
4. `target_model_addendum`: only the addendum bullet that names the model being run.
5. `footer_focus`: target model footer focus, rendered after the target-model addendum.

Current v5.1 registry id: `photosynthesis_snowflake_v5_1_task_specific_prompts`

## v6 Code-Footer Control

- `runs/v6/benchmark_cases.jsonl`: original v2 prompt text with only the code-footer appended.
- `runs/v6/reference_solutions.jsonl`: reference SQL for passes 1-3 and Python/pandas for passes 4-5.
- `runs/v6/prompt_preview.jsonl`: audit preview of the final case prompt field.

v6 is an oracle-code control. Reference solution code is present in each prompt,
so v6 scores measure code-following and JSON output compliance rather than
independent data reasoning. Do not compare v6 scores directly with v2-v5.1
benchmark scores.
