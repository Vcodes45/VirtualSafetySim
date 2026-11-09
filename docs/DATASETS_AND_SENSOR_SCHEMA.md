# Dataset sources and harmonized sensor-window schema

This document reflects the datasets named in the research proposal. No public dataset is downloaded automatically. Dataset availability, access conditions, consent constraints and schema differences must be checked before use.

## Public sources named in the proposal

1. **Pina et al. (2025), VR cognitive-load biosignals** — https://graphics.unizar.es/projects/CL_Biosignals/ . The project page describes 36 users across high/low load and 90-degree/360-degree visual-search conditions and includes ECG, respiration, EDA, PPG, gaze, pupil size, performance data and questionnaires. Suitable as one candidate pre-training source, but the file schemas and label definition must be inspected before mapping.
2. **VRWalking / Setu et al. (2024)** — https://arxiv.org/abs/2409.06898 . The proposal describes it as including 39 participants and signals/labels relating to mental load, physical load, attention and cybersickness. Do not assume its labels are interchangeable with the Pina dataset's labels.
3. **HP Omnicept Cognitive Load Database (HPO-CLD)** — https://developers.hp.com/node/21981 . The proposal lists this as a potential larger sample with pupillometry, eye tracking, PPG and self-reported load. Confirm that the page and access conditions remain available before use.
4. **Official fire-safety planning context (UK)** — https://www.gov.uk/workplace-fire-safety-your-responsibilities/fire-safety-and-evacuation-plans and https://www.gov.uk/government/publications/fire-safety-risk-assessment-offices-and-shops/fire-safety-risk-assessment-offices-and-shops-accessible . Scenario content must remain illustrative and be checked against competent guidance and site-specific plans.

## Canonical 10-second window CSV

The initial training script expects one row per participant and 10-second window, with these columns:

- `participant_id` — pseudonymous participant/group identifier used for subject-independent validation.
- `window_start_seconds` — time offset of the window, when available.
- `pupil_diameter_mm`
- `fixation_count`
- `saccade_count`
- `blink_rate_per_min`
- `heart_rate_bpm`
- `rmssd_ms`
- `sdnn_ms`
- `cognitive_load_label` — normalized to `low`, `medium` or `high`.
- `data_source` — provenance label.

The proposal describes features over 10-second windows. A source that has only some of these channels should retain missing values rather than fabricate measurements. The interim classifier handles missing values through a training pipeline, but the dataset mapping must still be methodologically justified.

## Mapping an original CSV

`scripts/harmonize_sensor_windows.py` accepts explicit source-column mappings. Example only — replace column names with the ones found in your downloaded file:

```bash
python scripts/harmonize_sensor_windows.py \
  --input data/raw/source_export.csv \
  --column-map-json '{"participant_id":"participant","timestamp":"timestamp_seconds","cognitive_load_label":"condition","pupil_diameter_mm":"pupil_mm","heart_rate_bpm":"heart_rate","fixation_count":"fixations","saccade_count":"saccades","blink_count":"blinks"}' \
  --label-map-json '{"low load":"low","high load":"high"}' \
  --output data/processed/harmonized_sensor_windows.csv
```

This command is an example of the mapping interface, not an assertion that those exact source columns exist in a published dataset. Inspect the source README and configure correct label mapping, units, clock alignment and aggregation before use. Never mix participant-level labels from one dataset with sensor values from another without a documented matching protocol.

## Demo data warning

`scripts/generate_demo_sensor_windows.py` can create synthetic sensor rows to validate software plumbing. These rows are fabricated. Any model trained on them is marked `demo_only` and must not be reported as research evidence or as a validated cognitive-load detector.
