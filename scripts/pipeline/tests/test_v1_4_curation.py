"""Tests for the v1.4 secondary-target screens (rules in 00_config/v1_4_curation_rules.yaml), on synthetic rows."""
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import build_analysis_dataset_v1_4 as b  # noqa: E402

RULES = yaml.safe_load((ROOT / "00_config/v1_4_curation_rules.yaml").read_text(encoding="utf-8"))


def mass_frame(rows):
    return pd.DataFrame(rows, columns=["reduced_formula", "Ms_massMagnetization_clean"])


def test_mass_ceiling_depends_on_heavy_rare_earth_content():
    df = mass_frame([("Fe0.7Co0.3", 257.0), ("FeCo", 240.0), ("Dy", 350.0), ("Dy", 400.0), ("Fe3O4", 92.0)])
    flags = b.ms_mass_flags(df, RULES)
    assert flags["M1_above_ceiling_no_heavy_RE"].tolist() == [True, False, False, False, False]
    assert flags["M2_above_ceiling_heavy_RE"].tolist() == [False, False, False, True, False]


def test_mass_zero_is_flagged_but_small_positive_is_kept():
    flags = b.ms_mass_flags(mass_frame([("Fe", 0.0), ("Fe", 0.001)]), RULES)
    assert flags["M3_zero_value"].tolist() == [True, False]


def volume_frame(rows):
    return pd.DataFrame(rows, columns=["reduced_formula", "Ms_volumeMagnetization_clean", "unit_raw"])


def test_volume_ceiling_zero_and_mass_unit_misparse():
    df = volume_frame([("FeCo", 2.884e6, "emu/cm^3"), ("FeCo", 1.95e6, "kA/m"), ("Dy", 3.0e6, "A/m"), ("Dy", 3.3e6, "A/m"),
                       ("Mn0.55Al0.45", 0.0, "A/m"), ("Fe4Ni", 120.0, "A.m^2/kg"), ("Fe19Ni", 135.0, "Am2/kg"), ("Fe", 1.7e6, "A/m")])
    f = b.ms_volume_flags(df, RULES)
    assert f["V1_above_ceiling_no_heavy_RE"].tolist() == [True, False, False, False, False, False, False, False]
    assert f["V2_above_ceiling_heavy_RE"].tolist() == [False, False, False, True, False, False, False, False]
    assert f["V3_zero_value"].tolist() == [False, False, False, False, True, False, False, False]
    assert f["V4_mass_unit_misparsed"].tolist() == [False, False, False, False, False, True, True, False]


def test_k1_ceiling_uses_absolute_value_and_keeps_known_large_values():
    df = pd.DataFrame({"K1_clean": [6.44e8, -7.2e7, 3.0e7, -2.2e7, 0.0, 5.0e7]})
    flags = b.k1_flags(df, RULES)
    assert flags["K1_above_ceiling"].tolist() == [True, True, False, False, False, False]


def test_removal_reason_text_lists_every_triggered_rule():
    flags = pd.DataFrame({"M1_above_ceiling_no_heavy_RE": [True, False], "M3_zero_value": [True, True]})
    texts = [b.reason_text(r, ["M1_above_ceiling_no_heavy_RE", "M3_zero_value"]) for _, r in flags.iterrows()]
    assert texts[0] == "v1.4 R10: M1+M3" and texts[1] == "v1.4 R10: M3"
    with pytest.raises(KeyError):
        b.reason_text(flags.iloc[0], ["unknown_rule"])


def test_removed_rows_lose_their_clean_value_but_keep_it_in_the_quarantine_copy():
    original = pd.DataFrame({"Ms_massMagnetization_clean": [257.0, 100.0], "exclusion_reason": [None, None], "v1_4_change": ["", ""]})
    removed = pd.Series([True, False])
    flagged = original.assign(exclusion_reason=["v1.4 R10: M1", None], v1_4_change=["R10_ms_mass_excluded", ""])
    quarantine = b.with_reason(original, flagged, removed)
    blanked = b.blank_clean_values(flagged, removed, "Ms_massMagnetization_clean")
    assert quarantine["Ms_massMagnetization_clean"].tolist() == [257.0] and quarantine["exclusion_reason"].tolist() == ["v1.4 R10: M1"]
    assert pd.isna(blanked.loc[0, "Ms_massMagnetization_clean"]) and blanked.loc[1, "Ms_massMagnetization_clean"] == 100.0
