"""
services/artifact_manager.py
=============================
Saves and loads fitted encoders and scalers to disk.

WHY THIS MATTERS FOR PRODUCTION
────────────────────────────────
After the pipeline runs, you have:
    encoder_map  → fitted LabelEncoders, frequency maps, one-hot mappings
    scaler_map   → fitted MinMaxScaler / RobustScaler objects

These are not just data — they are TRAINED objects.
When new data arrives (inference / test set), you must apply
the EXACT SAME transformation, not re-fit on new data.

Re-fitting on new data = data leakage = wrong predictions.

Example:
    Training data: Sex encoded as male=1, female=0
    If you re-fit on test data, it might become male=0, female=1
    → the model now gets opposite inputs → garbage predictions

WHAT GETS SAVED
────────────────
artifacts/
└── {domain}_{timestamp}/
    ├── encoders.pkl     → the full encoder_map dict
    ├── scalers.pkl      → the full scaler_map dict
    ├── metadata.json    → human-readable info about what was saved
    └── feature_list.json → ordered list of feature columns

CONNECTION TO MODULE 1
──────────────────────
module1_output["dataset_info"]["domain"]
    → used to name the artifact folder (e.g. "titanic_20240101_120000")
module1_output["dataset_info"]["file_name"]
    → recorded in metadata so you know which file these artifacts came from

USAGE (in pipeline_module2.py)
──────────────────────────────
    from module2.services.artifact_manager import save_artifacts, load_artifacts

    paths = save_artifacts(
        encoder_map    = artifacts["encoder_map"],
        scaler_map     = artifacts["scaler_map"],
        feature_cols   = result["feature_columns"],
        module1_output = module1_output,
    )
    # paths = {"encoders": "...", "scalers": "...", "metadata": "..."}

    # Later — load back for inference:
    loaded = load_artifacts(paths["base_dir"])
"""

import os
import json
import joblib
from datetime import datetime
from typing import Dict, Any, List

DEFAULT_ARTIFACTS_DIR = "artifacts"


