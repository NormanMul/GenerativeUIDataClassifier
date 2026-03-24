using System.Text;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using UDC.Classifier.Core.Models;

namespace UDC.Classifier.Core.Agents;

/// <summary>
/// Use Case 2 agent — automatically documents ETL/ELT pipelines,
/// extracts lineage information, and generates pipeline reports.
/// </summary>
public class PipelineDocAgent
{
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of <see cref="PipelineDocAgent"/>.
    /// </summary>
    /// <param name="kernel">Configured Semantic Kernel instance.</param>
    public PipelineDocAgent(Kernel kernel)
    {
        _kernel = kernel ?? throw new ArgumentNullException(nameof(kernel));
    }

    /// <summary>
    /// Generates documentation for a pipeline based on its metadata.
    /// </summary>
    /// <param name="pipeline">Pipeline metadata to document.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Generated documentation as a string.</returns>
    public virtual async Task<string> DocumentPipelineAsync(
        PipelineMetadata pipeline,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(pipeline);

        var chatService = _kernel.GetRequiredService<IChatCompletionService>();
        var lineage = await ExtractLineageAsync(pipeline, cancellationToken);

        var prompt = $"""        
            You are a data engineering documentation expert.
            Generate comprehensive documentation for the following ETL/ELT pipeline.

            Pipeline Name: {pipeline.PipelineName}
            Status: {pipeline.Status}
            Steps: {string.Join(" -> ", pipeline.Steps)}
            Started: {pipeline.StartedAt?.ToString("o") ?? "N/A"}
            Completed: {pipeline.CompletedAt?.ToString("o") ?? "N/A"}

            Lineage:
            {lineage}

            Generate a structured document with these sections:
            1. Overview
            2. Pipeline Steps (describe each step)
            3. Data Lineage (source -> target mappings)
            4. Dependencies
            5. Notes and Recommendations
            """;

        var history = new ChatHistory();
        history.AddUserMessage(prompt);
        var response = await chatService.GetChatMessageContentAsync(history, cancellationToken: cancellationToken);
        return response.Content ?? string.Empty;
    }

    /// <summary>
    /// Extracts data lineage from a pipeline's transformation steps.
    /// </summary>
    /// <param name="pipeline">Pipeline metadata to analyze.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Lineage graph as a serialized string.</returns>
    public virtual Task<string> ExtractLineageAsync(
        PipelineMetadata pipeline,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(pipeline);

        var sb = new StringBuilder();
        var tablePattern = new Regex(
            @"(?:FROM|JOIN|INTO|UPDATE|MERGE\s+INTO)\s+([A-Za-z_][\w.]*)",
            RegexOptions.IgnoreCase);

        for (int i = 0; i < pipeline.Steps.Count; i++)
        {
            var step = pipeline.Steps[i];
            var matches = tablePattern.Matches(step);
            var tables = matches.Select(m => m.Groups[1].Value).Distinct().ToList();

            sb.AppendLine($"Step {i + 1}: {step}");
            if (tables.Count > 0)
                sb.AppendLine($"  Referenced tables: {string.Join(", ", tables)}");
            if (i > 0)
                sb.AppendLine($"  Flow: Step {i} -> Step {i + 1}");
        }

        return Task.FromResult(sb.ToString());
    }

    /// <summary>
    /// Generates a comprehensive report for pipeline execution.
    /// </summary>
    /// <param name="pipeline">Pipeline metadata to report on.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Formatted report string.</returns>
    public virtual async Task<string> GenerateReportAsync(
        PipelineMetadata pipeline,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(pipeline);

        var chatService = _kernel.GetRequiredService<IChatCompletionService>();
        var documentation = await DocumentPipelineAsync(pipeline, cancellationToken);

        var prompt = $"""        
            Convert the following pipeline documentation into a well-formatted HTML report.
            Use clean HTML5 with inline CSS for styling. Include a header, table of contents,
            and styled sections. Use a professional blue/gray color scheme.

            Pipeline: {pipeline.PipelineName}
            Documentation:
            {documentation}
            """;

        var history = new ChatHistory();
        history.AddUserMessage(prompt);
        var response = await chatService.GetChatMessageContentAsync(history, cancellationToken: cancellationToken);
        return response.Content ?? "<html><body><p>No report generated.</p></body></html>";
    }
}
