"""Compile supplementary binary animate-inanimate RSA summaries.

This targeted script reuses existing RSA/RDM outputs. It does not run feature
extraction or image preprocessing.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.stats import rankdata
from statsmodels.stats.multitest import multipletests


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "outputs_multimodel_dnn_rsa"
RESULTS_CSV = OUT_DIR / "all_multimodel_rsa_results_with_grayscale.csv"
METADATA_CSV = OUT_DIR / "feature_rdm_metadata_with_grayscale.csv"
LEGACY_DIR = ROOT / "Correlation Dissimilarity"
N_PERM = 1000
SEED = 20240517

MODEL_ORDER = ["vgg19_legacy", "alexnet", "resnet50", "cornet_s", "vgg16"]
MODEL_LABELS = {
    "vgg19_legacy": "VGG-19",
    "alexnet": "AlexNet",
    "resnet50": "ResNet-50",
    "cornet_s": "CORnet-S",
    "vgg16": "VGG-16",
}
STIMULUS_ORDER = [
    ("Color", "Color"),
    ("Grayscale", "Grayscale"),
    ("CPS", "Phase-scrambled"),
    ("GPS", "Grayscale phase-scrambled"),
    ("Texform", "Texform"),
]
LEGACY_CONDITIONS = {
    "Color": "Color",
    "Grayscale": "GrayScale",
    "CPS": "Color_Scrambled",
    "GPS": "Gray_scrambled",
    "Texform": "newTexform",
}
VGG19_LAYERS = [
    "conv1_1",
    "conv1_2",
    "conv2_1",
    "conv2_2",
    "conv3_1",
    "conv3_2",
    "conv3_3",
    "conv3_4",
    "conv4_1",
    "conv4_2",
    "conv4_3",
    "conv4_4",
    "conv5_1",
    "conv5_2",
    "conv5_3",
    "conv5_4",
    "fc6",
    "fc7",
    "fc8",
]


def upper_tri_values(matrix: np.ndarray) -> np.ndarray:
    idx = np.triu_indices_from(matrix, k=1)
    return matrix[idx]


def binary_rdm(n_per_category: int = 320) -> np.ndarray:
    labels = np.r_[np.zeros(n_per_category, dtype=int), np.ones(n_per_category, dtype=int)]
    return (labels[:, None] != labels[None, :]).astype(float)


def rdm_from_labels(labels: np.ndarray) -> np.ndarray:
    return (labels[:, None] != labels[None, :]).astype(float)


class BinaryPermutationCache:
    def __init__(self, rng: np.random.Generator, n_perm: int = N_PERM) -> None:
        labels = np.r_[np.zeros(320, dtype=np.int8), np.ones(320, dtype=np.int8)]
        tri = np.triu_indices(labels.size, k=1)
        self.n_pairs = len(tri[0])
        observed_binary = (labels[tri[0]] != labels[tri[1]]).astype(np.float64)
        self.observed_z = self._zscore(observed_binary)
        self.null_z = np.empty((n_perm, self.n_pairs), dtype=np.float32)
        for i in range(n_perm):
            shuffled = rng.permutation(labels)
            binary_vec = (shuffled[tri[0]] != shuffled[tri[1]]).astype(np.float64)
            self.null_z[i] = self._zscore(binary_vec).astype(np.float32)

    @staticmethod
    def _zscore(values: np.ndarray) -> np.ndarray:
        values = values.astype(np.float64, copy=False)
        return (values - values.mean()) / values.std(ddof=1)


def vectorized_binary_permutation_test(
    rdm: np.ndarray,
    cache: BinaryPermutationCache,
) -> tuple[float, float, float, float]:
    labels = np.r_[np.zeros(320, dtype=int), np.ones(320, dtype=int)]
    target_vec = upper_tri_values(rdm)
    mask = np.isfinite(target_vec)
    if not np.all(mask):
        target_vec = target_vec[mask]
        observed_z = cache.observed_z[mask]
        null_z = cache.null_z[:, mask]
        denom = mask.sum() - 1
    else:
        observed_z = cache.observed_z
        null_z = cache.null_z
        denom = cache.n_pairs - 1
    # Spearman correlation equals Pearson correlation between rank vectors.
    target_ranks_z = BinaryPermutationCache._zscore(rankdata(target_vec, method="average"))
    observed = float(np.dot(target_ranks_z, observed_z) / denom)
    null = (null_z @ target_ranks_z.astype(np.float32)) / denom
    p_perm = (np.sum(np.abs(null) >= abs(observed)) + 1.0) / (null.shape[0] + 1.0)
    return observed, float(p_perm), float(np.nanmean(null)), float(np.nanstd(null, ddof=1))


def load_npz_rdm(path: Path) -> np.ndarray:
    with np.load(path, allow_pickle=False) as data:
        if "rdm" in data:
            return np.asarray(data["rdm"], dtype=float)
        if "dissimilarity_matrix" in data:
            return np.asarray(data["dissimilarity_matrix"], dtype=float)
        keys = list(data.keys())
        if len(keys) == 1:
            return np.asarray(data[keys[0]], dtype=float)
        raise KeyError(f"Could not identify RDM array in {path}; keys={keys}")


def load_legacy_mat_rdm(path: Path) -> np.ndarray:
    mat = loadmat(path)
    if "dissimilarityMatrix" not in mat:
        raise KeyError(f"`dissimilarityMatrix` not found in {path}")
    return np.asarray(mat["dissimilarityMatrix"], dtype=float)


def existing_binary_rows() -> pd.DataFrame:
    df = pd.read_csv(RESULTS_CSV)
    return df[(df["rsa_type"] == "binary_animacy") & (df["status"] == "OK")].copy()


def compute_missing_grayscale_rows(existing: pd.DataFrame, cache: BinaryPermutationCache) -> list[dict]:
    metadata = pd.read_csv(METADATA_CSV)
    rows: list[dict] = []
    for model in ["alexnet", "resnet50", "cornet_s", "vgg16"]:
        if not existing[(existing["model"] == model) & (existing["stimulus_set"] == "Grayscale")].empty:
            continue
        sub = metadata[
            (metadata["model"] == model)
            & (metadata["stimulus_set"] == "Grayscale")
        ].copy()
        sub = sub[sub["file_path"].notna()].copy()
        if sub.empty:
            raise RuntimeError(f"No saved Grayscale RDM metadata found for {model}")
        for _, item in sub.iterrows():
            rdm_path = Path(item["file_path"])
            rdm = load_npz_rdm(rdm_path)
            if rdm.shape != (640, 640):
                raise ValueError(f"Expected 640x640 Grayscale RDM for {model}, got {rdm.shape}: {rdm_path}")
            r, p, mean_null, sd_null = vectorized_binary_permutation_test(rdm, cache)
            rows.append(
                {
                    "model": model,
                    "source": item.get("source", "existing_saved_rdm"),
                    "layer": item["layer"],
                    "stimulus_set": "Grayscale",
                    "rsa_type": "binary_animacy",
                    "reference_id": str(OUT_DIR / "rdms" / "_binary_animacy_Grayscale.npz"),
                    "n_images": 640,
                    "observed_r": r,
                    "p_perm": p,
                    "n_perm": N_PERM,
                    "mean_null": mean_null,
                    "sd_null": sd_null,
                    "convention_used": "Spearman upper triangle excluding diagonal; label permutation",
                    "status": "OK",
                    "notes": "Targeted binary RSA from existing saved Grayscale RDM; no feature extraction rerun.",
                }
            )
    return rows


def compute_vgg19_rows(cache: BinaryPermutationCache) -> list[dict]:
    rows: list[dict] = []
    for stim_key, _ in STIMULUS_ORDER:
        legacy_condition = LEGACY_CONDITIONS[stim_key]
        for layer in VGG19_LAYERS:
            path = LEGACY_DIR / f"correlationDissimilarityMatrix_{layer}_{legacy_condition}.mat"
            if not path.exists():
                raise FileNotFoundError(path)
            rdm = load_legacy_mat_rdm(path)
            if rdm.shape != (640, 640):
                raise ValueError(f"Expected 640x640 VGG-19 RDM, got {rdm.shape}: {path}")
            r, p, mean_null, sd_null = vectorized_binary_permutation_test(rdm, cache)
            rows.append(
                {
                    "model": "vgg19_legacy",
                    "source": "legacy_matlab_vgg19_rdm",
                    "layer": layer,
                    "stimulus_set": stim_key,
                    "rsa_type": "binary_animacy",
                    "reference_id": "binary_animacy_animate_first_inanimate_second_640",
                    "n_images": 640,
                    "observed_r": r,
                    "p_perm": p,
                    "n_perm": N_PERM,
                    "mean_null": mean_null,
                    "sd_null": sd_null,
                    "convention_used": "Spearman upper triangle excluding diagonal; label permutation",
                    "status": "OK",
                    "notes": f"Targeted binary RSA from legacy VGG-19 MATLAB RDM ({legacy_condition}); no feature extraction rerun.",
                }
            )
    return rows


def apply_fdr(binary_df: pd.DataFrame) -> pd.DataFrame:
    binary_df = binary_df.copy()
    binary_df["q_global_binary"] = np.nan
    ok = binary_df["status"].eq("OK") & binary_df["p_perm"].notna()
    binary_df.loc[ok, "q_global_binary"] = multipletests(binary_df.loc[ok, "p_perm"], method="fdr_bh")[1]
    binary_df["q_within_model_binary"] = np.nan
    for model, idx in binary_df[ok].groupby("model").groups.items():
        binary_df.loc[idx, "q_within_model_binary"] = multipletests(
            binary_df.loc[idx, "p_perm"],
            method="fdr_bh",
        )[1]
    return binary_df


def best_layer_table(binary_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    display_rows = []
    best_records = []
    for stim_key, stim_label in STIMULUS_ORDER:
        row = {"Stimulus set": stim_label}
        display_row = {"Stimulus set": stim_label}
        for model in MODEL_ORDER:
            sub = binary_df[
                (binary_df["model"] == model)
                & (binary_df["stimulus_set"] == stim_key)
                & (binary_df["rsa_type"] == "binary_animacy")
                & (binary_df["status"] == "OK")
            ].copy()
            if sub.empty:
                raise RuntimeError(f"Missing binary RSA rows for {model} / {stim_key}")
            sub = sub.sort_values(["observed_r", "layer"], ascending=[False, True])
            best = sub.iloc[0]
            model_label = MODEL_LABELS[model]
            rho = float(best["observed_r"])
            row[f"{model_label} Best-layer Spearman rho"] = f"{rho:.3f}"
            row[f"{model_label} Best layer"] = str(best["layer"])
            display_row[f"{model_label} Best-layer Spearman ρ"] = f"{rho:.3f}"
            display_row[f"{model_label} Best layer"] = str(best["layer"])
            best_records.append(
                {
                    "stimulus_set": stim_label,
                    "source_stimulus_label": stim_key,
                    "model": model_label,
                    "best_layer": str(best["layer"]),
                    "best_layer_spearman_rho": rho,
                    "p_perm": float(best["p_perm"]),
                    "q_within_model_binary": float(best["q_within_model_binary"]),
                    "q_global_binary": float(best["q_global_binary"]),
                    "n_perm": int(best["n_perm"]),
                }
            )
        rows.append(row)
        display_rows.append(display_row)
    return pd.DataFrame(rows), pd.DataFrame(best_records), pd.DataFrame(display_rows)


def write_outputs(
    table: pd.DataFrame,
    best_long: pd.DataFrame,
    binary_all: pd.DataFrame,
    display_table: pd.DataFrame,
) -> None:
    csv_path = OUT_DIR / "supplementary_binary_rsa_table.csv"
    md_path = OUT_DIR / "supplementary_binary_rsa_table.md"
    all_path = OUT_DIR / "binary_animacy_all_models_with_vgg19.csv"
    notes_path = OUT_DIR / "supplementary_binary_rsa_notes.md"
    paragraph_path = OUT_DIR / "supplementary_binary_rsa_text.md"

    table.to_csv(csv_path, index=False, encoding="utf-8")
    binary_all.to_csv(all_path, index=False, encoding="utf-8")
    best_long.to_csv(OUT_DIR / "supplementary_binary_rsa_best_layers_long.csv", index=False, encoding="utf-8")

    md_text = (
        "# Supplementary Table S2. Binary animate-inanimate RSA across architectures\n\n"
        + display_table.to_markdown(index=False, disable_numparse=True)
        + "\n\n"
        "Values report the best-layer Spearman rho for each model and stimulus set. "
        "The corresponding best layer is listed in the adjacent column for each model.\n"
    )
    md_path.write_text(md_text, encoding="utf-8")

    notes = f"""# Supplementary Binary RSA Notes

