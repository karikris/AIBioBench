#!/usr/bin/env python3
import sys
from pathlib import Path

import pass123_v2_v3_comparison as comparison


def main() -> int:
    if len(sys.argv) not in {3, 4}:
        print("usage: pass1_v2_v3_comparison.py <v2_results_dir> <v3_results_dir> [out_dir]", file=sys.stderr)
        return 2

    comparison.PASSES = ("1",)
    comparison.PASS_LABELS = {"1": "Pass 1", "total": "Total"}
    comparison.SCOPE_TITLE = "Pass 1"
    comparison.SCOPE_DESCRIPTION = "Pass 1 only; 10 SQL tasks, 14 models, and 420 attempts per run."
    comparison.RUNTIME_SCOPE_LABEL = "for Pass 1"

    v2_dir = Path(sys.argv[1]).resolve()
    v3_dir = Path(sys.argv[2]).resolve()
    out_dir = Path(sys.argv[3]).resolve() if len(sys.argv) == 4 else v3_dir / "pass1_v2_v3_comparison_analysis"
    comparison.run_comparison(v2_dir, v3_dir, out_dir, "pass1_v2_v3")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
