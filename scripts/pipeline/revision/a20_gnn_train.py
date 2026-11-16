"""A20 step 2 (pimm-discovery env, GPU): end-to-end graph-network check for the Curie temperature. Specification: final/revision/PLAN.md, entry A20.

Callers: a20_gnn_analysis.py reads the prediction files written here. Input: outputs/a20_gnn/matched_curie_inputs.parquet (a20_gnn_prepare.py) and
outputs/a6/mp_structures.json.gz. Output: outputs/a20_gnn/preds/{variant}__s{split}__seed{seed}.parquet with columns material_id, y_pred, best_epoch, val_mae.

Variants (same head, same fixed settings, no tuning): mlp_t1 (Tier 1 predictors only), gnn_t1 (pretrained CHGNet crystal feature, trainable, + Tier 1),
gnn_only (CHGNet crystal feature alone). Implementation details fixed before the run: a LayerNorm on the 64-d crystal feature; head Linear(d,256)-SiLU-
Dropout(0.1)-Linear(256,128)-SiLU-Linear(128,1); records are batched BY STRUCTURE (32 structures per step, every training record of those structures), which is
equivalent in expectation to record batches because the 4,602 records map to 521 structures and formula-grouped splits keep a structure inside one split;
standardised Tier 1 values clipped to [-10, 10].
Resumable: finished (variant, split, seed) files are skipped; --max-minutes stops cleanly between runs.
Run (repository root, foreground chunks):
  /c/Users/USER/anaconda3/envs/pimm-discovery/python.exe -X utf8 final/revision/scripts/a20_gnn_train.py --max-minutes 9
"""
from __future__ import annotations

import argparse
import copy
import gzip
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "final/revision/outputs/a20_gnn"
PREDS = OUT / "preds"
VARIANTS = {"mlp_t1": (False, True), "gnn_t1": (True, True), "gnn_only": (True, False)}   # (uses structure, uses Tier 1)
META = {"material_id", "reduced_formula", "mp_id", "y"}
STRUCT_PER_STEP, LR_HEAD, LR_CHG, WEIGHT_DECAY, HUBER_DELTA, EVAL_CHUNK = 32, 1e-3, 1e-4, 1e-4, 1.0, 64


class Net(nn.Module):
    def __init__(self, uses_struct: bool, uses_tab: bool, n_tab: int) -> None:
        super().__init__()
        from chgnet.model import CHGNet
        self.uses_struct, self.uses_tab = uses_struct, uses_tab
        self.chg = CHGNet.load(verbose=False) if uses_struct else None
        self.norm = nn.LayerNorm(64) if uses_struct else None
        d = (64 if uses_struct else 0) + (n_tab if uses_tab else 0)
        self.head = nn.Sequential(nn.Linear(d, 256), nn.SiLU(), nn.Dropout(0.1), nn.Linear(256, 128), nn.SiLU(), nn.Linear(128, 1))

    def forward(self, graphs: list, rec_to_struct: torch.Tensor, xtab: torch.Tensor) -> torch.Tensor:
        parts = []
        if self.uses_struct:
            fea = self.norm(self.chg(graphs, task="e", return_crystal_feas=True)["crystal_fea"])
            parts.append(fea[rec_to_struct])
        if self.uses_tab:
            parts.append(xtab)
        return self.head(torch.cat(parts, dim=1)).squeeze(1)


def load_inputs() -> tuple[pd.DataFrame, list[str]]:
    data = pd.read_parquet(OUT / "matched_curie_inputs.parquet")
    tab = [c for c in data.columns if c not in META and not c.startswith("split_")]
    return data, tab


def build_graphs(mp_ids: list[str], device: str) -> dict:
    from chgnet.model import CHGNet
    from pymatgen.core import Structure
    with gzip.open(ROOT / "final/revision/outputs/a6/mp_structures.json.gz", "rt", encoding="utf-8") as f:
        structures = json.load(f)
    conv = CHGNet.load(verbose=False).graph_converter
    return {m: conv(Structure.from_dict(structures[m])).to(device) for m in mp_ids}


def group_by_structure(mp: np.ndarray, rows: np.ndarray) -> dict[str, np.ndarray]:
    out: dict[str, list[int]] = {}
    for i in rows:
        out.setdefault(mp[i], []).append(i)
    return {k: np.asarray(v) for k, v in out.items()}


def make_batch(structs: list[str], groups: dict, graphs: dict, xt: torch.Tensor, device: str):
    rows = np.concatenate([groups[m] for m in structs])
    rec_to_struct = torch.as_tensor(np.concatenate([np.full(len(groups[m]), k) for k, m in enumerate(structs)]), device=device)
    return rows, [graphs[m] for m in structs], rec_to_struct, xt[torch.as_tensor(rows, device=device)]


