# AIBioBench v5.1 Query Snapshot

This directory preserves the exact query-engineering inputs intended for v5.1 runs:

- `benchmark_manifest.json`: manifest pointing runtime query engineering at the v5.1 Markdown registry.
- `aibiobench_v51_task_specific_prompts.md`: single Markdown source for all v5.1 prompt parts.

At runtime, `aibiobench.py` reconstructs each prompt from the Markdown source in this order:

1. common JSON contract
2. model-specific task agenda
3. task-specific fenced prompt body with actual CSV tables inserted
4. target-model addendum for the model being run
5. footer focus
