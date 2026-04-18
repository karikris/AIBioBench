# AIBioBench
A lightweight benchmark suite for comparing local Ollama AI models on data analytics and bioinformatics challenges.

AIBioBench is designed to run structured benchmarks using task and schema files in this repository, with model definitions configured in `ollama-bench.py`. The goal is to make local model testing reproducible, easy to extend, and useful for comparing model performance on realistic technical tasks.

## What this project includes

- Benchmark tasks for:
  - data analytics
  - bioinformatics
  - structured reasoning over datasets and instructions
- Benchmark and schema files:
  - `benchmark_cases.jsonl`
  - `gold_answers.jsonl`
  - `results_template.jsonl`
  - `benchmark_case.schema.json`
  - `gold_answer.schema.json`
  - `run_result.schema.json`
  - `shared_dataset.json`
  - `standard_instructions.json`
  - `benchmark_manifest.json`
- Model configuration and execution logic in `aibiobench.py`

## Goal

To evaluate local AI models on practical tasks at the intersection of:
- data analysis
- bioinformatics
- structured problem solving

## Acknowledgements

This project was developed with appreciation for the **Plant Energy and Biotechnology Lab at Monash University** and **Dr Ermakova**, Group Leader / Senior Lecturer, whose research environment inspired this work.

## Contributing

Collaborators are welcome.

Ideas for improving the benchmark design, extending the task suite, tightening schemas, or making the evaluations more robust and reproducible are very welcome. Suggestions for better data analytics and bioinformatics test cases are especially encouraged.

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

## Contact

**Kris Kari**  
toffe.kari@gmail.com
