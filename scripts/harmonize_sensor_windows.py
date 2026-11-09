from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["pupil_diameter_mm", "fixation_count", "saccade_count", "blink_rate_per_min", "heart_rate_bpm", "rmssd_ms", "sdnn_ms"]


def timestamp_seconds(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().mean() > 0.8:
        return numeric
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    if parsed.notna().mean() < 0.8:
        raise ValueError("Timestamp column must be numeric seconds or parseable datetimes.")
    return parsed.astype("int64") / 1e9


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize a researcher-mapped sensor CSV into 10-second feature windows.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--column-map-json", required=True, help="JSON mapping canonical field names to source CSV column names.")
    parser.add_argument("--label-map-json", default="{}", help="Optional JSON mapping source labels to low/medium/high.")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "processed" / "harmonized_sensor_windows.csv")
    parser.add_argument("--window-seconds", type=int, default=10)
    args = parser.parse_args()
    if args.window_seconds < 1:
        parser.error("--window-seconds must be positive")
    if not args.input.exists():
        parser.error(f"Input not found: {args.input}")
    mapping = json.loads(args.column_map_json)
    label_map = {str(k).lower(): str(v).lower() for k, v in json.loads(args.label_map_json).items()}
    frame = pd.read_csv(args.input)
    required = ["participant_id", "timestamp", "cognitive_load_label"]
    missing_map = [name for name in required if name not in mapping]
    if missing_map:
        parser.error(f"--column-map-json must map: {', '.join(missing_map)}")
    required_source = [mapping[name] for name in required]
    missing_source = [name for name in required_source if name not in frame.columns]
    if missing_source:
        parser.error(f"Mapped source columns missing from CSV: {', '.join(missing_source)}")

    data = pd.DataFrame()
    data["participant_id"] = frame[mapping["participant_id"]].astype(str)
    data["timestamp_seconds"] = timestamp_seconds(frame[mapping["timestamp"]])
    original_labels = frame[mapping["cognitive_load_label"]].astype(str).str.lower()
    data["cognitive_load_label"] = original_labels.map(lambda label: label_map.get(label, label))
    invalid_labels = sorted(set(data["cognitive_load_label"].dropna()) - {"low", "medium", "high"})
    if invalid_labels:
        parser.error(f"Unmapped load labels {invalid_labels}. Pass --label-map-json mapping source labels to low/medium/high.")

    numeric_cols = ["pupil_diameter_mm", "fixation_count", "saccade_count", "blink_count", "blink_rate_per_min", "heart_rate_bpm", "rmssd_ms", "sdnn_ms"]
    for canonical in numeric_cols:
        source = mapping.get(canonical)
        if source and source in frame.columns:
            data[canonical] = pd.to_numeric(frame[source], errors="coerce")
    feature_present = False
    for feature in FEATURES:
        if feature in data:
            feature_present = True
        else:
            data[feature] = np.nan
    if not feature_present:
        parser.error("Map at least one sensor feature column in --column-map-json.")

    data = data.dropna(subset=["participant_id", "timestamp_seconds", "cognitive_load_label"])
    data["window_start_seconds"] = np.floor(data["timestamp_seconds"] / args.window_seconds) * args.window_seconds
    aggregations: dict[str, str] = {}
    for feature in FEATURES:
        if feature == "fixation_count" or feature == "saccade_count":
            aggregations[feature] = "sum"
        elif feature == "blink_rate_per_min":
            aggregations[feature] = "mean"
        else:
            aggregations[feature] = "mean"
    if "blink_count" in data:
        data["blink_count"] = pd.to_numeric(data["blink_count"], errors="coerce")
    by = ["participant_id", "window_start_seconds"]
    output = data.groupby(by, as_index=False).agg({**aggregations, "cognitive_load_label": lambda values: values.mode().iloc[0] if not values.mode().empty else "medium"})
    if "blink_rate_per_min" in mapping and mapping["blink_rate_per_min"] in frame.columns:
        pass
    elif "blink_count" in data:
        blink_agg = data.groupby(by)["blink_count"].sum().rename("blink_count_sum").reset_index()
        output = output.merge(blink_agg, on=by, how="left")
        output["blink_rate_per_min"] = output["blink_count_sum"] * (60 / args.window_seconds)
        output = output.drop(columns=["blink_count_sum"])
    output["data_source"] = f"harmonized_from:{args.input.name}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    print(f"Wrote {len(output)} {args.window_seconds}-second windows to {args.output}")
    print("Check that labels and features have matching definitions before model training; dataset schemas are not interchangeable by default.")


if __name__ == "__main__":
    main()
