using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;

namespace UDC.Classifier.Core.Middleware;

/// <summary>
/// ASP.NET Core middleware that calls UDC-PolicyGuard to enforce data governance policies
/// before allowing request processing to continue.
/// </summary>
public sealed class PolicyEnforcementMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<PolicyEnforcementMiddleware> _logger;

    /// <summary>
    /// Initializes a new instance of <see cref="PolicyEnforcementMiddleware"/>.
    /// </summary>
    /// <param name="next">Next middleware in the pipeline.</param>
    /// <param name="logger">Logger instance.</param>
    public PolicyEnforcementMiddleware(RequestDelegate next, ILogger<PolicyEnforcementMiddleware> logger)
    {
        _next = next ?? throw new ArgumentNullException(nameof(next));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <summary>
    /// Invokes the middleware to enforce policy checks via UDC-PolicyGuard.
    /// </summary>
    /// <param name="context">HTTP context for the current request.</param>
    public Task InvokeAsync(HttpContext context)
    {
        throw new NotImplementedException("Not yet implemented");
    }
}
