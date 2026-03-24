using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using UDC.Classifier.Core.Models;

namespace UDC.Classifier.Core.Agents;

/// <summary>
/// Use Case 4 agent — parses natural-language dashboard requests,
/// generates dashboard specifications, and renders Power BI or HTML dashboards.
/// </summary>
public class DashboardBuilderAgent
{
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of <see cref="DashboardBuilderAgent"/>.
    /// </summary>
    /// <param name="kernel">Configured Semantic Kernel instance.</param>
    public DashboardBuilderAgent(Kernel kernel)
    {
        _kernel = kernel ?? throw new ArgumentNullException(nameof(kernel));
    }

    /// <summary>
    /// Parses a natural-language request into structured dashboard requirements.
    /// </summary>
    /// <param name="request">Natural-language description of the desired dashboard.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Parsed dashboard specification.</returns>
    public virtual async Task<DashboardSpec> ParseRequestAsync(
        string request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);

        var chatService = _kernel.GetRequiredService<IChatCompletionService>();

        var prompt = $$"""
            You are a BI dashboard designer. Parse the following natural-language request
            into a structured dashboard specification. Respond ONLY with JSON (no markdown).

            Request: {{request}}

            JSON schema:
            {
              "title": "<dashboard title>",
              "description": "<purpose>",
              "target": "<powerbi|html>",
              "dataSources": ["table1", "table2"],
              "measures": ["SUM(revenue)", "COUNT(orders)"],
              "visuals": ["bar_chart: revenue by region", "line_chart: orders over time"],
              "filters": ["date_range", "region"]
            }
            """;

        var history = new ChatHistory();
        history.AddUserMessage(prompt);
        var response = await chatService.GetChatMessageContentAsync(history, cancellationToken: cancellationToken);
        var responseText = response.Content?.Trim() ?? "{}";

        if (responseText.StartsWith("```"))
        {
            var firstNewline = responseText.IndexOf('\n');
            var lastFence = responseText.LastIndexOf("```");
            if (firstNewline >= 0 && lastFence > firstNewline)
                responseText = responseText[(firstNewline + 1)..lastFence].Trim();
        }

        var spec = new DashboardSpec { Title = "Dashboard", Target = "html" };

        try
        {
            using var doc = JsonDocument.Parse(responseText);
            var root = doc.RootElement;

            if (root.TryGetProperty("title", out var t)) spec.Title = t.GetString() ?? "Dashboard";
            if (root.TryGetProperty("description", out var d)) spec.Description = d.GetString();
            if (root.TryGetProperty("target", out var tgt)) spec.Target = tgt.GetString() ?? "html";

            static List<string> ReadArray(JsonElement el)
            {
                var list = new List<string>();
                if (el.ValueKind == JsonValueKind.Array)
                    foreach (var item in el.EnumerateArray())
                    {
                        var s = item.GetString();
                        if (s is not null) list.Add(s);
                    }
                return list;
            }

            if (root.TryGetProperty("dataSources", out var ds)) spec.DataSources = ReadArray(ds);
            if (root.TryGetProperty("measures", out var m)) spec.Measures = ReadArray(m);
            if (root.TryGetProperty("visuals", out var v)) spec.Visuals = ReadArray(v);
            if (root.TryGetProperty("filters", out var f)) spec.Filters = ReadArray(f);
        }
        catch (JsonException) { /* use defaults */ }

