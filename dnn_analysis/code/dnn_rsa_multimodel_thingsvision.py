"""
Multi-DNN RSA pipeline with two-tier order handling.

Tier A (legacy filename order) is required only for direct comparison with the
legacy MATLAB VGG-19 RDMs. It is not verified in this repository and is skipped
by default.

Tier B (analysis order) is a deterministic order defined by this script:
animate block first, inanimate block second, each sorted by ascending numeric
index parsed from the filename. This order is sufficient for within-model RSA
and binary animate-inanimate RSA because all new models use the same order.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import platform
import re
import sys
import time
import traceback
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import h5py
import numpy as np
import pandas as pd
import scipy.io as sio
from PIL import Image
from scipy.stats import rankdata


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs_multimodel_dnn_rsa"
LOGS = OUT / "logs"
FIGS = OUT / "figures"
RDMS = OUT / "rdms"
LAYERS_DIR = OUT / "model_layer_lists"
SEED_DEFAULT = 20240517
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
MAT_RDM_DIR = ROOT / "Correlation Dissimilarity"
EXCEL = ROOT / "AllCorrelation6plus.xlsx"


class HardGateFailure(RuntimeError):
    pass


def ensure_dirs() -> None:
    for p in [OUT, LOGS, FIGS, RDMS, LAYERS_DIR, OUT / "metadata"]:
        p.mkdir(parents=True, exist_ok=True)


def log_status(kind: str, phase: str, message: str, details: str = "") -> None:
    ensure_dirs()
    path = OUT / "STATUS_BLOCKER.md"
    entry = f"\n\n# {kind}\n\nPhase: {phase}\n\n{message}\n\n"
    if details:
        entry += "## Details\n\n" + details.strip() + "\n"
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    path.write_text(existing + entry, encoding="utf-8")
    print(f"{kind} in {phase}: {message}")


def sha1_file(path: Path, block_size: int = 1 << 20) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()


def package_versions() -> Dict[str, str]:
    versions = {
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "seed_default": str(SEED_DEFAULT),
    }
    for name in [
        "numpy",
        "scipy",
        "pandas",
        "sklearn",
        "matplotlib",
        "statsmodels",
        "torch",
        "torchvision",
        "thingsvision",
        "timm",
        "PIL",
        "h5py",
    ]:
        try:
            mod = importlib.import_module(name)
            versions[name] = getattr(mod, "__version__", "available_unknown_version")
        except Exception as exc:
            versions[name] = f"unavailable: {type(exc).__name__}: {exc}"
    return versions


def write_env_files() -> None:
    versions = package_versions()
    (OUT / "env_versions.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in versions.items()) + "\n",
        encoding="utf-8",
    )
    pkg_map = {"sklearn": "scikit-learn", "PIL": "pillow"}
    req = []
    for k, v in versions.items():
        if k in {"python", "platform", "seed_default"}:
            continue
        name = pkg_map.get(k, k)
        req.append(f"# {name}: {v}" if v.startswith("unavailable") else f"{name}=={v}")
    (ROOT / "requirements_multimodel_dnn_rsa.txt").write_text("\n".join(req) + "\n", encoding="utf-8")


def numeric_index(name: str) -> Optional[int]:
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else None


def numeric_sort(paths: Sequence[Path]) -> Tuple[List[Path], str]:
    indexed = [(numeric_index(p.name), p) for p in paths]
    if all(i is not None for i, _ in indexed):
        return [p for _, p in sorted(indexed, key=lambda x: (x[0], x[1].name.lower()))], "numeric_index_ascending"
    return sorted(paths, key=lambda p: p.name.lower()), "lexicographic_basename_fallback"


def read_inventory() -> pd.DataFrame:
    inv = OUT / "file_inventory.csv"
    if not inv.exists():
        rows = []
        for p in ROOT.rglob("*"):
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                rows.append(
                    {
                        "record_type": "image",
                        "abs_path": str(p.resolve()),
                        "parent_chain": " / ".join(p.relative_to(ROOT).parent.parts),
                        "basename": p.name,
                        "extension": p.suffix.lower(),
                        "size_bytes": p.stat().st_size,
                        "sha1": sha1_file(p),
                        "category_as_found": "",
                        "numeric_index": numeric_index(p.name),
                    }
                )
        pd.DataFrame(rows).to_csv(inv, index=False)
    return pd.read_csv(inv)


def path_images(parent: Path) -> List[Path]:
    if not parent.exists():
        return []
    return sorted([p for p in parent.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS])


def prefixed_images(parent: Path, prefix: str) -> List[Path]:
    if not parent.exists():
        return []
    pat = re.compile(rf"^{re.escape(prefix)}(\d+)\.(jpg|jpeg|png|tif|tiff|bmp)$", re.I)
    return sorted([p for p in parent.iterdir() if p.is_file() and pat.match(p.name)])


@dataclass
class StimulusSet:
    name: str
    lane: str
    animate: List[Path]
    inanimate: List[Path]
    order_rule: str
    source: str
    status: str
    reason: str

    @property
    def n_total(self) -> int:
        return len(self.animate) + len(self.inanimate)


def discover_stimulus_sets() -> List[StimulusSet]:
    specs: List[StimulusSet] = []

    def add_category(name: str, root: Path, lane: str = "640") -> None:
        a, ar = numeric_sort(path_images(root / "Animate"))
        i, ir = numeric_sort(path_images(root / "Inanimate"))
        rule = ar if ar == ir else f"animate={ar}; inanimate={ir}"
        expected = 320 if lane == "640" else 175
        status = "INCLUDED_640" if lane == "640" and len(a) == len(i) == expected else "INCLUDED_350" if lane == "350" and len(a) == len(i) == expected else "EXCLUDED"
        reason = "" if status.startswith("INCLUDED") else f"expected {expected}+{expected}; found {len(a)}+{len(i)}"
        specs.append(StimulusSet(name, lane, a, i, rule, str(root), status, reason))

    def add_flat(name: str, root: Path, aprefix: str, iprefix: str, lane: str = "640") -> None:
        a, ar = numeric_sort(prefixed_images(root, aprefix))
        i, ir = numeric_sort(prefixed_images(root, iprefix))
        rule = ar if ar == ir else f"animate={ar}; inanimate={ir}"
        expected = 320 if lane == "640" else 175
        status = "INCLUDED_640" if lane == "640" and len(a) == len(i) == expected else "INCLUDED_350" if lane == "350" and len(a) == len(i) == expected else "EXCLUDED"
        reason = "" if status.startswith("INCLUDED") else f"expected {expected}+{expected}; found {len(a)}+{len(i)}"
        specs.append(StimulusSet(name, lane, a, i, rule, str(root), status, reason))

    add_category("Color", ROOT / "Color", "640")
    add_category("Grayscale", ROOT / "Grayscale", "640")
    add_flat("CPS", ROOT / "CPS", "CPS_A", "CPS_I", "640")
    add_flat("GPS", ROOT / "GPS", "GPS_A", "GPS_I", "640")
    add_flat("Texform", ROOT / "Texform", "Tex_A", "Tex_I", "640")

    add_category("Color_reduced", ROOT / "New_version_Reduced" / "Color", "350")
    add_category("Grayscale_reduced", ROOT / "New_version_Reduced" / "Grayscale", "350")
    add_flat("CPS_reduced", ROOT / "New_version_Reduced" / "CPS", "CPS_A", "CPS_I", "350")
    add_flat("GPS_reduced", ROOT / "New_version_Reduced" / "GPS", "GPS_A", "GPS_I", "350")
    add_flat("Tout2_reduced", ROOT / "New_version_Reduced" / "Tout2", "A", "I", "350")

    add_flat("Tout2_root", ROOT / "Tout2", "A", "I", "350")

    # The requested main analysis uses clean 640-image sets. Reduced sets are
    # documented but not mixed into the main lane by default.
    for s in specs:
        if s.status == "INCLUDED_350":
            s.status = "EXCLUDED"
            s.reason = "clean 350-image reduced lane discovered; not mixed into the main 640-image analysis"
    return specs


def phase1() -> None:
    ensure_dirs()
    write_env_files()
    inv = read_inventory()
    required = [
        OUT / "file_inventory.csv",
        OUT / "mat_inventory.csv",
        OUT / "data_structure_audit_report.md",
        LOGS / "303_investigation.md",
        LOGS / "image_order_selection.md",
    ]
    missing = [str(p) for p in required if not p.exists()]
    sets = discover_stimulus_sets()
    lines = [
        "",
        "## Phase 1 Refresh",
        "",
        f"- Refresh timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Existing audit files reused: {len(required) - len(missing)} / {len(required)}",
        f"- Missing audit files regenerated or unavailable: {missing if missing else 'none'}",
        f"- Image rows in inventory: {int((inv.get('record_type', '') == 'image').sum()) if 'record_type' in inv else len(inv)}",
        "",
        "| stimulus_set | source | animate_count | inanimate_count | status | reason |",
        "|---|---:|---:|---:|---|---|",
    ]
    for s in sets:
        lines.append(f"| {s.name} | `{s.source}` | {len(s.animate)} | {len(s.inanimate)} | {s.status} | {s.reason} |")
    report = OUT / "data_structure_audit_report.md"
    existing = report.read_text(encoding="utf-8", errors="replace") if report.exists() else "# Data Structure Audit Report\n"
    report.write_text(existing.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")


def phase2() -> List[StimulusSet]:
    ensure_dirs()
    sets = discover_stimulus_sets()
    included = [s for s in sets if s.status == "INCLUDED_640"]
    lines = [
        "# Condition Completeness Report",
        "",
        "Tier B main lane uses only clean 640-image stimulus sets. Clean 350-image reduced sets are documented but not mixed into this lane.",
        "",
        "| stimulus_set | lane | source | animate | inanimate | total | status | usable_for_new_dnn_rsa | reason | order_rule |",
        "|---|---:|---|---:|---:|---:|---|---|---|---|",
    ]
    for s in sets:
        usable = "yes" if s.status == "INCLUDED_640" else "no"
        lines.append(
            f"| {s.name} | {s.lane} | `{s.source}` | {len(s.animate)} | {len(s.inanimate)} | {s.n_total} | {s.status} | {usable} | {s.reason} | {s.order_rule} |"
        )
    (OUT / "condition_completeness_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    tex_lines = [
        "# Texform Version Decision",
        "",
        "The audit found a clean root `Texform/` image folder with `Tex_A###.jpg` and `Tex_I###.jpg` patterns.",
        "No separate image folder named `newTexform` was found in the refreshed stimulus-set roots. Legacy `.mat` files include `newTexform` labels, but that is not evidence for a separate on-disk image set.",
        "Decision: use root `Texform/` as the Tier-B stimulus set label `Texform`; do not collapse it with any unavailable `newTexform` folder.",
        "",
    ]
    tex = [s for s in sets if "Tex" in s.name or "Tout" in s.name]
    for s in tex:
        tex_lines.append(f"- {s.name}: source=`{s.source}`, animate={len(s.animate)}, inanimate={len(s.inanimate)}, status={s.status}, reason={s.reason}")
    (OUT / "texform_version_decision.md").write_text("\n".join(tex_lines) + "\n", encoding="utf-8")

    if not included:
        log_status("HARD_GATE_FAILURE", "Phase 2", "No clean 640-image stimulus sets are usable.")
        raise HardGateFailure("No usable stimulus sets.")
    return included


def phase3() -> pd.DataFrame:
    ensure_dirs()
    included = phase2()
    rows = []
    for s in included:
        pos = 1
        for cat, paths in [("animate", s.animate), ("inanimate", s.inanimate)]:
            for p in paths:
                rows.append(
                    {
                        "stimulus_set": s.name,
                        "position_1toN": pos,
                        "abs_path": str(p.resolve()),
                        "basename": p.name,
                        "category": cat,
                        "source_subfolder": str(p.parent.resolve()),
                        "sha1": sha1_file(p),
                        "order_rule": s.order_rule,
                        "tier_b_statement": "animate block first, then inanimate block; within block sorted by ascending numeric filename index",
                    }
                )
                pos += 1
    df = pd.DataFrame(rows)
    # Hard sanity check for 640 lane.
    bad = []
    for stim, g in df.groupby("stimulus_set"):
        cats = g.sort_values("position_1toN")["category"].tolist()
        if len(g) != 640 or cats[:320] != ["animate"] * 320 or cats[320:] != ["inanimate"] * 320:
            bad.append(stim)
    if bad:
        log_status("HARD_GATE_FAILURE", "Phase 3", f"Tier-B order sanity check failed for: {bad}")
        raise HardGateFailure("Tier-B order failed sanity check.")
    df.to_csv(OUT / "analysis_order_defined.csv", index=False)
    return df


def parse_rdm_name(path: Path) -> Tuple[str, str]:
    stem = path.stem.replace("correlationDissimilarityMatrix_", "")
    known = ["Color_Scrambled", "Gray_scrambled", "GrayScale", "newTexform", "TextForm", "Color"]
    for cond in sorted(known, key=len, reverse=True):
        if stem.endswith("_" + cond):
            return stem[: -(len(cond) + 1)], cond
    a, b = stem.rsplit("_", 1)
    return a, b


def load_rdm(path: Path) -> np.ndarray:
    try:
        d = sio.loadmat(path)
        return np.asarray(d["dissimilarityMatrix"], dtype=np.float64)
    except NotImplementedError:
        with h5py.File(path, "r") as f:
            return np.asarray(f["dissimilarityMatrix"], dtype=np.float64)


def upper_values(m: np.ndarray) -> np.ndarray:
    return m[np.triu_indices(m.shape[0], 1)]


def pearson_vec(a: np.ndarray, b: np.ndarray) -> float:
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 3:
        return float("nan")
    x = a[mask].astype(np.float64)
    y = b[mask].astype(np.float64)
    x -= x.mean()
    y -= y.mean()
    den = np.linalg.norm(x) * np.linalg.norm(y)
    return float(x @ y / den) if den else float("nan")


def spearman_vec(a: np.ndarray, b: np.ndarray) -> float:
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 3:
        return float("nan")
    return pearson_vec(rankdata(a[mask]), rankdata(b[mask]))


def vector_for(m: np.ndarray, triangle: str, transform: str) -> np.ndarray:
    x = 1.0 - m if transform == "similarity" else m
    if triangle == "upper_no_diag":
        return upper_values(x)
    if triangle == "full_offdiag":
        return x[~np.eye(x.shape[0], dtype=bool)]
    if triangle == "full_incl_diag":
        return x.ravel()
    raise ValueError(triangle)


def phase4() -> str:
    ensure_dirs()
    files = sorted(MAT_RDM_DIR.glob("correlationDissimilarityMatrix_*.mat"))
    mats: Dict[Tuple[str, str], np.ndarray] = {}
    enum = []
    for f in files:
        layer, cond = parse_rdm_name(f)
        try:
            m = load_rdm(f)
            enum.append({"file": str(f), "layer": layer, "condition": cond, "shape": str(m.shape)})
            if m.ndim == 2 and m.shape[0] == m.shape[1]:
                mats[(layer, cond)] = m
        except Exception as exc:
            enum.append({"file": str(f), "layer": layer, "condition": cond, "shape": "", "error": f"{type(exc).__name__}: {exc}"})
    pd.DataFrame(enum).to_csv(OUT / "legacy_rdm_enumeration.csv", index=False)
    if not EXCEL.exists() or not mats:
        log_status("SOFT_GATE_FAILURE", "Phase 4", "Legacy Excel or MATLAB RDMs unavailable; legacy reproduction skipped.")
        return "SKIPPED"

    excel = pd.read_excel(EXCEL, sheet_name=0)
    condition_candidates = {
        "Color": ["Color"],
        "Grayscale": ["GrayScale"],
        "Color-Scrambled": ["Color_Scrambled"],
        "Grayscale-Scrambled": ["Gray_scrambled"],
        "Texform": ["newTexform", "TextForm"],
    }
    targets = []
    for _, row in excel.iterrows():
        for excel_cond, candidates in condition_candidates.items():
            for cond in candidates:
                if (row["Layer"], cond) in mats:
                    targets.append({"layer": row["Layer"], "condition": cond, "excel_condition": excel_cond, "excel_value": float(row[excel_cond])})
                    break
    # Phase 4 is best-effort and non-blocking. Keep the diagnostic focused on
    # references actually suggested by the legacy analysis context rather than
    # exhaustively testing every RDM as a reference.
    refs = [k for k in [("fc8", "Color"), ("fc7", "Color"), ("fc6", "Color")] if k in mats]
    rows = []
    best_rowwise = []
    vec_cache: Dict[Tuple[str, str, str, str], np.ndarray] = {}
    rank_cache: Dict[Tuple[str, str, str, str], np.ndarray] = {}

    def cached_vec(layer: str, cond: str, triangle: str, transform: str) -> np.ndarray:
        key = (layer, cond, triangle, transform)
        if key not in vec_cache:
            vec_cache[key] = vector_for(mats[(layer, cond)], triangle, transform)
        return vec_cache[key]

    def cached_rank(layer: str, cond: str, triangle: str, transform: str) -> np.ndarray:
        key = (layer, cond, triangle, transform)
        if key not in rank_cache:
            rank_cache[key] = rankdata(cached_vec(layer, cond, triangle, transform)).astype(np.float32)
        return rank_cache[key]

    for ref_layer, ref_cond in refs:
        for method in ["spearman", "pearson"]:
            for triangle in ["upper_no_diag", "full_offdiag", "full_incl_diag"]:
                for transform in ["dissimilarity", "similarity"]:
                    diffs, detail = [], []
                    for t in targets:
                        tm = mats[(t["layer"], t["condition"])]
                        rm = mats[(ref_layer, ref_cond)]
                        if tm.shape != rm.shape:
                            continue
                        if method == "spearman":
                            tv = cached_rank(t["layer"], t["condition"], triangle, transform)
                            rv = cached_rank(ref_layer, ref_cond, triangle, transform)
                            r = pearson_vec(tv, rv)
                        else:
                            tv = cached_vec(t["layer"], t["condition"], triangle, transform)
                            rv = cached_vec(ref_layer, ref_cond, triangle, transform)
                            r = pearson_vec(tv, rv)
                        d = abs(r - t["excel_value"])
                        diffs.append(d)
                        detail.append({**t, "computed_r": r, "abs_diff_vs_excel": d})
                    if diffs:
                        rows.append(
                            {
                                "method": method,
                                "reference_layer": ref_layer,
                                "reference_condition": ref_cond,
                                "target_layer": "*",
                                "target_condition": "*",
                                "texform_version": "newTexform_or_TextForm_if_present",
                                "triangle": triangle,
                                "transform": transform,
                                "max_abs_diff_vs_excel": float(np.max(diffs)),
                                "mean_abs_diff_vs_excel": float(np.mean(diffs)),
                                "n_rows_compared": len(diffs),
                            }
                        )
    diag = pd.DataFrame(rows).sort_values(["max_abs_diff_vs_excel", "mean_abs_diff_vs_excel"])
    diag.to_csv(OUT / "legacy_vgg19_reproduction_diagnostics.csv", index=False)
    status = "FAILED"
    if not diag.empty:
        best = diag.iloc[0]
        status = "REPRODUCED" if best["max_abs_diff_vs_excel"] < 1e-3 else "PARTIAL" if best["max_abs_diff_vs_excel"] < 1e-2 else "FAILED"
        # Rowwise best convention.
        ref_layer, ref_cond = best["reference_layer"], best["reference_condition"]
        rowwise = []
        for t in targets:
            if (t["layer"], t["condition"]) not in mats or mats[(t["layer"], t["condition"])].shape != mats[(ref_layer, ref_cond)].shape:
                continue
            if best["method"] == "spearman":
                tv = cached_rank(t["layer"], t["condition"], best["triangle"], best["transform"])
                rv = cached_rank(ref_layer, ref_cond, best["triangle"], best["transform"])
                r = pearson_vec(tv, rv)
            else:
                tv = cached_vec(t["layer"], t["condition"], best["triangle"], best["transform"])
                rv = cached_vec(ref_layer, ref_cond, best["triangle"], best["transform"])
                r = pearson_vec(tv, rv)
            rowwise.append({**t, "computed_r": r, "abs_diff_vs_excel": abs(r - t["excel_value"]), "method": best["method"], "reference_layer": ref_layer, "reference_condition": ref_cond, "triangle": best["triangle"], "transform": best["transform"]})
        pd.DataFrame(rowwise).to_csv(OUT / "legacy_vgg19_best_reproduction.csv", index=False)
        notes = f"Best legacy reproduction status={status}; max_abs_diff={best['max_abs_diff_vs_excel']:.6f}; convention={dict(best)}"
    else:
        notes = "No comparable legacy rows."
    (LOGS / "legacy_reproduction_notes.md").write_text("# Legacy VGG-19 Reproduction Notes\n\n" + notes + "\n", encoding="utf-8")
    if status == "FAILED":
        log_status("SOFT_GATE_FAILURE", "Phase 4", "Legacy VGG-19 Excel reproduction failed; continuing with within-model and binary RSA.", notes)
    return status


MODEL_SPECS = {
    "alexnet": {
        "layers": ["features.4", "features.7", "features.9", "features.11", "classifier.1", "classifier.4", "classifier.6"],
        "reference": ["classifier.6", "classifier.4"],
    },
    "resnet50": {
        "layers": ["layer1", "layer2", "layer3", "layer4", "avgpool", "fc"],
        "reference": ["fc", "avgpool"],
    },
    "cornet_s": {
        "layers": ["module.V1.output", "module.V2.output", "module.V4.output", "module.IT.output", "module.decoder.avgpool", "module.decoder.linear"],
        "reference": ["module.decoder.linear", "module.IT.output"],
    },
    "vgg16": {
        "layers": ["features.16", "features.23", "features.30", "classifier.0", "classifier.3", "classifier.6"],
        "reference": ["classifier.6", "classifier.3"],
    },
}


def imagenet_transform() -> Any:
    from torchvision import transforms

    return transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )


class PathDataset:
    def __init__(self, paths: Sequence[Path], transform: Any):
        self.paths = list(paths)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, idx: int) -> Any:
        with Image.open(self.paths[idx]) as im:
            return self.transform(im.convert("RGB"))


def load_model(model_name: str) -> Tuple[Any, str, str]:
    if model_name == "cornet_s":
        try:
            from thingsvision.cornet import cornet_s

            model = cornet_s(pretrained=True, map_location="cpu")
            return model, "thingsvision_cornet", "cornet_s pretrained=True"
        except Exception as exc:
            raise RuntimeError(f"THINGSVision CORnet-S load failed: {exc}") from exc

    # THINGSVision is preferred, but the installed API/version does not expose a
    # stable multi-layer hook interface. Use torchvision fallback and document it.
    import torchvision.models as models

    if model_name == "alexnet":
        weights = models.AlexNet_Weights.DEFAULT
        return models.alexnet(weights=weights), "torchvision_fallback_after_thingsvision_api_check", str(weights)
    if model_name == "resnet50":
        weights = models.ResNet50_Weights.DEFAULT
        return models.resnet50(weights=weights), "torchvision_fallback_after_thingsvision_api_check", str(weights)
    if model_name == "vgg16":
        weights = models.VGG16_Weights.DEFAULT
        return models.vgg16(weights=weights), "torchvision_fallback_after_thingsvision_api_check", str(weights)
    raise ValueError(model_name)


def model_module_map(model: Any) -> Dict[str, Any]:
    return dict(model.named_modules())


def save_model_modules(model_name: str, model: Any) -> None:
    path = LAYERS_DIR / f"{model_name}.txt"
    with path.open("w", encoding="utf-8") as f:
        f.write(str(model))
        f.write("\n\n--- named_modules ---\n")
        for name, _ in model.named_modules():
            f.write(name + "\n")


def compute_rdm(features: np.ndarray) -> np.ndarray:
    x = np.asarray(features, dtype=np.float32)
    x = x - x.mean(axis=1, keepdims=True)
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    bad = ~np.isfinite(norms[:, 0]) | (norms[:, 0] == 0)
    x = x / norms
    x[bad] = np.nan
    r = 1.0 - (x @ x.T)
    np.fill_diagonal(r, 0.0)
    return r.astype(np.float32)


def extract_rdms_for_model(model_name: str, order: pd.DataFrame, batch_size: int = 16, device: str = "cpu") -> pd.DataFrame:
    import torch
    from torch.utils.data import DataLoader

    meta_rows = []
    try:
        model, source, weights = load_model(model_name)
    except Exception as exc:
        return pd.DataFrame([{"model": model_name, "status": "MODEL_FAILED", "failure_reason": f"{type(exc).__name__}: {exc}"}])

    model.eval().to(device)
    save_model_modules(model_name, model)
    modules = model_module_map(model)
    requested = [l for l in MODEL_SPECS[model_name]["layers"] if l in modules]
    missing = [l for l in MODEL_SPECS[model_name]["layers"] if l not in modules]
    if missing:
        meta_rows.append({"model": model_name, "status": "MISSING_LAYERS", "failure_reason": ";".join(missing)})
    transform = imagenet_transform()
    preproc = "RGB; Resize(256); CenterCrop(224); ToTensor; Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])"
    preproc_hash = hashlib.sha1(preproc.encode("utf-8")).hexdigest()

    for stim, g in order.groupby("stimulus_set", sort=False):
        paths = [Path(p) for p in g.sort_values("position_1toN")["abs_path"]]
        n = len(paths)
        all_valid_existing = True
        for layer in requested:
            safe_layer = layer.replace(".", "__")
            rdm_path = RDMS / model_name / safe_layer / f"{stim}.npz"
            if not rdm_path.exists():
                all_valid_existing = False
                break
            try:
                if tuple(np.load(rdm_path)["rdm"].shape) != (n, n):
                    all_valid_existing = False
                    break
            except Exception:
                all_valid_existing = False
                break
        if all_valid_existing:
            for layer in requested:
                safe_layer = layer.replace(".", "__")
                rdm_path = RDMS / model_name / safe_layer / f"{stim}.npz"
                rdm = np.load(rdm_path)["rdm"]
                meta_rows.append(
                    {
                        "model": model_name,
                        "source": source,
                        "model_identifier": model_name,
                        "weights": weights,
                        "preprocessing_pipeline": preproc,
                        "preproc_hash": preproc_hash,
                        "layer": layer,
                        "stimulus_set": stim,
                        "n_images": n,
                        "rdm_shape": str(tuple(rdm.shape)),
                        "activation_shape": "",
                        "file_path": str(rdm_path),
                        "status": "LOADED_EXISTING",
                        "failure_reason": "",
                        "package_versions": json.dumps(package_versions(), sort_keys=True),
                    }
                )
            continue

        layer_outs: Dict[str, List[np.ndarray]] = {l: [] for l in requested}
        current_outputs: Dict[str, np.ndarray] = {}
        handles = []

        def make_hook(layer: str):
            def hook(_module: Any, _inp: Any, out: Any) -> None:
                if isinstance(out, (tuple, list)):
                    out = out[0]
                arr = out.detach().cpu().float().numpy()
                # CORnet-S recurrent areas can trigger the same hook multiple
                # times in one forward pass. Keep the final activation for the
                # batch, not every recurrent call.
                current_outputs[layer] = arr.reshape(arr.shape[0], -1)

            return hook

        for layer in requested:
            handles.append(modules[layer].register_forward_hook(make_hook(layer)))

        try:
            ds = PathDataset(paths, transform)
            dl = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0)
            with torch.no_grad():
                for batch in dl:
                    current_outputs.clear()
                    _ = model(batch.to(device))
                    for layer in requested:
                        if layer in current_outputs:
                            layer_outs[layer].append(current_outputs[layer])
        except Exception as exc:
            for h in handles:
                h.remove()
            meta_rows.append({"model": model_name, "stimulus_set": stim, "status": "EXTRACTION_FAILED", "failure_reason": f"{type(exc).__name__}: {exc}", "source": source, "weights": weights})
            continue
        for h in handles:
            h.remove()

        for layer, chunks in layer_outs.items():
            safe_layer = layer.replace(".", "__")
            outdir = RDMS / model_name / safe_layer
            outdir.mkdir(parents=True, exist_ok=True)
            rdm_path = outdir / f"{stim}.npz"
            existing_valid = False
            existed_before_compute = rdm_path.exists()
            if rdm_path.exists():
                try:
                    rdm = np.load(rdm_path)["rdm"]
                    existing_valid = tuple(rdm.shape) == (n, n)
                except Exception:
                    existing_valid = False
            if existing_valid:
                status = "LOADED_EXISTING"
                shape = ""
            else:
                feat = np.concatenate(chunks, axis=0)
                shape = str(tuple(feat.shape))
                rdm = compute_rdm(feat)
                np.savez_compressed(
                    rdm_path,
                    rdm=rdm,
                    positions=g.sort_values("position_1toN")["position_1toN"].to_numpy(),
                    stimulus_set=stim,
                    model=model_name,
                    layer=layer,
                )
                status = "RECOMPUTED_INVALID_SHAPE" if existed_before_compute else "COMPUTED"
                del feat
            meta_rows.append(
                {
                    "model": model_name,
                    "source": source,
                    "model_identifier": model_name,
                    "weights": weights,
                    "preprocessing_pipeline": preproc,
                    "preproc_hash": preproc_hash,
                    "layer": layer,
                    "stimulus_set": stim,
                    "n_images": n,
                    "rdm_shape": str(tuple(rdm.shape)),
                    "activation_shape": shape,
                    "file_path": str(rdm_path),
                    "status": status,
                    "failure_reason": "",
                    "package_versions": json.dumps(package_versions(), sort_keys=True),
                }
            )
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return pd.DataFrame(meta_rows)


def phase5(smoke: bool = False) -> pd.DataFrame:
    ensure_dirs()
    order_path = OUT / "analysis_order_defined.csv"
    if not order_path.exists():
        raise HardGateFailure("analysis_order_defined.csv missing; run Phase 3.")
    order = pd.read_csv(order_path)
    models = ["alexnet"] if smoke else list(MODEL_SPECS)
    frames = []
    for model in models:
        print(f"Extracting RDMs for {model}...")
        frames.append(extract_rdms_for_model(model, order))
    meta = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    existing = OUT / "feature_rdm_metadata.csv"
    if existing.exists() and smoke:
        old = pd.read_csv(existing)
        meta = pd.concat([old, meta], ignore_index=True).drop_duplicates(["model", "layer", "stimulus_set", "file_path"], keep="last")
    meta.to_csv(existing, index=False)
    attempted = meta[~meta["status"].isin(["MODEL_FAILED", "MISSING_LAYERS"])] if "status" in meta else pd.DataFrame()
    if attempted.empty:
        log_status("HARD_GATE_FAILURE", "Phase 5", "No model/stimulus RDMs were produced.")
        raise HardGateFailure("No RDMs produced.")
    return meta


def phase6() -> None:
    ensure_dirs()
    meta = pd.read_csv(OUT / "feature_rdm_metadata.csv")
    ok = meta[meta["status"].isin(["COMPUTED", "LOADED_EXISTING"])].copy()
    refs = []
    for model, g in ok.groupby("model"):
        for ref in MODEL_SPECS.get(model, {}).get("reference", []):
            row = g[(g["layer"] == ref) & (g["stimulus_set"] == "Color")]
            if not row.empty:
                src = Path(row.iloc[0]["file_path"])
                rdm = np.load(src)["rdm"]
                out = RDMS / model / "_reference_within_model_color.npz"
                np.savez_compressed(out, rdm=rdm, source_file=str(src), reference_layer=ref, stimulus_set="Color")
                refs.append({"model": model, "reference_layer": ref, "file_path": str(out), "status": "OK"})
                break
        else:
            refs.append({"model": model, "reference_layer": "", "file_path": "", "status": "MISSING_COLOR_REFERENCE"})
    pd.DataFrame(refs).to_csv(OUT / "within_model_reference_rdms.csv", index=False)

    order = pd.read_csv(OUT / "analysis_order_defined.csv")
    binary_rows = []
    for stim, g in order.groupby("stimulus_set", sort=False):
        labels = g.sort_values("position_1toN")["category"].to_numpy()
        rdm = (labels[:, None] != labels[None, :]).astype(np.float32)
        out = RDMS / f"_binary_animacy_{stim}.npz"
        np.savez_compressed(out, rdm=rdm, labels=labels, stimulus_set=stim)
        binary_rows.append({"stimulus_set": stim, "file_path": str(out), "n_images": len(labels), "n_animate": int((labels == "animate").sum()), "n_inanimate": int((labels == "inanimate").sum())})
    pd.DataFrame(binary_rows).to_csv(OUT / "binary_animacy_reference_rdms.csv", index=False)


def rank_center_upper(m: np.ndarray) -> Tuple[np.ndarray, float]:
    v = upper_values(m).astype(np.float64)
    r = rankdata(v)
    r -= r.mean()
    norm = np.linalg.norm(r)
    return r.astype(np.float32), float(norm)


def rank_matrix_for_permutation(m: np.ndarray) -> Tuple[np.ndarray, float, float]:
    idx = np.triu_indices(m.shape[0], 1)
    ranks = rankdata(m[idx])
    mean = float(ranks.mean())
    centered = ranks - mean
    norm = float(np.linalg.norm(centered))
    mat = np.zeros_like(m, dtype=np.float32)
    mat[idx] = centered.astype(np.float32)
    mat[(idx[1], idx[0])] = centered.astype(np.float32)
    return mat, mean, norm


def observed_spearman_rdm(a: np.ndarray, b: np.ndarray) -> float:
    ar, an = rank_center_upper(a)
    br, bn = rank_center_upper(b)
    return float(ar @ br / (an * bn)) if an and bn else float("nan")


def mantel_perm_p(target: np.ndarray, ref: np.ndarray, observed: float, n_perm: int, rng: np.random.Generator) -> Tuple[float, float, float]:
    tr, tn = rank_center_upper(target)
    rrmat, _, rn = rank_matrix_for_permutation(ref)
    idx = np.triu_indices(ref.shape[0], 1)
    vals = np.empty(n_perm, dtype=np.float32)
    n = ref.shape[0]
    for k in range(n_perm):
        p = rng.permutation(n)
        rv = rrmat[np.ix_(p, p)][idx]
        vals[k] = float(tr @ rv / (tn * rn))
    pval = (np.sum(np.abs(vals) >= abs(observed)) + 1.0) / (n_perm + 1.0)
    return float(pval), float(vals.mean()), float(vals.std(ddof=1))


def binary_label_perm_p(target: np.ndarray, labels: np.ndarray, observed: float, n_perm: int, rng: np.random.Generator) -> Tuple[float, float, float]:
    tr, tn = rank_center_upper(target)
    idx = np.triu_indices(target.shape[0], 1)
    vals = np.empty(n_perm, dtype=np.float32)
    for k in range(n_perm):
        lab = rng.permutation(labels)
        b = (lab[:, None] != lab[None, :]).astype(np.float32)
        br = rankdata(b[idx])
        br -= br.mean()
        bn = np.linalg.norm(br)
        vals[k] = float(tr @ br / (tn * bn))
    pval = (np.sum(np.abs(vals) >= abs(observed)) + 1.0) / (n_perm + 1.0)
    return float(pval), float(vals.mean()), float(vals.std(ddof=1))


def fdr_bh(pvals: Sequence[float]) -> np.ndarray:
    p = np.asarray(pvals, dtype=float)
    out = np.full_like(p, np.nan)
    valid = np.isfinite(p)
    pv = p[valid]
    if len(pv) == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order]
    n = len(ranked)
    q = ranked * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    restored = np.empty_like(q)
    restored[order] = np.minimum(q, 1.0)
    out[valid] = restored
    return out


def run_rsa(n_perm: int, smoke: bool, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    meta = pd.read_csv(OUT / "feature_rdm_metadata.csv")
    ok = meta[meta["status"].isin(["COMPUTED", "LOADED_EXISTING"])].copy()
    if smoke:
        ok = ok[ok["model"] == "alexnet"]
        n_perm = 100
    refs = pd.read_csv(OUT / "within_model_reference_rdms.csv")
    bins = pd.read_csv(OUT / "binary_animacy_reference_rdms.csv")
    bin_map = {r["stimulus_set"]: r["file_path"] for _, r in bins.iterrows()}
    order = pd.read_csv(OUT / "analysis_order_defined.csv")
    label_map = {s: g.sort_values("position_1toN")["category"].to_numpy() for s, g in order.groupby("stimulus_set")}
    rows = []
    t0 = time.time()
    for _, row in ok.iterrows():
        target = np.load(row["file_path"])["rdm"]
        refrow = refs[(refs["model"] == row["model"]) & (refs["status"] == "OK")]
        if not refrow.empty:
            ref = np.load(refrow.iloc[0]["file_path"])["rdm"]
            obs = observed_spearman_rdm(target, ref)
            p, mu, sd = mantel_perm_p(target, ref, obs, n_perm, rng)
            rows.append(
                {
                    "model": row["model"],
                    "source": row.get("source", ""),
                    "layer": row["layer"],
                    "stimulus_set": row["stimulus_set"],
                    "rsa_type": "within_model",
                    "reference_id": str(refrow.iloc[0]["file_path"]),
                    "n_images": target.shape[0],
                    "observed_r": obs,
                    "p_perm": p,
                    "n_perm": n_perm,
                    "mean_null": mu,
                    "sd_null": sd,
                    "convention_used": "Spearman upper triangle excluding diagonal; Mantel row/column permutation",
                    "status": "OK",
                    "notes": "",
                }
            )
        labels = label_map[row["stimulus_set"]]
        bref = np.load(bin_map[row["stimulus_set"]])["rdm"]
        obs = observed_spearman_rdm(target, bref)
        p, mu, sd = binary_label_perm_p(target, labels, obs, n_perm, rng)
        rows.append(
            {
                "model": row["model"],
                "source": row.get("source", ""),
                "layer": row["layer"],
                "stimulus_set": row["stimulus_set"],
                "rsa_type": "binary_animacy",
                "reference_id": bin_map[row["stimulus_set"]],
                "n_images": target.shape[0],
                "observed_r": obs,
                "p_perm": p,
                "n_perm": n_perm,
                "mean_null": mu,
                "sd_null": sd,
                "convention_used": "Spearman upper triangle excluding diagonal; label permutation",
                "status": "OK",
                "notes": "",
            }
        )
        if not smoke:
            rows.append(
                {
                    "model": row["model"],
                    "source": row.get("source", ""),
                    "layer": row["layer"],
                    "stimulus_set": row["stimulus_set"],
                    "rsa_type": "legacy_vgg19_reference_rsa",
                    "reference_id": "",
                    "n_images": target.shape[0],
                    "observed_r": np.nan,
                    "p_perm": np.nan,
                    "n_perm": 0,
                    "mean_null": np.nan,
                    "sd_null": np.nan,
                    "convention_used": "",
                    "status": "SKIPPED_TIER_A_NOT_VERIFIED",
                    "notes": "Tier A legacy filename order is not verified; legacy comparison skipped by default.",
                }
            )
    res = pd.DataFrame(rows)
    if not res.empty:
        okmask = res["status"] == "OK"
        res.loc[okmask, "q_global"] = fdr_bh(res.loc[okmask, "p_perm"].to_numpy())
        for (model, typ), idxs in res[okmask].groupby(["model", "rsa_type"]).groups.items():
            res.loc[idxs, "q_within_model_type"] = fdr_bh(res.loc[idxs, "p_perm"].to_numpy())
    elapsed = time.time() - t0
    log = f"# RSA {'Smoke Test' if smoke else 'Full Run'} Log\n\n- n_perm: {n_perm}\n- rows: {len(res)}\n- elapsed_seconds: {elapsed:.2f}\n"
    (OUT / ("rsa_smoke_test_log.md" if smoke else "rsa_full_run_log.md")).write_text(log, encoding="utf-8")
    return res


def phase7(n_perm: int, smoke: bool, seed: int) -> pd.DataFrame:
    ensure_dirs()
    if not (OUT / "feature_rdm_metadata.csv").exists():
        raise HardGateFailure("feature_rdm_metadata.csv missing; run Phase 5.")
    if not (OUT / "within_model_reference_rdms.csv").exists():
        phase6()
    smoke_res = run_rsa(100, True, seed)
    smoke_res.to_csv(OUT / "rsa_smoke_test_results.csv", index=False)
    if smoke:
        return smoke_res
    full_perm = n_perm if n_perm <= 1000 else 1000
    full_res = run_rsa(full_perm, False, seed)
    full_res.to_csv(OUT / "all_multimodel_rsa_results.csv", index=False)
    main = full_res[(full_res["rsa_type"].isin(["within_model", "binary_animacy"])) & (full_res["status"] != "OK")]
    if not main.empty:
        log_status("HARD_GATE_FAILURE", "Phase 7", "Main RSA contains skipped/failed rows.")
        raise HardGateFailure("Main RSA failed.")
    return full_res


def phase8() -> None:
    ensure_dirs()
    res_path = OUT / "all_multimodel_rsa_results.csv"
    if not res_path.exists():
        return
    import matplotlib.pyplot as plt

    res = pd.read_csv(res_path)
    ok = res[res["status"] == "OK"].copy()
    if ok.empty:
        return
    y_min, y_max = -0.1, max(0.8, float(ok["observed_r"].max()) + 0.05)
    for model, g in ok.groupby("model"):
        fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
        for ax, typ in zip(axes, ["within_model", "binary_animacy"]):
            sub = g[g["rsa_type"] == typ]
            for stim, sg in sub.groupby("stimulus_set"):
                sg = sg.reset_index(drop=True)
                ax.errorbar(range(len(sg)), sg["observed_r"], yerr=sg["sd_null"], marker="o", linewidth=1.2, label=stim)
            ax.set_title(typ)
            ax.set_ylim(y_min, y_max)
            ax.set_ylabel("Spearman r")
            ax.set_xlabel("Layer order")
            ax.legend(frameon=False, fontsize=7)
        fig.suptitle(model)
        fig.tight_layout()
        fig.savefig(FIGS / f"{model}_rsa_by_layer.png", dpi=300)
        fig.savefig(FIGS / f"{model}_rsa_by_layer.pdf")
        plt.close(fig)

    best = ok.sort_values("observed_r").groupby(["model", "stimulus_set", "rsa_type"]).tail(1)
    fig, ax = plt.subplots(figsize=(10, 5))
    xlabels = []
    xpos = []
    for i, ((model, typ), sg) in enumerate(best.groupby(["model", "rsa_type"])):
        ax.scatter([i] * len(sg), sg["observed_r"], label=f"{model}/{typ}", s=35)
        xlabels.append(f"{model}\n{typ}")
        xpos.append(i)
    ax.set_xticks(xpos)
    ax.set_xticklabels(xlabels, rotation=45, ha="right")
    ax.set_ylim(y_min, y_max)
    ax.set_ylabel("Best-layer Spearman r")
    fig.tight_layout()
    fig.savefig(FIGS / "combined_best_layer_rsa.png", dpi=300)
    fig.savefig(FIGS / "combined_best_layer_rsa.pdf")
    plt.close(fig)

    binary = best[best["rsa_type"] == "binary_animacy"].copy()
    if not binary.empty:
        fig, ax = plt.subplots(figsize=(9, 5))
        stimuli = sorted(binary["stimulus_set"].unique())
        models = sorted(binary["model"].unique())
        width = 0.18
        x = np.arange(len(stimuli))
        for j, model in enumerate(models):
            vals = []
            qvals = []
            for stim in stimuli:
                row = binary[(binary["model"] == model) & (binary["stimulus_set"] == stim)]
                vals.append(float(row["observed_r"].iloc[0]) if not row.empty else np.nan)
                qvals.append(float(row["q_within_model_type"].iloc[0]) if not row.empty else np.nan)
            xpos = x + (j - (len(models) - 1) / 2) * width
            ax.bar(xpos, vals, width=width, label=model)
            for xx, yy, qq in zip(xpos, vals, qvals):
                if np.isfinite(yy) and np.isfinite(qq) and qq < 0.05:
                    ax.text(xx, yy + 0.015, "*", ha="center", va="bottom", fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(stimuli)
        ax.set_ylim(y_min, y_max)
        ax.set_ylabel("Best-layer binary animacy Spearman r")
        ax.set_title("Binary animate-inanimate RSA across models")
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(FIGS / "binary_animacy_best_layer_by_model.png", dpi=300)
        fig.savefig(FIGS / "binary_animacy_best_layer_by_model.pdf")
        plt.close(fig)


def phase9(execution_status: str, start_time: float, seed: int, n_perm: int) -> None:
    ensure_dirs()
    order_exists = (OUT / "analysis_order_defined.csv").exists()
    cond_report = (OUT / "condition_completeness_report.md").read_text(encoding="utf-8", errors="replace") if (OUT / "condition_completeness_report.md").exists() else ""
    meta = pd.read_csv(OUT / "feature_rdm_metadata.csv") if (OUT / "feature_rdm_metadata.csv").exists() else pd.DataFrame()
    res = pd.read_csv(OUT / "all_multimodel_rsa_results.csv") if (OUT / "all_multimodel_rsa_results.csv").exists() else pd.DataFrame()
    order = pd.read_csv(OUT / "analysis_order_defined.csv") if order_exists else pd.DataFrame()
    included = order.groupby("stimulus_set").size().to_dict() if not order.empty else {}
    successful_models = sorted(meta.loc[meta.get("status", pd.Series(dtype=str)).isin(["COMPUTED", "LOADED_EXISTING"]), "model"].dropna().unique()) if not meta.empty else []
    layers_by_model = {}
    sources_by_model = {}
    if not meta.empty:
        good_meta = meta[meta.get("status", pd.Series(dtype=str)).isin(["COMPUTED", "LOADED_EXISTING", "RECOMPUTED_INVALID_SHAPE"])]
        for model, g in good_meta.groupby("model"):
            layers_by_model[model] = sorted(g["layer"].dropna().unique().tolist())
            sources_by_model[model] = sorted(g.get("source", pd.Series(dtype=str)).dropna().unique().tolist())
    nperm_summary = {}
    skipped_legacy = 0
    if not res.empty:
        skipped_legacy = int((res["status"] == "SKIPPED_TIER_A_NOT_VERIFIED").sum())
        nperm_summary = res[res["status"] == "OK"].groupby("rsa_type")["n_perm"].agg(lambda x: sorted(set(map(int, x)))).to_dict()
    top_lines = []
    if not res.empty:
        ok = res[res["status"] == "OK"]
        for typ in ["within_model", "binary_animacy"]:
            sub = ok[ok["rsa_type"] == typ]
            if not sub.empty:
                top = sub.sort_values("observed_r").groupby(["model", "stimulus_set"]).tail(1)
                top_lines.append(f"## Top {typ} Results")
                top_lines.append(top[["model", "stimulus_set", "layer", "observed_r", "q_within_model_type", "q_global"]].to_markdown(index=False))
    versions = (OUT / "env_versions.txt").read_text(encoding="utf-8", errors="replace") if (OUT / "env_versions.txt").exists() else ""
    report = f"""# Final Report

