# Unity / XR starter integration

This folder adds the next implementation path required by the research proposal. The Python/FastAPI browser prototype is the immediately runnable interim application; these C# scripts are a compile-oriented starter layer for the intended Unity scenario runtime.

## Setup in Unity

1. Create a Unity 2022.3 LTS or later project.
2. Install XR Interaction Toolkit and OpenXR Plugin using Package Manager when the target headset is available. Complete Unity's XR Plug-in Management setup for the selected headset.
3. Copy `Assets/Scripts/` into the Unity project's `Assets/Scripts/` directory.
4. Copy `StreamingAssets/scenarios.json` into the project's `Assets/StreamingAssets/scenarios.json`.
5. Create an active GameObject and add `ScenarioCatalog`, `AdaptiveGuidanceController`, `CognitiveLoadEstimatorBridge`, `SessionEventLogger`, and `VirtualSafetyScenarioManager` components. Assign the four component references on the manager in the Inspector.
6. Connect a UI layer to `DecisionShown`, `FeedbackShown` and `SessionCompleted`. Use `CurrentDecision.options` to create buttons and call `SubmitDecision(option.id, responseTimeMs)` when a choice is made.
7. For an interim check, invoke `StartScenario("office_fire", TrainingCondition.AdaptiveVR, "demo-001")` from your scene's UI controller. Other scenario IDs are `blocked_exit` and `smoke_stairwell`.

The JSON file was converted from the Python prototype's scenario catalogue to a Unity `JsonUtility`-compatible list schema. Keep both versions synchronized if the scenarios change.

## What this is not

- These scripts do not implement 3D environments, tracked XR controllers, gaze tracking, Polar H10/LSL integration or a trained ML inference runtime.
- `CognitiveLoadEstimatorBridge` is a placeholder. Its rule-based estimate is unvalidated and the manual demo input should remain active until a real, validated data/model integration is ready.
- `ScenarioCatalog` uses `File.ReadAllText` from StreamingAssets and is aimed at an interim desktop/editor test. Mobile/console StreamingAssets often requires platform-specific asynchronous loading.
- The scenario score and safety content require review by competent safety personnel before any real-world training use.
