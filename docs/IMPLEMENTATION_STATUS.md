# Interim implementation status

## Implemented in this baseline

- Browser-based fire-emergency simulation with office fire, blocked exit and smoke-filled stairwell scenarios.
- Three condition labels: desktop, fixed VR simulation and adaptive simulation.
- Branching decision graph with safety scores and corrective feedback.
- Decision latency, condition, scenario and explicitly marked load-source logging.
- Adaptive rules that can increase guidance and cue salience and reduce simulated time pressure for a manually simulated high-load input.
- Optional predictor loader for a trained scikit-learn bundle; an unvalidated heuristic fallback is also present.
- Dataset harmonization script interface, synthetic demo feature generator, grouped-validation training script, EDA output and tests.
- Session JSON export.

## Not implemented / not verified

- Unity 3D scene implementation, XR Interaction Toolkit and OpenXR headset support.
- Actual eye-tracker, Polar H10, heart-rate, ECG or Lab Streaming Layer integration.
- Downloading, inspecting, harmonizing or validating any real public VR dataset.
- A cognitive-load classifier trained on real public data or validation against the proposal's macro-F1 target.
- User recruitment, ethics approval, the 66-participant controlled study, one-week retention testing and formal learning-effectiveness claims.
- Scientific validation of the scenario scoring; the scenarios are an interim instructional prototype and require review by a competent fire-safety professional.

The app displays prototype values for software verification only. Do not use any generated data, demo-session scores or unvalidated heuristic estimates as scientific findings.
