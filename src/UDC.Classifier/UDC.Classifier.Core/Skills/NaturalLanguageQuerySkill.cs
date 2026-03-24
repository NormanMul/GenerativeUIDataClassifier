using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace UDC.Classifier.Core.Skills;

/// <summary>
/// Semantic Kernel plugin for translating natural-language queries
/// into SQL or DAX expressions.
/// </summary>
public sealed class NaturalLanguageQuerySkill
{
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of <see cref="NaturalLanguageQuerySkill"/>.
    /// </summary>
    /// <param name="kernel">Configured Semantic Kernel instance.</param>
    public NaturalLanguageQuerySkill(Kernel kernel)
    {
        _kernel = kernel ?? throw new ArgumentNullException(nameof(kernel));
    }
    /// <summary>
    /// Translates a natural-language question into a SQL query.
    /// </summary>
    /// <param name="question">Natural-language question.</param>
    /// <param name="schemaJson">JSON description of the target schema.</param>
    /// <returns>Generated SQL query string.</returns>
    [KernelFunction, Description("Translate natural language to SQL.")]
    public async Task<string> TranslateToSQLAsync(
        [Description("Natural language question")] string question,
        [Description("Target schema as JSON")] string schemaJson)
    {
        var chatService = _kernel.GetRequiredService<IChatCompletionService>();

        var prompt = $"""        
            You are a SQL expert. Translate the following natural-language question into a SQL query.
            Use only standard SQL syntax. Do NOT include markdown formatting.
            Return ONLY the SQL query, nothing else.

            Database schema:
            {schemaJson}

            Question: {question}
            """;

        var history = new ChatHistory();
        history.AddUserMessage(prompt);
        var response = await chatService.GetChatMessageContentAsync(history);
        var sql = response.Content?.Trim() ?? string.Empty;

        // Strip markdown code fences if present
        if (sql.StartsWith("```"))
        {
            var firstNl = sql.IndexOf('\n');
            var lastFence = sql.LastIndexOf("```");
            if (firstNl >= 0 && lastFence > firstNl)
                sql = sql[(firstNl + 1)..lastFence].Trim();
        }

        return sql;
    }

    /// <summary>
    /// Translates a natural-language question into a DAX expression for Power BI.
    /// </summary>
    /// <param name="question">Natural-language question.</param>
    /// <param name="modelJson">JSON description of the semantic model.</param>
    /// <returns>Generated DAX expression.</returns>
    [KernelFunction, Description("Translate natural language to DAX.")]
    public async Task<string> TranslateToDAXAsync(
        [Description("Natural language question")] string question,
        [Description("Semantic model as JSON")] string modelJson)
    {
        var chatService = _kernel.GetRequiredService<IChatCompletionService>();

        var prompt = $"""        
            You are a Power BI DAX expert. Translate the following natural-language question
            into a DAX expression. Do NOT include markdown formatting.
            Return ONLY the DAX expression, nothing else.

            Semantic model:
            {modelJson}

            Question: {question}
            """;

        var history = new ChatHistory();
        history.AddUserMessage(prompt);
        var response = await chatService.GetChatMessageContentAsync(history);
        var dax = response.Content?.Trim() ?? string.Empty;

        if (dax.StartsWith("```"))
        {
            var firstNl = dax.IndexOf('\n');
            var lastFence = dax.LastIndexOf("```");
            if (firstNl >= 0 && lastFence > firstNl)
                dax = dax[(firstNl + 1)..lastFence].Trim();
        }

        return dax;
    }
}
