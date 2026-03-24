using System.ComponentModel;
using Microsoft.SemanticKernel;
using UDC.Classifier.Core.Models;

namespace UDC.Classifier.Core.Skills;

/// <summary>
/// Semantic Kernel plugin for rendering dashboards to Power BI or static HTML.
/// </summary>
public sealed class DashboardRenderSkill
{
    /// <summary>
    /// Renders a dashboard specification to a Power BI report definition (PBIR JSON).
    /// </summary>
    /// <param name="specJson">Dashboard specification as JSON.</param>
    /// <returns>Power BI report definition JSON.</returns>
    [KernelFunction, Description("Render dashboard spec to Power BI format.")]
    public Task<string> RenderPowerBIAsync(
        [Description("Dashboard spec JSON")] string specJson)
    {
        throw new NotImplementedException("Not yet implemented");
    }

    /// <summary>
    /// Renders a dashboard specification to a standalone HTML page with embedded charts.
    /// </summary>
    /// <param name="specJson">Dashboard specification as JSON.</param>
    /// <returns>Complete HTML page as a string.</returns>
    [KernelFunction, Description("Render dashboard spec to HTML.")]
    public Task<string> RenderHTMLAsync(
        [Description("Dashboard spec JSON")] string specJson)
    {
        throw new NotImplementedException("Not yet implemented");
    }
}