@torch.no_grad()
def predict(net: Net, groups: dict, graphs: dict, xt: torch.Tensor, device: str) -> tuple[np.ndarray, np.ndarray]:
    net.eval()
    keys, rows_all, pred_all = list(groups), [], []
    for i in range(0, len(keys), EVAL_CHUNK):
        rows, g, r2s, x = make_batch(keys[i:i + EVAL_CHUNK], groups, graphs, xt, device)
        rows_all.append(rows)
        pred_all.append(net(g, r2s, x).float().cpu().numpy())
    return np.concatenate(rows_all), np.concatenate(pred_all)


def run_one(variant: str, split: str, seed: int, data: pd.DataFrame, tab: list[str], graphs: dict, device: str, max_epochs: int, patience: int) -> pd.DataFrame:
    uses_struct, uses_tab = VARIANTS[variant]
    torch.manual_seed(seed * 1000 + int(split))
    rng = np.random.default_rng(seed * 1000 + int(split))
    lab = data[f"split_{split}"].to_numpy()
    tr, va, te = (np.flatnonzero(lab == s) for s in ("train", "validation", "test"))
    X = data[tab].to_numpy(float)
    X = np.where(np.isnan(X), np.nanmedian(X[tr], axis=0), X)
    X = np.clip((X - X[tr].mean(0)) / (X[tr].std(0) + 1e-8), -10, 10)
    y = data["y"].to_numpy(float)
    ym, ys = y[tr].mean(), y[tr].std()
    yz = torch.as_tensor((y - ym) / ys, dtype=torch.float32, device=device)
    xt = torch.as_tensor(X, dtype=torch.float32, device=device)
    mp = data["mp_id"].to_numpy()
    g_tr, g_va, g_te = (group_by_structure(mp, r) for r in (tr, va, te))
    net = Net(uses_struct, uses_tab, len(tab)).to(device)
    param_groups = [{"params": net.head.parameters(), "lr": LR_HEAD}]
    if uses_struct:
        param_groups += [{"params": net.chg.parameters(), "lr": LR_CHG}, {"params": net.norm.parameters(), "lr": LR_HEAD}]
    opt = torch.optim.AdamW(param_groups, weight_decay=WEIGHT_DECAY)
    loss_fn = nn.HuberLoss(delta=HUBER_DELTA)
    best, best_state, best_epoch, keys = np.inf, None, 0, list(g_tr)
    for epoch in range(max_epochs):
        net.train()
        order = rng.permutation(len(keys))
        for i in range(0, len(order), STRUCT_PER_STEP):
            rows, g, r2s, x = make_batch([keys[k] for k in order[i:i + STRUCT_PER_STEP]], g_tr, graphs, xt, device)
            loss = loss_fn(net(g, r2s, x), yz[torch.as_tensor(rows, device=device)])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 5.0)
            opt.step()
        rows, pred = predict(net, g_va, graphs, xt, device)
        val_mae = float(np.abs(pred * ys + ym - y[rows]).mean())
        if val_mae < best - 1e-6:
            best, best_epoch, best_state = val_mae, epoch, copy.deepcopy(net.state_dict())
        elif epoch - best_epoch >= patience:
            break
    net.load_state_dict(best_state)
    rows, pred = predict(net, g_te, graphs, xt, device)
    return pd.DataFrame({"material_id": data["material_id"].to_numpy()[rows], "y_pred": pred * ys + ym, "best_epoch": best_epoch, "val_mae": best})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS))
    ap.add_argument("--splits", nargs="+", default=[str(i) for i in range(10)])
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--max-epochs", type=int, default=150)
    ap.add_argument("--patience", type=int, default=20)
    ap.add_argument("--max-minutes", type=float, default=9.0)
    a = ap.parse_args()
    PREDS.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    data, tab = load_inputs()
    graphs = build_graphs(sorted(data["mp_id"].unique()), device)
    t0, done, todo = time.perf_counter(), 0, 0
    for seed in a.seeds:
        for split in a.splits:
            for variant in a.variants:
                f = PREDS / f"{variant}__s{split}__seed{seed}.parquet"
                if f.exists():
                    continue
                todo += 1
                if (time.perf_counter() - t0) / 60 > a.max_minutes:
                    continue
                t1 = time.perf_counter()
                res = run_one(variant, split, seed, data, tab, graphs, device, a.max_epochs, a.patience)
                res.to_parquet(f, index=False)
                done += 1
                te = data.set_index("material_id").loc[res["material_id"], "y"].to_numpy()
                print(f"{variant} split {split} seed {seed}: test MAE {np.abs(res.y_pred.to_numpy() - te).mean():.1f} K | val MAE {res.val_mae.iloc[0]:.1f} | "
                      f"best epoch {int(res.best_epoch.iloc[0])} | {time.perf_counter() - t1:.0f}s", flush=True)
    print(f"finished {done} runs this call; {todo - done} left")


if __name__ == "__main__":
    main()
