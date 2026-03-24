using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using UDC.Classifier.Core.Models;

namespace UDC.Classifier.Core.Agents;

/// <summary>
/// Main orchestrator agent that classifies data assets and columns using Semantic Kernel.
/// Coordinates profiling, schema inference, glossary lookup, and LLM-based classification.
/// </summary>
public class ClassifierAgent
{
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of <see cref="ClassifierAgent"/>.
    /// </summary>
    /// <param name="kernel">Configured Semantic Kernel instance with registered plugins.</param>
    public ClassifierAgent(Kernel kernel)
    {
        _kernel = kernel ?? throw new ArgumentNullException(nameof(kernel));
    }

    /// <summary>
    /// Classifies all columns within a data asset and returns classification results.
    /// </summary>
    /// <param name="asset">The data asset to classify.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A list of classification results, one per column.</returns>
    public virtual async Task<List<ClassificationResult>> ClassifyAssetAsync(
        DataAsset asset,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(asset);

        var results = new List<ClassificationResult>();
        foreach (var column in asset.Columns)
        {
            var result = await ClassifyColumnAsync(column, asset, cancellationToken);
            results.Add(result);
        }
        return results;
    }

    /// <summary>
    /// Classifies a single column and returns its classification result.
    /// </summary>
    /// <param name="column">The column profile to classify.</param>
    /// <param name="assetContext">Parent asset providing contextual metadata.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Classification result for the column.</returns>
    public virtual async Task<ClassificationResult> ClassifyColumnAsync(
        ColumnProfile column,
        DataAsset assetContext,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(column);
        ArgumentNullException.ThrowIfNull(assetContext);

        var chatService = _kernel.GetRequiredService<IChatCompletionService>();

        var prompt = $$"""
            You are a data classification expert. Classify the following database column.
            Respond ONLY with a JSON object (no markdown, no explanation).

            Table: {{assetContext.QualifiedName}}
            Column: {{column.Name}}
            Data Type: {{column.DataType}}
            Nullable: {{column.IsNullable}}
            Null%: {{column.NullPercentage.ToString("F1")}}
            Unique%: {{column.UniquePercentage.ToString("F1")}}
            Sample Values: {{string.Join(", ", column.SampleValues.Take(5))}}

            JSON schema:
            {
              "classification": "<Identifier|Name|Address|Financial|Date|Metric|Code|Description|Status|Other>",
              "confidence": 0.0-1.0,
              "isPii": true or false,
              "piiType": "<Email|SSN|Phone|Address|Name|null>",
              "suggestedTags": ["tag1","tag2"],
              "rationale": "<brief explanation>"
            }
            """;

        var history = new ChatHistory();
        history.AddUserMessage(prompt);
        var response = await chatService.GetChatMessageContentAsync(history, cancellationToken: cancellationToken);
        var responseText = response.Content?.Trim() ?? "{}";

        // Strip markdown fences if present
        if (responseText.StartsWith("```"))
        {
            var firstNewline = responseText.IndexOf('\n');
            var lastFence = responseText.LastIndexOf("```");
            if (firstNewline >= 0 && lastFence > firstNewline)
                responseText = responseText[(firstNewline + 1)..lastFence].Trim();
        }

        var result = new ClassificationResult
        {
            AssetId = assetContext.Id,
            ColumnName = column.Name,
            DataType = column.DataType,
            Classification = "Unknown",
            Confidence = 0.0
        };

        try
        {
            using var doc = JsonDocument.Parse(responseText);
            var root = doc.RootElement;

            if (root.TryGetProperty("classification", out var cls))
                result.Classification = cls.GetString() ?? "Unknown";
            if (root.TryGetProperty("confidence", out var conf))
                result.Confidence = conf.GetDouble();
            if (root.TryGetProperty("isPii", out var pii))
                result.IsPii = pii.GetBoolean();
            if (root.TryGetProperty("piiType", out var piiType))
                result.PiiType = piiType.GetString();
            if (root.TryGetProperty("rationale", out var rat))
                result.Rationale = rat.GetString();
            if (root.TryGetProperty("suggestedTags", out var tags) && tags.ValueKind == JsonValueKind.Array)
            {
                foreach (var tag in tags.EnumerateArray())
                {
                    var tagStr = tag.GetString();
                    if (tagStr is not null) result.SuggestedTags.Add(tagStr);
                }
            }
        }
        catch (JsonException)
        {
            result.Rationale = $"Failed to parse LLM response: {responseText}";
        }

        return result;
    }
}
