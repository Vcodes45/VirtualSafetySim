using System;
using System.IO;
using UnityEngine;

public class SessionEventLogger : MonoBehaviour
{
    public string LogPath { get; private set; }

    private void Awake()
    {
        string directory = Path.Combine(Application.persistentDataPath, "virtual-safety-logs");
        Directory.CreateDirectory(directory);
        LogPath = Path.Combine(directory, "decision_events.jsonl");
    }

    public void AppendDecision(DecisionEventRecord record)
    {
        if (record == null) return;
        File.AppendAllText(LogPath, JsonUtility.ToJson(record) + Environment.NewLine);
    }

    public void AppendSession(SessionEventRecord record)
    {
        if (record == null) return;
        string sessionPath = Path.Combine(Path.GetDirectoryName(LogPath), "sessions.jsonl");
        File.AppendAllText(sessionPath, JsonUtility.ToJson(record) + Environment.NewLine);
    }
}
