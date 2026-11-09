using System;

[Serializable]
public class ScenarioCatalogData
{
    public ScenarioData[] scenarios;
}

[Serializable]
public class ScenarioData
{
    public string id;
    public string title;
    public string description;
    public string environment;
    public string learningNote;
    public string startDecisionId;
    public DecisionNodeData[] decisions;
}

[Serializable]
public class DecisionNodeData
{
    public string id;
    public string title;
    public string prompt;
    public string hint;
    public DecisionOptionData[] options;
}

[Serializable]
public class DecisionOptionData
{
    public string id;
    public string label;
    public int score;
    public string feedback;
    public string nextDecisionId;
}

public enum TrainingCondition
{
    Desktop,
    FixedVR,
    AdaptiveVR
}

public enum CognitiveLoadBand
{
    Low,
    Medium,
    High
}

[Serializable]
public class SensorFeatureFrame
{
    public float pupilDiameterMm;
    public float fixationCount;
    public float saccadeCount;
    public float blinkRatePerMin;
    public float heartRateBpm;
    public float rmssdMs;
    public float sdnnMs;
    public bool isSynthetic;
}

[Serializable]
public class AdaptationState
{
    public bool enabled;
    public string loadLabel;
    public string loadSource;
    public string guidanceLevel;
    public string cueSalience;
    public string timePressure;
    public string message;
}

[Serializable]
public class DecisionEventRecord
{
    public string timestampUtc;
    public string sessionId;
    public string participantCode;
    public string scenarioId;
    public string condition;
    public string decisionId;
    public string choiceId;
    public int decisionScore;
    public bool safetyCorrect;
    public float responseTimeMs;
    public string loadLabel;
    public string loadSource;
    public bool syntheticInput;
    public string adaptationMessage;
}

[Serializable]
public class SessionEventRecord
{
    public string timestampUtc;
    public string eventType;
    public string sessionId;
    public string participantCode;
    public string scenarioId;
    public string condition;
    public string status;
    public int decisionCount;
    public int correctCount;
    public int score;
}
