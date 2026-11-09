using UnityEngine;

public class AdaptiveGuidanceController : MonoBehaviour
{
    public AdaptationState Evaluate(TrainingCondition condition, CognitiveLoadBand loadBand, string loadSource)
    {
        if (condition != TrainingCondition.AdaptiveVR)
        {
            return new AdaptationState
            {
                enabled = false,
                loadLabel = loadBand.ToString().ToLowerInvariant(),
                loadSource = loadSource,
                guidanceLevel = "fixed",
                cueSalience = "fixed",
                timePressure = "fixed",
                message = "Fixed presentation condition; adaptive guidance is disabled."
            };
        }

        if (loadBand == CognitiveLoadBand.High)
        {
            return new AdaptationState
            {
                enabled = true,
                loadLabel = "high",
                loadSource = loadSource,
                guidanceLevel = "high",
                cueSalience = "high",
                timePressure = "reduced",
                message = "Prototype adaptation: show an explicit safety hint, emphasize the safe-route cue and reduce simulated time pressure."
            };
        }

        if (loadBand == CognitiveLoadBand.Low)
        {
            return new AdaptationState
            {
                enabled = true,
                loadLabel = "low",
                loadSource = loadSource,
                guidanceLevel = "standard",
                cueSalience = "standard",
                timePressure = "normal",
                message = "Prototype adaptation: keep all critical safety cues visible and offer a reflection prompt."
            };
        }

        return new AdaptationState
        {
            enabled = true,
            loadLabel = "medium",
            loadSource = loadSource,
            guidanceLevel = "standard",
            cueSalience = "enhanced",
            timePressure = "normal",
            message = "Prototype adaptation: preserve normal time pressure and emphasize essential safety cues."
        };
    }
}
