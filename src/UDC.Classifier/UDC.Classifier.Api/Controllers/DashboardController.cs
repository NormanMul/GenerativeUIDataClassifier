using Microsoft.AspNetCore.Mvc;
using UDC.Classifier.Core.Agents;
using UDC.Classifier.Core.Models;

namespace UDC.Classifier.Api.Controllers;

/// <summary>
/// Endpoints for AI-powered dashboard generation.
/// </summary>
[ApiController]
[Route("api/dashboard")]
public sealed class DashboardController : ControllerBase
{
    private readonly DashboardBuilderAgent _agent;

    /// <summary>
    /// Initializes a new instance of <see cref="DashboardController"/>.
    /// </summary>
    /// <param name="agent">Dashboard builder agent instance.</param>
    public DashboardController(DashboardBuilderAgent agent)
    {
        _agent = agent;
    }

    /// <summary>
    /// Generates a dashboard from a natural-language request.
    /// </summary>
    /// <param name="request">Dashboard generation request.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Generated dashboard specification.</returns>
    [HttpPost("generate")]
    [ProducesResponseType(typeof(DashboardSpec), StatusCodes.Status200OK)]
    public async Task<IActionResult> Generate(
        [FromBody] DashboardGenerateRequest request,
        CancellationToken cancellationToken)
    {
        var spec = await _agent.ParseRequestAsync(request.Prompt, cancellationToken);
        var completed = await _agent.GenerateDashboardSpecAsync(spec, cancellationToken);
        return Ok(completed);
    }
}

/// <summary>
/// Request body for dashboard generation.
/// </summary>
public sealed class DashboardGenerateRequest
{
    /// <summary>Natural-language prompt describing the desired dashboard.</summary>
    public required string Prompt { get; set; }
}
