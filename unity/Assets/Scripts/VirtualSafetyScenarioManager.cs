using System;
using System.Collections.Generic;
using UnityEngine;

public class VirtualSafetyScenarioManager : MonoBehaviour
{
    public ScenarioCatalog scenarioCatalog;
    public AdaptiveGuidanceController adaptationController;
    public CognitiveLoadEstimatorBridge loadEstimator;
    public SessionEventLogger eventLogger;

    public event Action<DecisionNodeData, string> DecisionShown;
    public event Action<string, bool> FeedbackShown;
    public event Action<string> SessionCompleted;

    public ScenarioData CurrentScenario { get; private set; }
    public DecisionNodeData CurrentDecision { get; private set; }
    public AdaptationState CurrentAdaptation { get; private set; }
    public TrainingCondition CurrentCondition { get; private set; }
    public string SessionId { get; private set; }
    public string ParticipantCode { get; private set; }
    public int Score { get; private set; }
    public int DecisionCount { get; private set; }
    public int CorrectCount { get; private set; }
    public bool IsComplete { get; private set; }

    private readonly Dictionary<string, DecisionNodeData> decisions = new Dictionary<string, DecisionNodeData>();
    private float decisionShownAt;

    public void StartScenario(string scenarioId, TrainingCondition condition, string participantCode = "")
    {
        if (scenarioCatalog == null || adaptationController == null || loadEstimator == null || eventLogger == null)
            throw new InvalidOperationException("Assign ScenarioCatalog, AdaptiveGuidanceController, CognitiveLoadEstimatorBridge and SessionEventLogger components first.");

        if (scenarioCatalog.Catalog == null) scenarioCatalog.LoadFromStreamingAssets();
        CurrentScenario = scenarioCatalog.Find(scenarioId);
        if (CurrentScenario == null) throw new ArgumentException("Unknown scenario id: " + scenarioId);

        decisions.Clear();
        foreach (DecisionNodeData node in CurrentScenario.decisions) decisions[node.id] = node;
        if (!decisions.ContainsKey(CurrentScenario.startDecisionId)) throw new InvalidOperationException("Scenario start decision is missing.");

        CurrentCondition = condition;
        ParticipantCode = SanitizeCode(string.IsNullOrWhiteSpace(participantCode) ? "demo" : participantCode);
        SessionId = Guid.NewGuid().ToString("N");
        Score = 0;
        DecisionCount = 0;
        CorrectCount = 0;
        IsComplete = false;
        CurrentDecision = decisions[CurrentScenario.startDecisionId];
        CurrentAdaptation = adaptationController.Evaluate(condition, CognitiveLoadBand.Medium, "neutral_fallback");
        eventLogger.AppendSession(new SessionEventRecord {
            timestampUtc = DateTime.UtcNow.ToString("o"), eventType = "session_started", sessionId = SessionId,
            participantCode = ParticipantCode, scenarioId = CurrentScenario.id, condition = CurrentCondition.ToString(),
            status = "active", decisionCount = 0, correctCount = 0, score = 0
        });
        PublishDecision();
    }

    public void SubmitDecision(string choiceId, float responseTimeMs, SensorFeatureFrame features = null)
    {
        if (IsComplete || CurrentDecision == null) throw new InvalidOperationException("There is no active decision.");
        DecisionOptionData chosen = null;
        foreach (DecisionOptionData option in CurrentDecision.options)
            if (string.Equals(option.id, choiceId, StringComparison.Ordinal)) { chosen = option; break; }
        if (chosen == null) throw new ArgumentException("Choice does not belong to current decision.");

        if (responseTimeMs <= 0f) responseTimeMs = Mathf.Max(0f, (Time.realtimeSinceStartup - decisionShownAt) * 1000f);
        string loadSource;
        CognitiveLoadBand load = loadEstimator.Estimate(features, out loadSource);
        CurrentAdaptation = adaptationController.Evaluate(CurrentCondition, load, loadSource);
        Score += chosen.score;
        DecisionCount++;
        bool safetyCorrect = chosen.score >= 2;
        if (safetyCorrect) CorrectCount++;

        eventLogger.AppendDecision(new DecisionEventRecord {
            timestampUtc = DateTime.UtcNow.ToString("o"), sessionId = SessionId, participantCode = ParticipantCode,
            scenarioId = CurrentScenario.id, condition = CurrentCondition.ToString(), decisionId = CurrentDecision.id,
            choiceId = chosen.id, decisionScore = chosen.score, safetyCorrect = safetyCorrect,
            responseTimeMs = Mathf.Max(0, responseTimeMs), loadLabel = load.ToString().ToLowerInvariant(),
            loadSource = loadSource, syntheticInput = features == null || features.isSynthetic || loadSource == "simulated_manual_demo",
            adaptationMessage = CurrentAdaptation.message
        });
        FeedbackShown?.Invoke(chosen.feedback, safetyCorrect);

        if (string.IsNullOrEmpty(chosen.nextDecisionId))
        {
            IsComplete = true;
            CurrentDecision = null;
            eventLogger.AppendSession(new SessionEventRecord {
                timestampUtc = DateTime.UtcNow.ToString("o"), eventType = "session_completed", sessionId = SessionId,
                participantCode = ParticipantCode, scenarioId = CurrentScenario.id, condition = CurrentCondition.ToString(),
                status = "completed", decisionCount = DecisionCount, correctCount = CorrectCount, score = Score
            });
            SessionCompleted?.Invoke("Completed " + CurrentScenario.title + ". Correct choices: " + CorrectCount + "/" + DecisionCount + ". Prototype data only.");
            return;
        }

        DecisionNodeData nextDecision;
        if (!decisions.TryGetValue(chosen.nextDecisionId, out nextDecision))
            throw new InvalidOperationException("Next decision was not found: " + chosen.nextDecisionId);
        CurrentDecision = nextDecision;
        PublishDecision();
    }

    public string CurrentHint
    {
        get
        {
            if (CurrentDecision == null) return string.Empty;
            if (CurrentCondition != TrainingCondition.AdaptiveVR || (CurrentAdaptation != null && CurrentAdaptation.guidanceLevel == "high"))
                return CurrentDecision.hint;
            return string.Empty;
        }
    }

    private void PublishDecision()
    {
        decisionShownAt = Time.realtimeSinceStartup;
        DecisionShown?.Invoke(CurrentDecision, CurrentHint);
    }

    private string SanitizeCode(string value)
    {
        string clean = "";
        foreach (char c in value)
            if (char.IsLetterOrDigit(c) || c == '-' || c == '_') clean += c;
        return string.IsNullOrWhiteSpace(clean) ? "demo" : clean.Substring(0, Math.Min(40, clean.Length));
    }
}