- Source consolidated CSV: `{RESULTS_CSV}`
- Existing binary RSA rows were reused for AlexNet, ResNet-50, CORnet-S, and VGG-16 where present.
- VGG-19 binary RSA was absent from the consolidated CSV and was computed from legacy MATLAB RDM files in `{LEGACY_DIR}`.
- Grayscale binary RSA rows for AlexNet, ResNet-50, CORnet-S, and VGG-16 were absent from the consolidated CSV and were computed from existing saved Grayscale RDMs under `{OUT_DIR / 'rdms'}`.
- No feature extraction, image processing, or DNN forward passes were rerun.
- Binary category RDM convention: 640 images, 320 animate followed by 320 inanimate; within-category pairs = 0, between-category pairs = 1.
- Correlation convention: Spearman rho over the upper triangle, excluding the diagonal.
- Permutation test: label permutation preserving category counts, {N_PERM} permutations, seed = {SEED}.
- FDR correction: Benjamini-Hochberg within each model and globally across all binary RSA rows in `binary_animacy_all_models_with_vgg19.csv`.
"""
    notes_path.write_text(notes, encoding="utf-8")

    paragraph = """Following the reviewer’s suggestion, we performed an additional representational similarity analysis using a theoretical binary animate-inanimate model RDM. In this model, within-category image pairs were assigned a dissimilarity of 0 and between-category animate-inanimate pairs were assigned a dissimilarity of 1. For each architecture and stimulus set, layer-wise DNN RDMs were correlated with this binary model using Spearman correlations over the upper triangular RDM entries, excluding the diagonal. Statistical significance was assessed with 1,000 label permutations preserving the animate/inanimate category counts, followed by Benjamini-Hochberg FDR correction within model and across the full set of binary RSA tests. This complementary sanity-check analysis showed that intact Color and Grayscale images retained the strongest animate-inanimate categorical structure across architectures, whereas the phase-scrambled, grayscale phase-scrambled, and texform stimuli generally showed weaker best-layer correlations. This pattern is consistent with the reference-RDM analysis in suggesting reduced representational alignment for impoverished stimuli, while avoiding any claim that the tested DNNs constitute a mechanistic model of human visual cortex.\n"""
    paragraph_path.write_text(paragraph, encoding="utf-8")


def main() -> None:
    rng = np.random.default_rng(SEED)
    cache = BinaryPermutationCache(rng, N_PERM)
    existing = existing_binary_rows()
    vgg_present = "vgg19_legacy" in set(existing["model"])
    add_rows = []
    add_rows.extend(compute_missing_grayscale_rows(existing, cache))
    if not vgg_present:
        add_rows.extend(compute_vgg19_rows(cache))
    combined = pd.concat([existing, pd.DataFrame(add_rows)], ignore_index=True, sort=False)
    combined = apply_fdr(combined)
    table, best_long, display_table = best_layer_table(combined)
    write_outputs(table, best_long, combined, display_table)
    print(f"Existing binary models: {sorted(existing['model'].unique())}")
    print(f"VGG-19 present in source CSV: {vgg_present}")
    print(f"Targeted rows added: {len(add_rows)}")
    print(f"Wrote {OUT_DIR / 'supplementary_binary_rsa_table.csv'}")
    print(f"Wrote {OUT_DIR / 'supplementary_binary_rsa_table.md'}")


if __name__ == "__main__":
    main()
