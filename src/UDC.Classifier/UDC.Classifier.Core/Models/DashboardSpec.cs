namespace UDC.Classifier.Core.Models;

/// <summary>
/// Specification for generating a dashboard (Power BI or HTML).
/// </summary>
public sealed class DashboardSpec
{
    /// <summary>Unique identifier for this dashboard spec.</summary>
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>Title of the dashboard.</summary>
    public required string Title { get; set; }

    /// <summary>Business description of the dashboard purpose.</summary>
    public string? Description { get; set; }

    /// <summary>Target rendering platform: "powerbi" or "html".</summary>
    public required string Target { get; set; }

    /// <summary>Data sources referenced by this dashboard.</summary>
    public List<string> DataSources { get; set; } = [];

    /// <summary>Measures / KPIs to display.</summary>
    public List<string> Measures { get; set; } = [];

    /// <summary>Visual element definitions.</summary>
    public List<string> Visuals { get; set; } = [];

    /// <summary>Filter definitions for slicing data.</summary>
    public List<string> Filters { get; set; } = [];
}
