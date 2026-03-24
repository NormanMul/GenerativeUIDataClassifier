namespace UDC.Classifier.Core.Models;

/// <summary>
/// Data quality report generated after profiling and validation of a data asset.
/// </summary>
public sealed class QualityReport
{
    /// <summary>Unique identifier for this quality report.</summary>
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>Identifier of the data asset that was assessed.</summary>
    public Guid AssetId { get; set; }

    /// <summary>Overall quality score (0.0–1.0).</summary>
    public double OverallScore { get; set; }

    /// <summary>Whether the asset passed all quality checks.</summary>
    public bool Passed { get; set; }

    /// <summary>Individual quality checks performed.</summary>
    public List<QualityCheck> Checks { get; set; } = [];

    /// <summary>Timestamp when the report was generated.</summary>
    public DateTimeOffset GeneratedAt { get; set; } = DateTimeOffset.UtcNow;

    /// <summary>Identity or agent that generated this report.</summary>
    public string? GeneratedBy { get; set; }
}

/// <summary>
/// An individual quality check result within a quality report.
/// </summary>
public sealed class QualityCheck
{
    /// <summary>Name of the quality check rule.</summary>
    public required string RuleName { get; set; }

    /// <summary>Description of what the check validates.</summary>
    public string? Description { get; set; }

    /// <summary>Whether this check passed.</summary>
    public bool Passed { get; set; }

    /// <summary>Score for this individual check (0.0–1.0).</summary>
    public double Score { get; set; }

    /// <summary>Details or message about the check result.</summary>
    public string? Details { get; set; }
}
