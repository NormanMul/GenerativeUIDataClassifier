using Microsoft.AspNetCore.Mvc;
using UDC.Classifier.Core.Agents;
using UDC.Classifier.Core.Models;

namespace UDC.Classifier.Api.Controllers;

/// <summary>
/// Endpoints for data quality validation and reporting.
/// </summary>
[ApiController]
[Route("api/quality")]
public sealed class QualityGateController : ControllerBase
{
    private readonly QualityGateAgent _agent;

    /// <summary>
    /// Initializes a new instance of <see cref="QualityGateController"/>.
    /// </summary>
    /// <param name="agent">Quality gate agent instance.</param>
    public QualityGateController(QualityGateAgent agent)
    {
        _agent = agent;
    }

    /// <summary>
    /// Validates a data asset against quality rules and returns a quality report.
    /// </summary>
    /// <param name="asset">Data asset to validate.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Quality report with scores and check results.</returns>
    [HttpPost("validate")]
    [ProducesResponseType(typeof(QualityReport), StatusCodes.Status200OK)]
    public async Task<IActionResult> Validate(
        [FromBody] DataAsset asset,
        CancellationToken cancellationToken)
    {
        var report = await _agent.GenerateQualityReportAsync(asset, cancellationToken);
        return Ok(report);
    }
}
