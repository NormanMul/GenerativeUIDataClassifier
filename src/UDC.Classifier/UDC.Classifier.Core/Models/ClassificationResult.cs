namespace UDC.Classifier.Core.Models;

/// <summary>
/// Result of an AI-driven classification for a single column within a data asset.
/// </summary>
public sealed class ClassificationResult
{
    /// <summary>Identifier of the parent data asset.</summary>
    public Guid AssetId { get; set; }

    /// <summary>Name of the classified column.</summary>
    public required string ColumnName { get; set; }

    /// <summary>Assigned classification label.</summary>
    public required string Classification { get; set; }

    /// <summary>Model confidence score (0.0–1.0).</summary>
    public double Confidence { get; set; }

    /// <summary>Data type of the column.</summary>
    public string? DataType { get; set; }

    /// <summary>Whether the column was identified as containing PII.</summary>
    public bool IsPii { get; set; }

    /// <summary>Type of PII detected, if applicable.</summary>
    public string? PiiType { get; set; }

    /// <summary>AI-suggested tags for the column.</summary>
    public List<string> SuggestedTags { get; set; } = [];

    /// <summary>LLM rationale explaining the classification decision.</summary>
    public string? Rationale { get; set; }

    /// <summary>Timestamp when the classification was performed.</summary>
    public DateTimeOffset ClassifiedAt { get; set; } = DateTimeOffset.UtcNow;
}