        return spec;
    }

    /// <summary>
    /// Generates a full dashboard specification from parsed requirements.
    /// </summary>
    /// <param name="spec">Partial dashboard spec to complete.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Completed dashboard specification.</returns>
    public virtual async Task<DashboardSpec> GenerateDashboardSpecAsync(
        DashboardSpec spec,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(spec);

        var chatService = _kernel.GetRequiredService<IChatCompletionService>();

        var prompt = $"""        
            You are a BI dashboard designer. Given the partial dashboard spec below,
            add appropriate visuals and complete any missing details.
            Respond ONLY with a JSON array of visual definitions (no markdown).

            Title: {spec.Title}
            Data Sources: {string.Join(", ", spec.DataSources)}
            Measures: {string.Join(", ", spec.Measures)}
            Filters: {string.Join(", ", spec.Filters)}
            Existing Visuals: {string.Join(", ", spec.Visuals)}

            Return JSON array: ["visual_type: description", ...]
            """;

        var history = new ChatHistory();
        history.AddUserMessage(prompt);
        var response = await chatService.GetChatMessageContentAsync(history, cancellationToken: cancellationToken);
        var responseText = response.Content?.Trim() ?? "[]";

        if (responseText.StartsWith("```"))
        {
            var firstNewline = responseText.IndexOf('\n');
            var lastFence = responseText.LastIndexOf("```");
            if (firstNewline >= 0 && lastFence > firstNewline)
                responseText = responseText[(firstNewline + 1)..lastFence].Trim();
        }

        try
        {
            var visuals = JsonSerializer.Deserialize<List<string>>(responseText);
            if (visuals is not null)
                spec.Visuals = visuals;
        }
        catch (JsonException) { /* keep existing visuals */ }

        return spec;
    }

    /// <summary>
    /// Renders the dashboard to the target platform (Power BI or HTML).
    /// </summary>
    /// <param name="spec">Completed dashboard specification.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Rendered output (Power BI JSON or HTML string).</returns>
    public virtual async Task<string> RenderDashboardAsync(
        DashboardSpec spec,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(spec);

        if (spec.Target.Equals("powerbi", StringComparison.OrdinalIgnoreCase))
        {
            // Generate Power BI-compatible JSON
            return JsonSerializer.Serialize(new
            {
                spec.Title,
                spec.Description,
                spec.DataSources,
                spec.Measures,
                spec.Visuals,
                spec.Filters
            }, new JsonSerializerOptions { WriteIndented = true });
        }

        // Generate HTML dashboard with Chart.js
        var chartConfigs = new System.Text.StringBuilder();
        for (int i = 0; i < spec.Visuals.Count; i++)
        {
            var visual = spec.Visuals[i];
            var chartType = visual.Contains("line", StringComparison.OrdinalIgnoreCase) ? "line"
                : visual.Contains("pie", StringComparison.OrdinalIgnoreCase) ? "pie"
                : "bar";

            chartConfigs.AppendLine($$"""
                <div style="flex:1;min-width:400px;padding:16px">
                  <canvas id="chart{{i}}"></canvas>
                  <script>
                    new Chart(document.getElementById('chart{{i}}'), {
                      type: '{{chartType}}',
                      data: {
                        labels: ['Sample A','Sample B','Sample C'],
                        datasets: [{
                          label: '{{visual.Replace("'", "\\'")}},',
                          data: [10, 20, 30],
                          backgroundColor: ['#3b82f6','#ef4444','#22c55e']
                        }]
                      },
                      options: { responsive: true }
                    });
                  </script>
                </div>
            """);
        }

        var filtersHtml = string.Join("\n", spec.Filters.Select(f =>
            $"<label style='margin-right:12px'>{f}: <select><option>All</option></select></label>"));

        return $$"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <title>{{spec.Title}}</title>
              <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
              <style>
                body { font-family:system-ui,sans-serif; margin:0; background:#f1f5f9; }
                header { background:#1e293b; color:#fff; padding:24px; }
                .filters { padding:16px 24px; background:#fff; border-bottom:1px solid #e2e8f0; }
                .grid { display:flex; flex-wrap:wrap; padding:16px; }
              </style>
            </head>
            <body>
              <header>
                <h1>{{spec.Title}}</h1>
                <p>{{spec.Description ?? "Auto-generated dashboard"}}</p>
              </header>
              <div class="filters">{{filtersHtml}}</div>
              <div class="grid">
                {{chartConfigs}}
              </div>
            </body>
            </html>
            """;
    }
}
