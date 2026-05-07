# AIBioBench v6 Code-Footer Query Snapshot

This directory contains the v6 oracle-code control prompt snapshot.

v6 prompts are intentionally not comparable to normal benchmark prompts. Each
case uses the original v2 prompt text and appends only this footer:

````text
Produce the output using the following code:
```<sql-or-python>
<reference solution code>
```
````

Footer policy:

- passes 1-3 use SQL reference code
- passes 4-5 use Python/pandas reference code
- no gold-answer rows are pasted directly into the footer
- every reference solution is validated against `gold_answers.jsonl`

Generated files:

- `benchmark_cases.jsonl`: v6 cases used by the runner
- `standard_instructions.json`: schema-compatible instruction ids with v2 instruction text
- `reference_solutions.jsonl`: per-case reference SQL/Python code
- `prompt_preview.jsonl`: audit preview of the final case prompt field
- `benchmark_manifest.json`: v6 manifest snapshot

Benchmark mode: oracle-code control. Scores measure code-following and JSON
output compliance, not independent reasoning.
