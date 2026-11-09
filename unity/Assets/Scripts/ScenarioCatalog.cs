using System;
using System.IO;
using UnityEngine;

public class ScenarioCatalog : MonoBehaviour
{
    public ScenarioCatalogData Catalog { get; private set; }

    public void LoadFromStreamingAssets()
    {
        string path = Path.Combine(Application.streamingAssetsPath, "scenarios.json");
        if (!File.Exists(path))
            throw new FileNotFoundException("Scenario file was not found. Copy scenarios.json into Assets/StreamingAssets.", path);

        string json = File.ReadAllText(path);
        Catalog = JsonUtility.FromJson<ScenarioCatalogData>(json);
        if (Catalog == null || Catalog.scenarios == null || Catalog.scenarios.Length == 0)
            throw new InvalidDataException("Scenario catalog is empty or has an invalid format.");

        foreach (ScenarioData scenario in Catalog.scenarios)
        {
            if (scenario.decisions == null || scenario.decisions.Length == 0)
                throw new InvalidDataException("Scenario has no decisions: " + scenario.id);
        }
    }

    public ScenarioData Find(string scenarioId)
    {
        if (Catalog == null || Catalog.scenarios == null) return null;
        foreach (ScenarioData scenario in Catalog.scenarios)
            if (string.Equals(scenario.id, scenarioId, StringComparison.OrdinalIgnoreCase)) return scenario;
        return null;
    }
}
