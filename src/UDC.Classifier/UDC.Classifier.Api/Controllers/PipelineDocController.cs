using Microsoft.AspNetCore.Mvc;
using UDC.Classifier.Core.Agents;
using UDC.Classifier.Core.Models;

namespace UDC.Classifier.Api.Controllers;

/// <summary>
/// Endpoints for automated pipeline documentation and lineage extraction.
/// </summary>
[ApiController]
[Route("api/pipeline")]
public sealed class PipelineDocController : ControllerBase
{
    private readonly PipelineDocAgent _agent;

    /// <summary>
    /// Initializes a new instance of <see cref="PipelineDocController"/>.
    /// </summary>
    /// <param name="agent">Pipeline documentation agent instance.</param>
    public PipelineDocController(PipelineDocAgent agent)
    {
        _agent = agent;
    }

    /// <summary>
    /// Generates documentation for a pipeline.
    /// </summary>
    /// <param name="pipeline">Pipeline metadata to document.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Generated documentation.</returns>
    [HttpPost("document")]
    [ProducesResponseType(typeof(string), StatusCodes.Status200OK)]
    public async Task<IActionResult> Document(
        [FromBody] PipelineMetadata pipeline,
        CancellationToken cancellationToken)
    {
        var doc = await _agent.DocumentPipelineAsync(pipeline, cancellationToken);
        return Ok(new { documentation = doc });
    }
}
