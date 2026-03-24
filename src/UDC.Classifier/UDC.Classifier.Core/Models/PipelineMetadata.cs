namespace UDC.Classifier.Core.Models;

/// <summary>
/// Metadata describing an ETL/ELT pipeline and its execution state.
/// </summary>
public sealed class PipelineMetadata
{
    /// <summary>Unique identifier for the pipeline.</summary>
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>Name of the pipeline.</summary>
    public required string PipelineName { get; set; }

    /// <summary>Ordered list of pipeline step names.</summary>
    public List<string> Steps { get; set; } = [];

    /// <summary>Current execution status (e.g., Pending, Running, Succeeded, Failed).</summary>
    public string Status { get; set; } = "Pending";

    /// <summary>When the pipeline execution started.</summary>
    public DateTimeOffset? StartedAt { get; set; }

    /// <summary>When the pipeline execution completed.</summary>
    public DateTimeOffset? CompletedAt { get; set; }
}