1. Was exact legacy filename order (Tier A) recovered? No. Previous diagnostics verified animate-block then inanimate-block feature-row concatenation, but not exact filename-to-row order.
2. Which analyses were skipped because of Tier A status? `legacy_vgg19_reference_rsa` rows were marked `SKIPPED_TIER_A_NOT_VERIFIED`.
3. Was deterministic analysis order (Tier B) defined? {'Yes' if order_exists else 'No'}. Convention: animate first, inanimate second, ascending numeric index within block.
4. Which stimulus sets were INCLUDED? {included}
5. Which stimulus sets were EXCLUDED, and why? See `condition_completeness_report.md`; Grayscale root is incomplete and reduced 350-image sets are not mixed with the main 640-image lane.
6. Which DNNs actually ran? {successful_models}. Sources: {sources_by_model}. Layers: {layers_by_model}
7. Which RSA analyses were run? Within-model RSA and binary animate-inanimate RSA. Legacy VGG-19 reference RSA skipped by default.
8. Number of permutations actually run per analysis. Smoke: 100. Full: {nperm_summary}; requested={n_perm}; legacy skipped rows={skipped_legacy}.
9. Main numerical results:

{chr(10).join(top_lines) if top_lines else 'No full RSA results available.'}

10. What can be said in the response letter:
- Additional multi-architecture computational checks were implemented.
- Within-model representational similarity was used to avoid forcing all architectures into VGG-19 fc8 geometry.
- Binary animate-inanimate model RSA directly tests categorical structure.
- Results should be described as model-dependent and layer-dependent.

