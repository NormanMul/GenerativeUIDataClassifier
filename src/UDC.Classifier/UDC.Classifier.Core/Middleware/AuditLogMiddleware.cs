using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;

namespace UDC.Classifier.Core.Middleware;

/// <summary>
/// ASP.NET Core middleware that logs every incoming request for audit purposes.
/// </summary>
public sealed class AuditLogMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<AuditLogMiddleware> _logger;

    /// <summary>
    /// Initializes a new instance of <see cref="AuditLogMiddleware"/>.
    /// </summary>
    /// <param name="next">Next middleware in the pipeline.</param>
    /// <param name="logger">Logger instance.</param>
    public AuditLogMiddleware(RequestDelegate next, ILogger<AuditLogMiddleware> logger)
    {
        _next = next ?? throw new ArgumentNullException(nameof(next));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <summary>
    /// Invokes the middleware to log audit information for the request.
    /// </summary>
    /// <param name="context">HTTP context for the current request.</param>
    public Task InvokeAsync(HttpContext context)
    {
        throw new NotImplementedException("Not yet implemented");
    }
}
