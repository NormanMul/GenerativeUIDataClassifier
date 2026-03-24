using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;

namespace UDC.Classifier.Core.Middleware;

/// <summary>
/// ASP.NET Core middleware that validates requests using API Key or Service Principal JWT tokens.
/// </summary>
public sealed class AuthMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<AuthMiddleware> _logger;

    /// <summary>
    /// Initializes a new instance of <see cref="AuthMiddleware"/>.
    /// </summary>
    /// <param name="next">Next middleware in the pipeline.</param>
    /// <param name="logger">Logger instance.</param>
    public AuthMiddleware(RequestDelegate next, ILogger<AuthMiddleware> logger)
    {
        _next = next ?? throw new ArgumentNullException(nameof(next));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <summary>
    /// Invokes the middleware to validate authentication credentials.
    /// </summary>
    /// <param name="context">HTTP context for the current request.</param>
    public Task InvokeAsync(HttpContext context)
    {
        throw new NotImplementedException("Not yet implemented");
    }
}
