namespace UDC.Classifier.Core.Models;

/// <summary>
/// Represents a data asset discovered from a source system (database, lakehouse, API, etc.).
/// </summary>
public sealed class DataAsset
{
    /// <summary>Unique identifier for the data asset.</summary>
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>Human-readable name of the data asset.</summary>
    public required string Name { get; set; }

    /// <summary>Fully qualified name including source, database, schema, and object name.</summary>
    public required string QualifiedName { get; set; }

    /// <summary>Type of the source system (e.g., PostgreSQL, SAP, FabricLakehouse).</summary>
    public required string SourceType { get; set; }

    /// <summary>Instance identifier of the source system.</summary>
    public string? SourceInstance { get; set; }

    /// <summary>Name of the database containing this asset.</summary>
    public string? DatabaseName { get; set; }

    /// <summary>Schema within the database.</summary>
    public string? SchemaName { get; set; }

    /// <summary>Business description of the data asset.</summary>
    public string? Description { get; set; }

    /// <summary>Tags applied to this asset for classification and search.</summary>
    public List<string> Tags { get; set; } = [];

    /// <summary>Overall data quality score (0.0–1.0).</summary>
    public double QualityScore { get; set; }

    /// <summary>Column-level profiles for this asset.</summary>
    public List<ColumnProfile> Columns { get; set; } = [];
}
