#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


DEFAULT_DATASET_URL = "https://www.kaggle.com/datasets/kristofferkari/aiobiobench-results"
DEFAULT_DATASET_ID = "kristofferkari/aiobiobench-results"
DEFAULT_GITHUB_REPO_URL = "https://github.com/karikris/AIBioBench"
DEFAULT_RESULTS_DIR_NAME = "photosynthesis_snowflake_v3"
DEFAULT_RESULTS_GLOB = DEFAULT_RESULTS_DIR_NAME
REQUIRED_RESULTS_FILES = (
    "detailed_results.csv",
    "detailed_results.jsonl",
    "run_results.jsonl",
    "run_meta.json",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Stage the current AIBioBench v3 results bundle and publish its full contents "
            "to Kaggle as a dataset."
        )
    )
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent)
    p.add_argument("--results-dir", type=Path, default=None, help="Explicit results bundle to publish.")
    p.add_argument("--results-glob", default=DEFAULT_RESULTS_GLOB, help="Glob used to auto-discover the v3 bundle.")
    p.add_argument("--tokens-path", type=Path, default=Path(__file__).resolve().parent / "TOKENS.md")
    p.add_argument("--dataset-id", default=DEFAULT_DATASET_ID, help="Kaggle dataset id in owner/slug form.")
    p.add_argument("--dataset-title", default="AIBioBench v3 Results Bundle")
    p.add_argument("--dataset-subtitle", default="Merged root files and analysis subfolders for AIBioBench v3")
    p.add_argument("--dataset-url", default=DEFAULT_DATASET_URL)
    p.add_argument("--github-repo-url", default=DEFAULT_GITHUB_REPO_URL)
    p.add_argument("--staging-dir", type=Path, default=None, help="Optional persistent staging directory.")
    p.add_argument("--version-message", default=None, help="Optional Kaggle dataset version message.")
    p.add_argument("--root-only", action="store_true", help="Stage only top-level files from the results bundle.")
    p.add_argument("--private", action="store_true", help="Create a private dataset if it does not already exist.")
    p.add_argument("--dry-run", action="store_true", help="Prepare the staging bundle and print the planned Kaggle action.")
    return p.parse_args()


def discover_results_dir(results_root: Path, glob_pattern: str) -> Path:
    candidates = sorted(path for path in results_root.glob(glob_pattern) if path.is_dir())
    if not candidates:
        raise SystemExit(f"No results directories matched {glob_pattern!r} under {results_root}")
    return candidates[-1]


def validate_results_bundle(results_dir: Path) -> None:
    missing = [name for name in REQUIRED_RESULTS_FILES if not (results_dir / name).is_file()]
    if missing:
        missing_text = ", ".join(missing)
        raise SystemExit(
            f"{results_dir} is not a complete results bundle yet. Missing required files: {missing_text}"
        )


def extract_kaggle_token(tokens_path: Path) -> str:
    if not tokens_path.exists():
        raise SystemExit(f"TOKENS file not found: {tokens_path}")
    text = tokens_path.read_text(encoding="utf-8", errors="replace")
    export_match = re.search(r"KAGGLE_API_TOKEN\s*=\s*([^\s]+)", text)
    if export_match:
        return export_match.group(1).strip()
    raw_match = re.search(r"\bKGAT_[A-Za-z0-9]+\b", text)
    if raw_match:
        return raw_match.group(0)
    raise SystemExit(f"Could not find a Kaggle API token in {tokens_path}")


def iter_selected_files(results_dir: Path, include_subdirs: bool) -> Iterable[Path]:
    if include_subdirs:
        for path in sorted(results_dir.rglob("*")):
            if path.is_file():
                yield path
        return
    for path in sorted(results_dir.iterdir()):
        if path.is_file():
            yield path


def file_description(path: Path, rel_path: Path) -> str:
    name = rel_path.name
    rel_text = rel_path.as_posix()
    if name == "detailed_results.csv":
        return "Detailed benchmark attempt rows in CSV format."
    if name == "detailed_results.jsonl":
        return "Detailed benchmark attempt rows in JSONL format."
    if name == "run_results.jsonl":
        return "Benchmark run results in schema-compatible JSONL format."
    if name == "run_meta.json":
        return "Benchmark run metadata for the merged local v3 bundle."
    if name.startswith("summary_") and name.endswith(".csv"):
        return f"Summary table exported from the merged local v3 bundle: {rel_text}."
    return f"File from the AIBioBench v3 local results bundle: {rel_text}."


def build_dataset_metadata(
    dataset_id: str,
    title: str,
    subtitle: str,
    dataset_url: str,
    github_repo_url: str,
    source_dir: Path,
    files: Sequence[Tuple[Path, Path]],
) -> dict:
    description_lines = [
        "Full AIBioBench v3 results bundle published from the local merged results directory.",
        "",
        f"Kaggle dataset page: {dataset_url}",
        f"Local source bundle: `{source_dir}`",
        f"GitHub repository for code, benchmark definitions, schemas, and publishing scripts: {github_repo_url}",
        "This Kaggle dataset contains the published result bundle; the executable code lives in the GitHub repository.",
        "Scope of this upload: root result files plus analysis subfolders from the merged v3 bundle.",
        "",
        "Included files:",
    ]
    for _path, rel_path in files:
        description_lines.append(f"- `{rel_path.as_posix()}`")

    return {
        "title": title,
        "subtitle": subtitle,
        "description": "\n".join(description_lines),
        "id": dataset_id,
        "licenses": [{"name": "other"}],
        "keywords": ["benchmark", "llm", "bioinformatics"],
        "expectedUpdateFrequency": "weekly",
        "userSpecifiedSources": (
            f"AIBioBench local results bundle {source_dir}, "
            f"GitHub repository {github_repo_url}, and Kaggle dataset page {dataset_url}"
        ),
        "resources": [
            {"path": rel_path.as_posix(), "description": file_description(path, rel_path)}
            for path, rel_path in files
        ],
    }


