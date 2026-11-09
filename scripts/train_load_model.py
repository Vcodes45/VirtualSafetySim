from __future__ import annotations

import argparse
from pathlib import Path
import json
import time
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["pupil_diameter_mm", "fixation_count", "saccade_count", "blink_rate_per_min", "heart_rate_bpm", "rmssd_ms", "sdnn_ms"]


def grouped_evaluate(model, X: pd.DataFrame, y: pd.Series, groups: pd.Series) -> dict:
    logo = LeaveOneGroupOut()
    truth, predicted, durations = [], [], []
    folds = 0
    for train_idx, test_idx in logo.split(X, y, groups):
        if len(np.unique(y.iloc[train_idx])) < 2:
            continue
        fold_model = __import__("sklearn.base", fromlist=["clone"]).clone(model)
        fold_model.fit(X.iloc[train_idx], y.iloc[train_idx])
        started = time.perf_counter()
        fold_predictions = fold_model.predict(X.iloc[test_idx])
        durations.append((time.perf_counter() - started) / max(1, len(test_idx)))
        truth.extend(y.iloc[test_idx].tolist())
        predicted.extend(fold_predictions.tolist())
        folds += 1
    if folds == 0:
        raise ValueError("Unable to form grouped validation folds. Check the participant and label columns.")
    return {
        "folds": folds,
        "macro_f1": float(f1_score(truth, predicted, average="macro")),
        "accuracy": float(accuracy_score(truth, predicted)),
        "balanced_accuracy": float(balanced_accuracy_score(truth, predicted)),
        "mean_prediction_ms_per_window": float(np.mean(durations) * 1000),
        "validation": "LeaveOneGroupOut by participant_id",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train/evaluate baseline cognitive-load classifiers on harmonized sensor windows.")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "processed" / "harmonized_sensor_windows.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "models" / "cognitive_load_model.joblib")
    parser.add_argument("--allow-demo-data", action="store_true", help="Allow synthetic demo rows; model will be marked demo-only.")
    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}\nCreate a harmonized CSV using docs/DATASETS_AND_SENSOR_SCHEMA.md. Synthetic demo: python scripts/generate_demo_sensor_windows.py --output data/example/demo_sensor_windows.csv -- then pass --allow-demo-data explicitly.")
    frame = pd.read_csv(args.input)
    required = set(FEATURES + ["participant_id", "cognitive_load_label"])
    missing = sorted(required - set(frame.columns))
    if missing:
        raise SystemExit(f"Input is missing required columns: {', '.join(missing)}")
    demo_only = "data_source" in frame.columns and frame["data_source"].astype(str).str.contains("synthetic_demo", case=False).any()
    if demo_only and not args.allow_demo_data:
        raise SystemExit("Synthetic demo rows detected. Pass --allow-demo-data only for a code-path demonstration, never for research claims.")
    frame = frame.dropna(subset=["participant_id", "cognitive_load_label"]).copy()
    frame["cognitive_load_label"] = frame["cognitive_load_label"].astype(str).str.lower()
    frame = frame[frame["cognitive_load_label"].isin(["low", "medium", "high"])]
    frame = frame.dropna(subset=FEATURES, how="all")
    if frame["participant_id"].nunique() < 2:
        raise SystemExit("At least two participant IDs are needed for grouped validation.")
    X = frame[FEATURES].apply(pd.to_numeric, errors="coerce")
    y = frame["cognitive_load_label"]
    groups = frame["participant_id"].astype(str)
    if y.nunique() < 2:
        raise SystemExit("At least two cognitive_load_label classes are required.")

    candidates = {
        "logistic_regression": Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()), ("model", LogisticRegression(max_iter=2000, class_weight="balanced"))]),
        "random_forest": Pipeline([("imputer", SimpleImputer(strategy="median")), ("model", RandomForestClassifier(n_estimators=250, min_samples_leaf=2, class_weight="balanced", random_state=42, n_jobs=-1))]),
    }
    results = {}
    best_name, best_f1 = None, -1.0
    for name, candidate in candidates.items():
        result = grouped_evaluate(candidate, X, y, groups)
        results[name] = result
        print(f"{name}: {json.dumps(result, sort_keys=True)}")
        if result["macro_f1"] > best_f1:
            best_name, best_f1 = name, result["macro_f1"]
    final_model = candidates[best_name]
    final_model.fit(X, y)
    source_label = "synthetic_demo_only" if demo_only else "user_supplied_harmonized_dataset_not_independently_verified"
    bundle = {
        "model": final_model,
        "feature_columns": FEATURES,
        "metadata": {
            "model_name": best_name,
            "training_source": source_label,
            "demo_only": bool(demo_only),
            "row_count": int(len(frame)),
            "participant_count": int(groups.nunique()),
            "class_counts": {str(k): int(v) for k, v in y.value_counts().items()},
            "grouped_validation": results,
            "validation_method": "LeaveOneGroupOut by participant_id",
            "note": "Prototype baseline only. Validate labels, source-data alignment and external generalization before research use.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, args.output)
    report_path = args.output.with_suffix(".evaluation.json")
    report_path.write_text(json.dumps(bundle["metadata"], indent=2), encoding="utf-8")
    print(f"Saved model bundle: {args.output}")
    print(f"Saved evaluation metadata: {report_path}")
    if demo_only:
        print("WARNING: This model is trained on synthetic data and is for software demonstration only.")


if __name__ == "__main__":
    main()
