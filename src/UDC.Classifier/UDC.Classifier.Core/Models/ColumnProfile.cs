namespace UDC.Classifier.Core.Models;

/// <summary>
/// Column-level profiling result containing metadata, statistics, and classification information.
/// </summary>
public sealed class ColumnProfile
{
    /// <summary>Column name.</summary>
    public required string Name { get; set; }

    /// <summary>Data type of the column (e.g., varchar, int, timestamp).</summary>
    public required string DataType { get; set; }

    /// <summary>Whether the column allows null values.</summary>
    public bool IsNullable { get; set; }

    /// <summary>Whether the column is a primary key.</summary>
    public bool IsPrimaryKey { get; set; }

    /// <summary>Whether the column is a foreign key.</summary>
    public bool IsForeignKey { get; set; }

    /// <summary>Percentage of null values in the column (0.0–100.0).</summary>
    public double NullPercentage { get; set; }

    /// <summary>Percentage of unique values in the column (0.0–100.0).</summary>
    public double UniquePercentage { get; set; }

    /// <summary>Whether the column contains personally identifiable information.</summary>
    public bool IsPii { get; set; }

    /// <summary>Type of PII detected (e.g., Email, SSN, Phone) if applicable.</summary>
    public string? PiiType { get; set; }

    /// <summary>Assigned classification label.</summary>
    public string? Classification { get; set; }

    /// <summary>Sample values from the column for review.</summary>
    public List<string> SampleValues { get; set; } = [];
}
