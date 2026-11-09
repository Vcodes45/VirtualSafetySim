using UnityEngine;

public class CognitiveLoadEstimatorBridge : MonoBehaviour
{
    [Header("Prototype switch only; no real headset sensor is connected by this script")]
    public bool useManualDemoInput = true;
    public CognitiveLoadBand manualDemoLoad = CognitiveLoadBand.Medium;

    public CognitiveLoadBand Estimate(SensorFeatureFrame features, out string source)
    {
        if (useManualDemoInput || features == null || features.isSynthetic)
        {
            source = "simulated_manual_demo";
            return manualDemoLoad;
        }

        // Unvalidated placeholder rule. Replace with a model trained and evaluated on mapped data.
        int score = 0;
        int observed = 0;
        if (features.pupilDiameterMm > 0)
        {
            observed++;
            if (features.pupilDiameterMm >= 5.5f) score += 2;
            else if (features.pupilDiameterMm >= 4.5f) score++;
        }
        if (features.blinkRatePerMin > 0)
        {
            observed++;
            if (features.blinkRatePerMin >= 25) score += 2;
            else if (features.blinkRatePerMin >= 10) score++;
        }
        if (features.heartRateBpm > 0)
        {
            observed++;
            if (features.heartRateBpm >= 110) score += 2;
            else if (features.heartRateBpm >= 85) score++;
        }
        source = "unvalidated_heuristic";
        if (observed == 0 || score < 2) return CognitiveLoadBand.Low;
        if (score >= 4) return CognitiveLoadBand.High;
        return CognitiveLoadBand.Medium;
    }
}