def stage_files(
    source_dir: Path,
    staging_dir: Path,
    dataset_id: str,
    title: str,
    subtitle: str,
    dataset_url: str,
    github_repo_url: str,
    include_subdirs: bool,
) -> List[Path]:
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    selected: List[Tuple[Path, Path]] = []
    for path in iter_selected_files(source_dir, include_subdirs=include_subdirs):
        rel = path.relative_to(source_dir)
        destination = staging_dir / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        selected.append((path, rel))

    if not selected:
        raise SystemExit(f"No files selected from {source_dir}")

    metadata = build_dataset_metadata(dataset_id, title, subtitle, dataset_url, github_repo_url, source_dir, selected)
    (staging_dir / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return [path for path, _rel in selected]


def resolve_kaggle_command() -> List[str]:
    kaggle_bin = shutil.which("kaggle")
    if kaggle_bin:
        return [kaggle_bin]
    sibling_kaggle = Path(sys.executable).with_name("kaggle")
    if sibling_kaggle.exists():
        return [str(sibling_kaggle)]
    try:
        import kaggle  # type: ignore  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "Kaggle CLI is not installed. Install the official client first with "
            "`python3 -m pip install kaggle`."
        ) from exc
    return [sys.executable, "-m", "kaggle"]


def run_cmd(cmd: List[str], env: dict, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        env=env,
        text=True,
        capture_output=capture,
        check=False,
    )


def dataset_exists(kaggle_cmd: List[str], dataset_id: str, env: dict) -> bool:
    probe = run_cmd(kaggle_cmd + ["datasets", "files", dataset_id, "--page-size", "1"], env=env, capture=True)
    if probe.returncode == 0:
        return True
    stderr = (probe.stderr or "") + "\n" + (probe.stdout or "")
    lowered = stderr.lower()
    if "not found" in lowered or "404" in lowered:
        return False
    raise SystemExit(f"Failed to probe Kaggle dataset {dataset_id}: {stderr.strip()}")


def publish_dataset(kaggle_cmd: List[str], staging_dir: Path, dataset_id: str, version_message: str, env: dict, private: bool) -> str:
    if dataset_exists(kaggle_cmd, dataset_id, env):
        cmd = kaggle_cmd + [
            "datasets",
            "version",
            "-p",
            str(staging_dir),
            "-m",
            version_message,
            "-q",
            "-t",
            "-r",
            "skip",
        ]
    else:
        cmd = kaggle_cmd + [
            "datasets",
            "create",
            "-p",
            str(staging_dir),
            "-q",
            "-t",
            "-r",
            "skip",
        ]
        if not private:
            cmd.append("--public")

    completed = run_cmd(cmd, env=env, capture=True)
    if completed.returncode != 0:
        stderr = (completed.stderr or "") + "\n" + (completed.stdout or "")
        raise SystemExit(f"Kaggle upload failed:\n{stderr.strip()}")
    return f"https://www.kaggle.com/datasets/{dataset_id}"


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    results_root = repo_root / "results"
    results_dir = args.results_dir.resolve() if args.results_dir else discover_results_dir(results_root, args.results_glob)
    validate_results_bundle(results_dir)
    token = extract_kaggle_token(args.tokens_path.resolve())

    dataset_id = args.dataset_id
    version_message = args.version_message or f"Update full v3 results bundle from {results_dir.name} at {utc_now_iso()}"

    with tempfile.TemporaryDirectory(prefix="aibiobench-kaggle-") as tmp_dir:
        staging_dir = args.staging_dir.resolve() if args.staging_dir else Path(tmp_dir) / dataset_id.split("/", 1)[1]
        selected_files = stage_files(
            source_dir=results_dir,
            staging_dir=staging_dir,
            dataset_id=dataset_id,
            title=args.dataset_title,
            subtitle=args.dataset_subtitle,
            dataset_url=args.dataset_url,
            github_repo_url=args.github_repo_url,
            include_subdirs=not args.root_only,
        )

        summary = {
            "results_dir": str(results_dir),
            "staging_dir": str(staging_dir),
            "dataset_id": dataset_id,
            "target_dataset_url": args.dataset_url,
            "github_repo_url": args.github_repo_url,
            "include_subdirs": not args.root_only,
            "selected_files": [str(path.relative_to(results_dir)) for path in selected_files],
            "version_message": version_message,
            "dry_run": args.dry_run,
        }

        if args.dry_run:
            print(json.dumps(summary, indent=2))
            return

        kaggle_cmd = resolve_kaggle_command()
        env = os.environ.copy()
        env["KAGGLE_API_TOKEN"] = token
        kaggle_config_dir = Path(tmp_dir) / ".kaggle"
        kaggle_config_dir.mkdir(parents=True, exist_ok=True)
        env.setdefault("KAGGLE_CONFIG_DIR", str(kaggle_config_dir))
        dataset_url = publish_dataset(
            kaggle_cmd=kaggle_cmd,
            staging_dir=staging_dir,
            dataset_id=dataset_id,
            version_message=version_message,
            env=env,
            private=args.private,
        )
        summary["dataset_url"] = dataset_url
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