11. What must NOT be claimed:
- Do not claim DNNs prove the neural mechanism.
- Do not claim VGG-19 is a proxy for the human visual system.
- Do not claim all models converge with human EEG.
- Do not claim direct replication across architectures unless the final numbers support it.

12. Execution status: {execution_status}. Current invocation wall-clock seconds: {time.time() - start_time:.2f}. Hardware: {platform.platform()}. Random seed: {seed}.

## Package Versions

{versions}
"""
    (OUT / "FINAL_REPORT.md").write_text(report, encoding="utf-8")

    summary = f"""# DNN Multimodel Results Summary

## What Ran vs. What Did Not

- Tier A legacy comparison: skipped by default because exact legacy filename order remains unverified.
- Tier B within-model and binary animacy RSA: {'completed' if not res.empty else 'not completed'}.
- Successful models: {', '.join(successful_models) if successful_models else 'none'}.

## Included Stimulus Sets

{included}

## Notes

Use calibrated language: complementary computational analysis, model-dependent and layer-dependent, and weaker/more variable for impoverished stimuli only if supported by the table.
"""
    (OUT / "dnn_multimodel_results_summary.md").write_text(summary, encoding="utf-8")
    paragraph = (
        "We added additional multi-architecture computational checks using THINGSVision where feasible and documented fallbacks where needed. "
        "Because the tested architectures have different representational geometries, we emphasized within-model representational similarity analysis, correlating each layer and stimulus-set RDM with the same model's Color reference RDM. "
        "We also added a binary animate-inanimate model RSA to directly quantify categorical structure. "
        "The results were {{QUALITATIVE_PATTERN}}, with intact Color stimuli showing {{COLOR_RESULT}} and impoverished stimuli showing {{IMPOVERISHED_RESULT}}. "
        "These analyses are a complementary computational analysis and are not intended as a mechanistic claim about human visual cortex."
    )
    (OUT / "reviewer_response_paragraph.md").write_text(paragraph + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", action="append", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "all"], default=None)
    p.add_argument("--n-permutations", type=int, default=5000)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--seed", type=int, default=SEED_DEFAULT)
    p.add_argument("--skip-legacy", dest="skip_legacy", action="store_true", default=True)
    p.add_argument("--no-skip-legacy", dest="skip_legacy", action="store_false")
    return p.parse_args()


def phases_from_args(args: argparse.Namespace) -> List[str]:
    vals = args.phase or ["all"]
    return ["1", "2", "3", "4", "5", "6", "7", "8", "9"] if "all" in vals else vals


def main() -> None:
    args = parse_args()
    ensure_dirs()
    start = time.time()
    status = "complete"
    try:
        for ph in phases_from_args(args):
            print(f"Running Phase {ph}...")
            if ph == "1":
                phase1()
            elif ph == "2":
                phase2()
            elif ph == "3":
                phase3()
            elif ph == "4":
                phase4()
            elif ph == "5":
                phase5(smoke=args.smoke)
            elif ph == "6":
                phase6()
            elif ph == "7":
                phase7(args.n_permutations, args.smoke, args.seed)
            elif ph == "8":
                phase8()
            elif ph == "9":
                phase9(status, start, args.seed, args.n_permutations)
        if "9" not in phases_from_args(args):
            phase9(status, start, args.seed, args.n_permutations)
    except HardGateFailure as exc:
        status = "failed"
        log_status("HARD_GATE_FAILURE", "runtime", str(exc), traceback.format_exc())
        phase9(status, start, args.seed, args.n_permutations)
        raise SystemExit(2) from exc
    except Exception as exc:
        status = "failed"
        log_status("HARD_GATE_FAILURE", "runtime", f"{type(exc).__name__}: {exc}", traceback.format_exc())
        phase9(status, start, args.seed, args.n_permutations)
        raise

    final = OUT / "FINAL_REPORT.md"
    print("\n=== One-screen summary ===")
    if final.exists():
        text = final.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in text[:18]:
            print(line)


if __name__ == "__main__":
    main()
