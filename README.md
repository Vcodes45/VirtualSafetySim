# Virtual Safety — Interim Code (Project B)

A first runnable prototype for **Virtual Simulation for Safety-Critical Training: A Human-Centred Approach to Decision-Making and Learning**.

It follows the proposal's interim direction: three branching fire-emergency scenarios, desktop/fixed/adaptive conditions, decision accuracy and response-latency logging, a demo adaptation policy, and a pipeline scaffold for cognitive-load data.

> **Important limits:** This is a browser-based interim prototype. It is not a Unity/OpenXR headset application, no eye tracker or heart-rate device is connected, and the adaptive load input defaults to a manually simulated label. The built-in heuristic is unvalidated. Scoring and scenario language require review by a competent fire-safety professional. Do not use this as real emergency guidance or claim that it demonstrates training effectiveness.

## Included now

- FastAPI app plus responsive browser UI.
- Three scenarios: office fire, blocked exit, smoke-filled stairwell.
- Branching choices, corrective feedback, a score, and browser-measured response latency.
- Three prototype conditions: Desktop, Fixed VR Simulation, Adaptive Simulation.
- Adaptive rule that can show additional guidance and increase safety-cue salience on simulated high cognitive load, while reducing simulated time pressure.
- Session and decision JSONL logs under `data/logs/` and one-session JSON export.
- Dataset source documentation, sensor CSV harmonization, demo data generation, baseline classifier training and EDA scripts.
- Unit/API tests.

## Run locally (Mac/Linux)

```bash
cd virtual-safety-interim
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. API documentation is at <http://127.0.0.1:8000/docs> and health is at <http://127.0.0.1:8000/api/health>.

If `uvicorn` reports an import error, run the commands from the project root (the folder containing `app/`, `data/`, `static/` and `requirements.txt`).

## Run tests

```bash
pytest -q
```

These tests verify app routes, scenario flow, response logging and the explicit simulated-load label. They do not establish the efficacy of the training method or validate a cognitive-load model.

## Run EDA

```bash
python scripts/run_eda.py
```

The script uses `data/processed/harmonized_sensor_windows.csv` when present. Otherwise it generates/uses synthetic demo rows from `data/example/`. Reports and figures go to `results/eda/`. EDA from synthetic data is strictly a software smoke test, not research evidence.

After running a session in the browser, run EDA again to generate a prototype decision summary from `data/logs/decision_events.jsonl`.

## Dataset work

The proposal names three possible public VR sources. Links and harmonization expectations are in [`docs/DATASETS_AND_SENSOR_SCHEMA.md`](docs/DATASETS_AND_SENSOR_SCHEMA.md):

- Pina et al. VR cognitive-load biosignals: <https://graphics.unizar.es/projects/CL_Biosignals/>
- VRWalking / Setu et al.: <https://arxiv.org/abs/2409.06898>
- HP Omnicept Cognitive Load Database: <https://developers.hp.com/node/21981>

No dataset is downloaded by this code. Inspect the dataset's own README and license/access conditions, then create a column mapping for the files you actually obtain.

Example:

```bash
python scripts/harmonize_sensor_windows.py \
  --input data/raw/source_export.csv \
  --column-map-json '{"participant_id":"participant","timestamp":"timestamp_seconds","cognitive_load_label":"condition","pupil_diameter_mm":"pupil_mm","heart_rate_bpm":"heart_rate","fixation_count":"fixations","saccade_count":"saccades","blink_count":"blinks"}' \
  --label-map-json '{"low load":"low","high load":"high"}' \
  --output data/processed/harmonized_sensor_windows.csv
```

The column names in this example are examples only. Adjust them to the actual source CSV. Verify units, time bases, labels and grouping before training. The helper builds 10-second windows; datasets with different collection semantics are not interchangeable by default.

## Train/evaluate a baseline model

After creating a harmonized dataset containing `participant_id`, the seven listed feature columns and `cognitive_load_label` (`low`, `medium`, `high`):

```bash
python scripts/train_load_model.py --input data/processed/harmonized_sensor_windows.csv
```

The script compares Logistic Regression and Random Forest using Leave-One-Group-Out validation by participant, prints macro-F1, accuracy, balanced accuracy and approximate prediction time, then saves a model bundle and evaluation JSON under `models/`.

Synthetic demo data can only be used when explicitly opted into:

```bash
python scripts/generate_demo_sensor_windows.py
python scripts/train_load_model.py --input data/example/demo_sensor_windows.csv --allow-demo-data
```

**A model trained using synthetic demo rows is marked `demo_only`. Its scores must never be cited as cognitive-load recognition performance.** The model-loading API can load a compatible model bundle, but the loaded model requires independent validation before research use.

## Logs and privacy

- `data/logs/decision_events.jsonl`: one decision per line.
- `data/logs/sessions.jsonl`: session-start and session-completion events.
- A completed session can also be downloaded from the browser as a JSON file.

Use pseudonymous participant codes only. The interim app records manual simulated load labels by default and does not integrate physiological hardware. Do not collect study-participant or health/biometric data until the required ethics approval, consent, retention, security and withdrawal procedures are in place. Logs are local development artefacts and are excluded from Git by `.gitignore`.

## Proposal requirements not yet delivered

- Unity 3D environment, XR Interaction Toolkit and OpenXR.
- Eye-tracker / Polar H10 / Lab Streaming Layer hardware integration.
- Real-data cognitive-load training and macro-F1 target validation.
- Ethics-approved co-design and participant study, 66-person between-subjects experiment, and one-week retention test.
- Full statistical analysis of controlled experiment results and expert validation of scenario scores.

See [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md) for the exact interim scope.
