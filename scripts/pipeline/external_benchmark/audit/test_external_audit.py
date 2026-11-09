"""Tests for the external-benchmark audit helpers and rules.  Run from this folder:  python -m pytest -q test_external_audit.py"""
from __future__ import annotations

import numpy as np
import pytest

from audit_common import (cluster_weights, composition_key, doi_set, fraction_vectors, metrics, nearest_tv_distance, paper_clusters, weighted_median_ae,
                          weighted_metrics)
from audit_external import a6_categories, is_impossible_ionic, is_mixed_scale


def test_doi_set_strips_url_prefix_brackets_and_splits_lists():
    assert doi_set("[10.1016/J.JMMM.2016.09.102]") == {"10.1016/j.jmmm.2016.09.102"}
    assert doi_set("https://doi.org/10.1063/1.1656420") == {"10.1063/1.1656420"}
    assert doi_set("[10.1/a, 10.2/b]") == {"10.1/a", "10.2/b"}


def test_doi_set_returns_empty_for_book_reference_and_nan():
    assert doi_set("[Magnetism and Magnetic Materials (J. M. D. Coey)]") == frozenset()
    assert doi_set(float("nan")) == frozenset()


def test_composition_key_is_spelling_independent():
    assert composition_key("Ca0.33La0.57Mn1O3") == composition_key("Ca33La57Mn100O300")
    assert composition_key("Fe2B0.7C0.3") == composition_key("Fe20B7C3")
    assert composition_key("Fe2B") != composition_key("FeB")
    assert composition_key("not a formula") is None


def test_paper_clusters_links_records_sharing_any_doi_transitively():
    dois = [frozenset({"a"}), frozenset({"a", "b"}), frozenset({"b"}), frozenset({"c"}), frozenset(), frozenset()]
    refs = ["", "", "", "", "book X", "book X"]
    c = paper_clusters(dois, refs)
    assert c[0] == c[1] == c[2]
    assert c[3] != c[0]
    assert c[4] == c[5] != c[3]


def test_paper_cluster_labels_do_not_depend_on_doi_iteration_order():
    dois = [frozenset({"x", "y"}), frozenset({"z"}), frozenset({"y", "w"}), frozenset({"w"})]
    reordered = [frozenset(sorted(s, reverse=True)) for s in dois]
    a, b = paper_clusters(dois, [""] * 4), paper_clusters(reordered, [""] * 4)
    np.testing.assert_array_equal(a, b)
    np.testing.assert_array_equal(a, [0, 1, 0, 0])      # numbered by first appearance


def test_nearest_tv_distance_matches_brute_force():
    rng = np.random.default_rng(0)
    q = rng.dirichlet(np.ones(6), size=7) * (rng.random((7, 6)) > 0.4)
    q[:, 0] += 0.01
    q = q / q.sum(axis=1, keepdims=True)
    r = rng.dirichlet(np.ones(6), size=50) * (rng.random((50, 6)) > 0.4)
    r[:, 1] += 0.01
    r = r / r.sum(axis=1, keepdims=True)
    brute = 0.5 * np.abs(q[:, None, :] - r[None, :, :]).sum(axis=2)
    near, mean3, idx = nearest_tv_distance(q, r, k=3, chunk=3)
    np.testing.assert_allclose(near, brute.min(axis=1), atol=1e-12)
    np.testing.assert_allclose(mean3, np.sort(brute, axis=1)[:, :3].mean(axis=1), atol=1e-12)
    np.testing.assert_array_equal(idx, brute.argmin(axis=1))


def test_tv_distance_is_zero_for_same_composition_and_one_for_disjoint_elements():
    els = ["Fe", "Ni", "Co", "B"]
    q = fraction_vectors(["Fe2Ni2"], els)
    r = fraction_vectors(["FeNi", "Co3B"], els)
    near, _, idx = nearest_tv_distance(q, r)
    assert near[0] == pytest.approx(0.0) and idx[0] == 0
    far, _, _ = nearest_tv_distance(q, r[1:])
    assert far[0] == pytest.approx(1.0)


def test_weighted_bootstrap_equals_explicit_cluster_resampling():
    rng = np.random.default_rng(1)
    clusters = np.repeat(np.arange(12), rng.integers(1, 5, 12))
    y = rng.normal(300, 100, len(clusters))
    pred = y + rng.normal(0, 40, len(clusters))
    lo, hi = pred - 60, pred + 60
    codes, w = cluster_weights(clusters, 5, seed=3)
    boot = weighted_metrics(codes, w, y, pred, lo, hi)
    med = weighted_median_ae(codes, w, np.abs(pred - y))
    for b in range(5):
        rows = np.concatenate([np.repeat(np.flatnonzero(codes == c), int(w[b, c])) for c in range(w.shape[1])])
        ref = metrics(y[rows], pred[rows], lo[rows], hi[rows])
        for key in ("mae_k", "r2", "coverage", "mean_width_k", "share_within_50k"):
            assert boot[key][b] == pytest.approx(ref[key])
        errs = np.sort(np.abs(pred - y)[rows])
        assert med[b] == pytest.approx(errs[(len(errs) - 1) // 2])


def test_mixed_scale_flags_partly_scaled_glass_formula_but_not_valid_dilute_alloys():
    assert is_mixed_scale("Zr7Fe6230(Ni1335B2)2")          # (Fe0.7Ni0.3)89Zr7B4 with Fe/Ni scaled x100, Zr/B not
    assert not is_mixed_scale("Fe13Pd987")                  # 1.3% Fe in Pd: valid dilute alloy
    assert not is_mixed_scale("Zr11Fe86B3")


def test_impossible_ionic_flags_non_perovskite_manganite_but_not_real_ones():
    assert is_impossible_ionic("Ba2La8MnFeO30")             # A10 B2 O30
    assert not is_impossible_ionic("Ca3La7Mn10O30")         # La0.7Ca0.3MnO3
    assert not is_impossible_ionic("CuCr2Se3Br")            # other anion former present -> not judged


def test_a6_categories_ignore_synthesis_under_pressure_but_flag_measurement_under_pressure():
    assert "pressure" not in a6_categories("Ferromagnetism of (ScCa)Co2 Laves phase compound synthesized under high pressure")
    assert "pressure" in a6_categories("Pressure Dependence of the Curie Temperature of Ferromagnetic Laves Phase Alloys")
    assert a6_categories("Structural and magnetocaloric effect of Ln0.67Sr0.33MnO3 nanoparticles") == ["nano"]
