# Changes from the project copies of the pipeline code

All other files are byte-identical to the project versions that produced the results.

| File | Change | Reason |
|---|---|---|
| `scripts/pipeline/config/analysis_config.yaml` | `project_root: "<project root>"` -> `project_root: "SET_BY_setup_workspace.py"` | absolute path; filled in by setup_workspace.py |
| `scripts/pipeline/external_benchmark/features.py` | `ROOT = Path(r"<project root>")` -> `ROOT = Path(__file__).resolve().parents[1]` | absolute path -> workspace-relative |
| `scripts/pipeline/analysis/build_analysis_dataset_v1_1.py` | `ROOT = Path(r"<project root>")` -> `ROOT = Path(__file__).resolve().parents[2]` | absolute path -> workspace-relative |
| `scripts/pipeline/analysis/build_analysis_dataset_v1_2.py` | `ROOT = Path(r"<project root>")` -> `ROOT = Path(__file__).resolve().parents[2]` | absolute path -> workspace-relative |
| `scripts/pipeline/analysis/build_analysis_dataset_v1_3.py` | `ROOT = Path(r"<project root>")` -> `ROOT = Path(__file__).resolve().parents[2]` | absolute path -> workspace-relative |
| `scripts/pipeline/analysis/build_analysis_dataset_v1_4.py` | `ROOT = Path(r"<project root>")` -> `ROOT = Path(__file__).resolve().parents[2]` | absolute path -> workspace-relative |
| `scripts/pipeline/final_checks/check4_normalization_audit.py` | (API-key lookup from a local notes file) -> `key = os.environ["MP_API_KEY"]  # set your own Materials Project API k` | API key from environment, never from a file |
| `scripts/pipeline/final_checks/check4_normalization_audit.py` | `import re` -> `import os; import re` | needed by the API-key patch |
