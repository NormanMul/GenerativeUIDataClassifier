using System.Diagnostics;
using Microsoft.AspNetCore.Mvc;

namespace UDC.Classifier.Api.Controllers;

/// <summary>
/// Health check endpoint for monitoring and orchestration.
/// </summary>
[ApiController]
[Route("health")]
public sealed class HealthController : ControllerBase
{
    private static readonly DateTimeOffset StartTime = DateTimeOffset.UtcNow;

    /// <summary>
    /// Returns current service health status.
    /// </summary>
    /// <returns>JSON object with status, version, and uptime.</returns>
    [HttpGet]
    [ProducesResponseType(StatusCodes.Status200OK)]
    public IActionResult GetHealth()
    {
        var uptime = DateTimeOffset.UtcNow - StartTime;

        return Ok(new
        {
            status = "healthy",
            version = typeof(HealthController).Assembly.GetName().Version?.ToString() ?? "1.0.0",
            uptime = uptime.ToString(@"dd\.hh\:mm\:ss"),
            timestamp = DateTimeOffset.UtcNow
        });
    }
}
