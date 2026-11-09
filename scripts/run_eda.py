from __future__ import annotations

import json
from pathlib import Path
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.generate_demo_sensor_windows import generate

FEATURES = ["pupil_diameter_mm", "fixation_count", "saccade_count", "blink_rate_per_min", "heart_rate_bpm", "rmssd_ms", "sdnn_ms"]


def read_jsonl(path: Path) -> pd.DataFrame:
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return pd.DataFrame(rows)


def main() -> None:
    output = ROOT / "results" / "eda"
    output.mkdir(parents=True, exist_ok=True)
    sensor_path = ROOT / "data" / "processed" / "harmonized_sensor_windows.csv"
    if sensor_path.exists():
        sensors = pd.read_csv(sensor_path)
        source_type = "harmonized external dataset; verify provenance and labels"
    else:
        demo_path = ROOT / "data" / "example" / "demo_sensor_windows.csv"
        if not demo_path.exists():
            demo_path.parent.mkdir(parents=True, exist_ok=True)
            generate(rows_per_class=120).to_csv(demo_path, index=False)
        sensors = pd.read_csv(demo_path)
        source_type = "SYNTHETIC DEMO ONLY — not research evidence"

    missing_features = [name for name in FEATURES if name not in sensors.columns]
    quality = {
        "source_type": source_type,
        "rows": int(len(sensors)),
        "columns": list(sensors.columns),
        "missing_feature_columns": missing_features,
        "missing_values_by_column": {str(k): int(v) for k, v in sensors.isna().sum().items()},
        "participants": int(sensors["participant_id"].nunique()) if "participant_id" in sensors else None,
        "label_distribution": {str(k): int(v) for k, v in sensors["cognitive_load_label"].value_counts(dropna=False).items()} if "cognitive_load_label" in sensors else {},
    }
    (output / "sensor_data_quality.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    numeric = sensors[[c for c in FEATURES if c in sensors.columns]].apply(pd.to_numeric, errors="coerce")
    numeric.describe().transpose().to_csv(output / "sensor_descriptive_statistics.csv")
    if "cognitive_load_label" in sensors:
        sensors["cognitive_load_label"].value_counts(dropna=False).rename_axis("load_label").reset_index(name="rows").to_csv(output / "label_distribution.csv", index=False)
        for feature in ["pupil_diameter_mm", "heart_rate_bpm", "blink_rate_per_min"]:
            if feature in sensors.columns:
                plot_data = sensors[["cognitive_load_label", feature]].dropna()
                if not plot_data.empty:
                    ax = plot_data.boxplot(column=feature, by="cognitive_load_label", grid=False, return_type="axes")
                    ax.iloc[0].set_title(f"{feature.replace('_',' ').title()} by load label")
                    ax.iloc[0].set_xlabel("Label")
                    ax.iloc[0].set_ylabel(feature.replace("_", " "))
                    plt.suptitle("")
                    plt.tight_layout()
                    plt.savefig(output / f"{feature}_by_load.png", dpi=140)
                    plt.close("all")

    events_path = ROOT / "data" / "logs" / "decision_events.jsonl"
    events = read_jsonl(events_path)
    if not events.empty:
        if "condition" in events and "decision_score" in events:
            summaries = events.groupby(["condition", "scenario_id"], dropna=False).agg(
                events=("decision_score", "size"),
                mean_score=("decision_score", "mean"),
                accuracy=("safety_correct", "mean"),
                mean_response_time_ms=("response_time_ms", "mean"),
            ).reset_index()
            summaries["interpretation"] = "prototype session summary; not a controlled study result"
            summaries.to_csv(output / "prototype_decision_summary.csv", index=False)
        events.to_csv(output / "decision_events_export.csv", index=False)
    else:
        (output / "decision_log_status.txt").write_text("No decision event log found yet. Run a prototype session to generate one.\n", encoding="utf-8")

    (output / "README.txt").write_text(
        "EDA outputs for Virtual Safety interim prototype.\n"
        f"Sensor source: {source_type}.\n"
        "If the sensor file is synthetic demo data, figures are only pipeline checks and must not be reported as research findings.\n"
        "Decision summaries contain prototype sessions only and are not controlled user-study results.\n",
        encoding="utf-8",
    )
    print(f"EDA complete: {output}")
    print(f"Sensor source: {source_type}")
    print(f"Sensor rows: {len(sensors)}")
    print(f"Decision events available: {len(events)}")


if __name__ == "__main__":
    main()
