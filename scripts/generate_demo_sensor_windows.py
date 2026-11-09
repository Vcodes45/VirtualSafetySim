from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["pupil_diameter_mm", "fixation_count", "saccade_count", "blink_rate_per_min", "heart_rate_bpm", "rmssd_ms", "sdnn_ms"]


def generate(rows_per_class: int = 150, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records = []
    for label, means in {
        "low": [3.2, 18, 22, 14, 72, 46, 58],
        "medium": [4.3, 25, 30, 20, 88, 34, 45],
        "high": [5.4, 33, 38, 28, 108, 24, 34],
    }.items():
        scales = [0.45, 5, 6, 5, 12, 10, 12]
        values = rng.normal(loc=means, scale=scales, size=(rows_per_class, len(FEATURES)))
        limits = [(1.0, 8.0), (0, None), (0, None), (0, 100), (35, 180), (1, 200), (1, 250)]
        for col_idx, (low, high) in enumerate(limits):
            if low is not None:
                values[:, col_idx] = np.maximum(values[:, col_idx], low)
            if high is not None:
                values[:, col_idx] = np.minimum(values[:, col_idx], high)
        for index, row in enumerate(values):
            records.append({
                "participant_id": f"DEMO-{(index % max(3, rows_per_class // 10)) + 1:03d}",
                "window_start_seconds": float(index * 10),
                **{feature: float(value) for feature, value in zip(FEATURES, row)},
                "cognitive_load_label": label,
                "data_source": "synthetic_demo_only",
            })
    frame = pd.DataFrame(records)
    return frame.sample(frac=1, random_state=seed).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create synthetic sensor windows for pipeline smoke tests only.")
    parser.add_argument("--rows-per-class", type=int, default=150)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "example" / "demo_sensor_windows.csv")
    args = parser.parse_args()
    if args.rows_per_class < 5:
        parser.error("--rows-per-class must be at least 5")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame = generate(args.rows_per_class, args.seed)
    frame.to_csv(args.output, index=False)
    print(f"Created {len(frame)} synthetic DEMO rows: {args.output}")
    print("These data are fabricated for code testing and must not be used as research evidence.")


if __name__ == "__main__":
    main()
