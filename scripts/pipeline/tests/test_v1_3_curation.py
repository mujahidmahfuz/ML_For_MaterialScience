"""Tests for the v1.3 Curie curation rules (synthetic rows only)."""
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import build_analysis_dataset_v1_3 as b  # noqa: E402

RULES = yaml.safe_load((SRC.parent / "00_config" / "v1_3_curation_rules.yaml").read_text(encoding="utf-8"))["curie"]


def flags(rows: list[tuple], ordering: dict | None = None) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["reduced_formula", "TC_K_clean"])
    return b.curie_flags(df, ordering or {}, RULES).set_index(df["reduced_formula"])


def test_symbols_parses_formulas_and_rejects_garbage():
    assert b.symbols("Fe3O4") == {"Fe", "O"}
    assert b.symbols("not a formula!!") == set()


@pytest.mark.parametrize("formula", ["BaTiO3", "LiNbO3", "ZnO", "Si", "GaAs", "MgB2"])
def test_non_magnetic_compounds_are_flagged_by_c1(formula):
    assert flags([(formula, 300.0)]).loc[formula, "C1_no_magnetism_capable_element"]


@pytest.mark.parametrize("formula", ["Fe", "SrRuO3", "EuO", "UGe2", "CrI3", "Fe3O4", "MnAs"])
def test_genuine_magnets_are_not_flagged_by_c1(formula):
    assert not flags([(formula, 300.0)]).loc[formula, "C1_no_magnetism_capable_element"]


def test_elemental_rule_keeps_ferromagnetic_elements_only():
    f = flags([("Fe", 1043.0), ("Gd", 293.0), ("Cu", 5.0), ("Pb", 7.2)])
    assert not f.loc["Fe", "C2_elemental_non_magnet"] and not f.loc["Gd", "C2_elemental_non_magnet"]
    assert f.loc["Cu", "C2_elemental_non_magnet"] and f.loc["Pb", "C2_elemental_non_magnet"]
    assert not flags([("Fe3O4", 858.0)]).loc["Fe3O4", "C2_elemental_non_magnet"]


def test_temperature_thresholds_are_strict():
    f = flags([("Fe", 0.9), ("Co", 1.0), ("Ni", 1400.0), ("Gd", 1400.5)])
    assert f["C3_below_1K"].tolist() == [True, False, False, False]
    assert f["C4_above_1400K"].tolist() == [False, False, False, True]


def test_afm_only_formula_rule_needs_every_label_to_be_afm():
    ordering = {"NiO": {"AFM"}, "Fe3O4": {"FiM"}, "MnBi": {"AFM", "FM"}}
    f = flags([("NiO", 520.0), ("Fe3O4", 858.0), ("MnBi", 630.0), ("CrI3", 61.0)], ordering)
    assert f["C5_afm_only_formula"].tolist() == [True, False, False, False]


def test_reason_text_lists_every_fired_rule():
    row = pd.Series({c: False for c in b.CURIE_RULES})
    row["C1_no_magnetism_capable_element"] = row["C3_below_1K"] = True
    assert b.reason_text(row) == "v1.3 R1: C1+C3"