def save_artifacts(
    encoder_map: Dict[str, Any],
    scaler_map: Dict[str, Any],
    feature_cols: List[str],
    module1_output: dict,
    base_dir: str = DEFAULT_ARTIFACTS_DIR,
) -> Dict[str, str]:
    """
    Serializes and saves preprocessing artifacts (encoders and scalers) alongside metadata.

    Args:
        encoder_map (Dict[str, Any]): Dictionary of fitted encoding objects from the encoding step.
        scaler_map (Dict[str, Any]): Dictionary of fitted scaler objects from the scaling step.
        feature_cols (List[str]): An ordered list of features expected during inference.
        module1_output (dict): The complete context output from Module 1.
        base_dir (str, optional): Root directory for saving the artifact folder. Defaults to DEFAULT_ARTIFACTS_DIR.

    Returns:
        Dict[str, str]: A mapping of artifact keys to their absolute file paths (e.g., 'encoders', 'scalers', 'metadata').
    """
    dataset_info = module1_output.get("dataset_info", {})
    domain       = dataset_info.get("domain", "dataset").lower().replace(" ", "_")
    file_name    = dataset_info.get("file_name", "unknown")
    timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create artifact subfolder: artifacts/titanic_20240101_120000/
    artifact_dir = os.path.join(base_dir, f"{domain}_{timestamp}")
    os.makedirs(artifact_dir, exist_ok=True)

    paths = {
        "base_dir": artifact_dir,
        "encoders": os.path.join(artifact_dir, "encoders.pkl"),
        "scalers":  os.path.join(artifact_dir, "scalers.pkl"),
        "metadata": os.path.join(artifact_dir, "metadata.json"),
        "features": os.path.join(artifact_dir, "feature_list.json"),
    }

    # ── Save encoders ──
    # Strip non-serialisable scaler objects from encoder_map before saving
    # (encoder_map is already serialisable — mappings are plain dicts)
    joblib.dump(encoder_map, paths["encoders"])

    # ── Save scalers ──
    # scaler_map contains fitted sklearn objects — joblib handles these
    joblib.dump(scaler_map, paths["scalers"])

    # ── Save feature list ──
    with open(paths["features"], "w", encoding="utf-8") as f:
        json.dump({"feature_columns": feature_cols}, f, indent=2)

    # ── Save metadata ──
    metadata = _build_metadata(
        encoder_map, scaler_map, feature_cols, module1_output, artifact_dir, timestamp
    )
    with open(paths["metadata"], "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    return paths


def load_artifacts(artifact_dir: str) -> Dict[str, Any]:
    """
    Loads saved preprocessing artifacts and metadata from disk for future inference.

    Args:
        artifact_dir (str): The directory containing the serialized artifact files.

    Returns:
        Dict[str, Any]: A dictionary containing the loaded 'encoder_map', 'scaler_map', 'feature_columns', and 'metadata'.
        
    Raises:
        FileNotFoundError: If the specified artifact_dir does not exist.
    """
    encoders_path = os.path.join(artifact_dir, "encoders.pkl")
    scalers_path  = os.path.join(artifact_dir, "scalers.pkl")
    features_path = os.path.join(artifact_dir, "feature_list.json")
    metadata_path = os.path.join(artifact_dir, "metadata.json")

    if not os.path.exists(artifact_dir):
        raise FileNotFoundError(
            f"Artifact directory not found: {artifact_dir}"
        )

    result = {}

    if os.path.exists(encoders_path):
        result["encoder_map"] = joblib.load(encoders_path)

    if os.path.exists(scalers_path):
        result["scaler_map"] = joblib.load(scalers_path)

    if os.path.exists(features_path):
        with open(features_path, "r", encoding="utf-8") as f:
            result["feature_columns"] = json.load(f)["feature_columns"]

    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            result["metadata"] = json.load(f)

    return result


def list_saved_artifacts(base_dir: str = DEFAULT_ARTIFACTS_DIR) -> List[Dict[str, str]]:
    """
    Lists all saved artifact sets available in the specified base directory.

    Args:
        base_dir (str, optional): The base directory containing all artifacts. Defaults to DEFAULT_ARTIFACTS_DIR.

    Returns:
        List[Dict[str, str]]: A list of dictionaries detailing the path and metadata of each artifact set found.
    """
    if not os.path.exists(base_dir):
        return []

    entries = []
    for folder in sorted(os.listdir(base_dir), reverse=True):
        full_path    = os.path.join(base_dir, folder)
        metadata_path = os.path.join(full_path, "metadata.json")
        if os.path.isdir(full_path):
            entry = {"name": folder, "path": full_path}
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    entry["domain"]   = meta.get("domain", "unknown")
                    entry["saved_at"] = meta.get("saved_at", "unknown")
                    entry["n_encoders"] = meta.get("n_encoders", 0)
                    entry["n_scalers"]  = meta.get("n_scalers", 0)
            entries.append(entry)

    return entries


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _build_metadata(
    encoder_map: Dict[str, Any], scaler_map: Dict[str, Any], feature_cols: List[str],
    module1_output: dict, artifact_dir: str, timestamp: str
) -> dict:
    """
    Compiles human-readable metadata detailing the preprocessing artifacts created for the dataset.

    Args:
        encoder_map (Dict[str, Any]): Fitted categorical encoders.
        scaler_map (Dict[str, Any]): Fitted numeric scalers.
        feature_cols (List[str]): The finalized list of predictive features.
        module1_output (dict): The complete context from Module 1.
        artifact_dir (str): Directory where artifacts are saved.
        timestamp (str): The ISO timestamp identifying the save action.

    Returns:
        dict: A comprehensive dictionary of metadata properties summarizing the artifacts.
    """

    dataset_info = module1_output.get("dataset_info", {})
    schema       = module1_output.get("data_schema", {})

    # Summarise encoder types
    encoder_summary = {}
    for col, info in encoder_map.items():
        if isinstance(info, dict):
            encoder_summary[col] = info.get("type", "unknown")

    # Summarise scaler types
    scaler_summary = {}
    for col, info in scaler_map.items():
        if isinstance(info, dict):
            scaler_summary[col] = info.get("type", "unknown")

    return {
        "saved_at":        datetime.now().isoformat(),
        "timestamp":       timestamp,
        "artifact_dir":    artifact_dir,
        "domain":          dataset_info.get("domain", "unknown"),
        "dataset_type":    dataset_info.get("dataset_type", "unknown"),
        "source_file":     dataset_info.get("file_name", "unknown"),
        "original_rows":   dataset_info.get("rows", 0),
        "original_cols":   dataset_info.get("columns", 0),
        "n_features":      len(feature_cols),
        "feature_columns": feature_cols,
        "n_encoders":      len(encoder_map),
        "encoders":        encoder_summary,
        "n_scalers":       len(scaler_map),
        "scalers":         scaler_summary,
        "schema_numeric":  schema.get("numeric", []),
        "schema_categorical": schema.get("categorical", []),
        "usage_note": (
            "Load with: artifact_manager.load_artifacts(artifact_dir). "
            "Apply to new data with: "
            "encoding.apply_saved_encoding(df, encoder_map) then "
            "scaling.apply_saved_scaling(df, scaler_map)."
        ),
    }

