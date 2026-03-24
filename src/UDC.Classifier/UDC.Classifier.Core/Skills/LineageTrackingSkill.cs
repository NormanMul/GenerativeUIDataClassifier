using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace UDC.Classifier.Core.Skills;

/// <summary>
/// Semantic Kernel plugin for tracking data lineage —
/// recording transformations and querying upstream/downstream dependencies.
/// </summary>
public sealed class LineageTrackingSkill
{
    /// <summary>
    /// Records a data transformation in the lineage graph.
    /// </summary>
    /// <param name="sourceAsset">Qualified name of the source asset.</param>
    /// <param name="targetAsset">Qualified name of the target asset.</param>
    /// <param name="transformationDescription">Description of the transformation applied.</param>
    /// <returns>Confirmation message with lineage edge ID.</returns>
    [KernelFunction, Description("Track a data transformation for lineage.")]
    public Task<string> TrackTransformationAsync(
        [Description("Source asset qualified name")] string sourceAsset,
        [Description("Target asset qualified name")] string targetAsset,
        [Description("Transformation description")] string transformationDescription)
    {
        throw new NotImplementedException("Not yet implemented");
    }

    /// <summary>
    /// Retrieves the lineage graph for a data asset.
    /// </summary>
    /// <param name="assetQualifiedName">Qualified name of the asset to trace.</param>
    /// <param name="direction">Direction: "upstream", "downstream", or "both".</param>
    /// <returns>Lineage graph as JSON.</returns>
    [KernelFunction, Description("Get lineage graph for a data asset.")]
    public Task<string> GetLineageAsync(
        [Description("Asset qualified name")] string assetQualifiedName,
        [Description("Direction: upstream, downstream, or both")] string direction = "both")
    {
        throw new NotImplementedException("Not yet implemented");
    }
}
