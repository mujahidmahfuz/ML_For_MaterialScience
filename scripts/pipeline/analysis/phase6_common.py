"""Shared loaders for Phase 6 analytics (config, targets, groups, predictor lists, run log)."""
from __future__ import annotations

import csv
import importlib
import platform
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

EDA_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = EDA_ROOT / "00_config" / "analysis_config.yaml"
RUN_LOG = EDA_ROOT / "logs" / "run_log.csv"
RUN_LOG_FIELDS = [
    "timestamp", "dataset_version", "script", "stage", "target",
    "tier", "group", "n", "seed", "output_path",
]


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def project_path(cfg: dict, key: str) -> Path:
    return Path(cfg["paths"]["project_root"]) / cfg["paths"][key]


def load_data_dictionary(cfg: dict) -> pd.DataFrame:
    return pd.read_csv(project_path(cfg, "data_dictionary"))


def build_predictor_lists(cfg: dict, dd: pd.DataFrame) -> dict[str, list[str]]:
    """Reproduce build_datasets.py tier rules, restricted to predictor families."""
    rules = cfg["predictor_rules"]
    oxidation = list(rules["oxidation_cols"])
    in_tier1_groups = dd["group"].isin(rules["tier1_dictionary_groups"])
    tier1 = [c for c in dd.loc[in_tier1_groups, "column"] if c not in oxidation]
    tier2 = tier1 + oxidation
    excluded = {c for cols in rules["excluded_predictors"].values() for c in cols}
    physics = dd.loc[dd["group"] == rules["tier3_added_dictionary_group"], "column"]
    tier3 = tier2 + [c for c in physics if c not in excluded]
    return {"tier1": tier1, "tier2": tier2, "tier3": tier3}


def write_predictor_lists(cfg: dict, lists: dict[str, list[str]]) -> None:
    for tier, cols in lists.items():
        path = EDA_ROOT / cfg["tiers"][tier]["predictors_file"]
        path.write_text("\n".join(cols) + "\n", encoding="utf-8")


def read_predictor_list(cfg: dict, tier: str) -> list[str]:
    path = EDA_ROOT / cfg["tiers"][tier]["predictors_file"]
    return [c for c in path.read_text(encoding="utf-8").splitlines() if c.strip()]


def load_feature_repository(cfg: dict, columns: list[str] | None = None) -> pd.DataFrame:
    return pd.read_parquet(project_path(cfg, "feature_repository_parquet"), columns=columns)


def physics_complete_mask(cfg: dict, repo: pd.DataFrame) -> pd.Series:
    return repo[cfg["predictor_rules"]["physics_bundle"]].notna().all(axis=1)


def load_target(cfg: dict, name: str, extra_cols: list[str] | None = None) -> pd.DataFrame:
    """Clean population for one target: material_id, provenance cols, and `value`."""
    spec = cfg["targets"][name]
    path = project_path(cfg, "target_harmonization_dir") / spec["file"]
    base = ["material_id", "reduced_formula", "_source", "Experimental", "Material_Type"]
    wanted = base + [spec["value_col"]] + ([spec["valid_col"]] if spec["valid_col"] else [])
    wanted += [c for c in (extra_cols or []) if c not in wanted]
    df = pd.read_csv(path, usecols=wanted, low_memory=False)
    keep = df[spec["valid_col"]].astype(bool) if spec["valid_col"] else df[spec["value_col"]].notna()
    out = df.loc[keep].rename(columns={spec["value_col"]: "value"}).reset_index(drop=True)
    if len(out) != spec["expected_n"]:
        raise ValueError(f"{name}: clean N {len(out)} != frozen expected_n {spec['expected_n']}")
    if not out["material_id"].is_unique:
        raise ValueError(f"{name}: material_id is not unique in the clean population")
    return out


def load_group_ids(cfg: dict) -> dict[str, set]:
    membership = pd.read_parquet(project_path(cfg, "group_membership"))
    return {name: set(membership.loc[membership[col], "material_id"]) for name, col in cfg["groups"].items()}


def tier_path(cfg: dict, tier: str) -> Path:
    return project_path(cfg, "tiers_dir") / cfg["tiers"][tier]["data_file"]


def log_run(cfg: dict, script: str, stage: str, target: str, tier: str,
            group: str, n: int, output_path: str | Path) -> None:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    is_new = not RUN_LOG.exists()
    with open(RUN_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RUN_LOG_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "dataset_version": cfg["analysis_dataset_version"],
            "script": script, "stage": stage, "target": target, "tier": tier,
            "group": group, "n": n, "seed": cfg["random_seed"],
            "output_path": str(output_path),
        })


def write_package_versions(path: Path, dataset_version: str) -> None:
    names = ["pandas", "numpy", "scipy", "matplotlib", "seaborn", "sklearn", "xgboost", "shap", "pyarrow", "yaml",
             "pymatgen"]
    lines = [f"analysis_dataset_version {dataset_version}", f"recorded {datetime.now().isoformat(timespec='seconds')}",
             f"python {platform.python_version()}", f"platform {platform.platform()}"]
    for name in names:
        try:
            lines.append(f"{name} {getattr(importlib.import_module(name), '__version__', 'unknown')}")
        except ImportError:
            lines.append(f"{name} NOT INSTALLED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
