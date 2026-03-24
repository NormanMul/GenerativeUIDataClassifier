using Microsoft.AspNetCore.Mvc;
using UDC.Classifier.Core.Agents;
using UDC.Classifier.Core.Models;

namespace UDC.Classifier.Api.Controllers;

/// <summary>
/// Endpoints for AI-driven data classification of assets and columns.
/// </summary>
[ApiController]
[Route("api/classify")]
public sealed class ClassifyController : ControllerBase
{
    private readonly ClassifierAgent _agent;

    /// <summary>
    /// Initializes a new instance of <see cref="ClassifyController"/>.
    /// </summary>
    /// <param name="agent">Classifier agent instance.</param>
    public ClassifyController(ClassifierAgent agent)
    {
        _agent = agent;
    }

    /// <summary>
    /// Classifies all columns in a single data asset.
    /// </summary>
    /// <param name="asset">Data asset to classify.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of classification results.</returns>
    [HttpPost]
    [ProducesResponseType(typeof(List<ClassificationResult>), StatusCodes.Status200OK)]
    public async Task<IActionResult> Classify(
        [FromBody] DataAsset asset,
        CancellationToken cancellationToken)
    {
        var results = await _agent.ClassifyAssetAsync(asset, cancellationToken);
        return Ok(results);
    }

    /// <summary>
    /// Classifies columns across multiple data assets in batch.
    /// </summary>
    /// <param name="assets">List of data assets to classify.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Aggregated classification results for all assets.</returns>
    [HttpPost("batch")]
    [ProducesResponseType(typeof(List<ClassificationResult>), StatusCodes.Status200OK)]
    public async Task<IActionResult> ClassifyBatch(
        [FromBody] List<DataAsset> assets,
        CancellationToken cancellationToken)
    {
        var allResults = new List<ClassificationResult>();
        foreach (var asset in assets)
        {
            var results = await _agent.ClassifyAssetAsync(asset, cancellationToken);
            allResults.AddRange(results);
        }
        return Ok(allResults);
    }
}
