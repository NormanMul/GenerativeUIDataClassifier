using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace UDC.Classifier.Core.Skills;

/// <summary>
/// Semantic Kernel plugin for inferring schemas from raw data
/// and detecting relationships between tables.
/// </summary>
public sealed class SchemaInferenceSkill
{
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of <see cref="SchemaInferenceSkill"/>.
    /// </summary>
    /// <param name="kernel">Configured Semantic Kernel instance.</param>
    public SchemaInferenceSkill(Kernel kernel)
    {
        _kernel = kernel ?? throw new ArgumentNullException(nameof(kernel));
    }
    /// <summary>
    /// Infers the schema of a dataset from sample data or metadata.
    /// </summary>
    /// <param name="sampleData">Serialized sample data (JSON or CSV fragment).</param>
    /// <returns>Inferred schema definition as JSON.</returns>
    [KernelFunction, Description("Infer schema from sample data.")]
    public async Task<string> InferSchemaAsync(
        [Description("Sample data as JSON or CSV")] string sampleData)
    {
        var chatService = _kernel.GetRequiredService<IChatCompletionService>();

        var prompt = $$"""
            You are a data schema inference expert. Analyze the following sample data
            and infer the schema including column names, data types, nullability,
            and any detected patterns. Respond ONLY with JSON (no markdown).

            Sample data:
            {{sampleData}}

            Return JSON in this format:
            {
              "columns": [
                {
                  "name": "column_name",
                  "inferredType": "string|integer|decimal|boolean|datetime|email|phone|uuid",
                  "nullable": true,
                  "isPrimaryKey": false,
                  "description": "brief description"
                }
              ],
              "rowCount": 0,
              "notes": "any observations"
            }
            """;

        var history = new ChatHistory();
        history.AddUserMessage(prompt);
        var response = await chatService.GetChatMessageContentAsync(history);
        var text = response.Content?.Trim() ?? "{}";

        if (text.StartsWith("```"))
        {
            var firstNl = text.IndexOf('\n');
            var lastFence = text.LastIndexOf("```");
            if (firstNl >= 0 && lastFence > firstNl)
                text = text[(firstNl + 1)..lastFence].Trim();
        }

        return text;
    }

    /// <summary>
    /// Detects foreign-key and join relationships between tables.
    /// </summary>
    /// <param name="schemasJson">JSON array of table schemas to analyze.</param>
    /// <returns>Detected relationships as JSON.</returns>
    [KernelFunction, Description("Detect relationships between tables.")]
    public async Task<string> DetectRelationshipsAsync(
        [Description("JSON array of table schemas")] string schemasJson)
    {
        var chatService = _kernel.GetRequiredService<IChatCompletionService>();

        var prompt = $$"""
            You are a database relationship detection expert. Analyze the following table schemas
            and detect foreign-key/join relationships between them based on column names,
            types, and naming conventions (e.g., order_id in one table likely references id in orders).
            Respond ONLY with JSON (no markdown).

            Table schemas:
            {{schemasJson}}

            Return JSON array:
            [
              {
                "sourceTable": "table_name",
                "sourceColumn": "column_name",
                "targetTable": "referenced_table",
                "targetColumn": "referenced_column",
                "relationship": "many-to-one|one-to-one|many-to-many",
                "confidence": 0.95
              }
            ]
            """;

        var history = new ChatHistory();
        history.AddUserMessage(prompt);
        var response = await chatService.GetChatMessageContentAsync(history);
        var text = response.Content?.Trim() ?? "[]";

        if (text.StartsWith("```"))
        {
            var firstNl = text.IndexOf('\n');
            var lastFence = text.LastIndexOf("```");
            if (firstNl >= 0 && lastFence > firstNl)
                text = text[(firstNl + 1)..lastFence].Trim();
        }

        return text;
    }
}
