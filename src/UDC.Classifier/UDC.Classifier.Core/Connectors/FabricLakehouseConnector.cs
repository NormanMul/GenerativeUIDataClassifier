using System.Net.Http.Headers;
using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace UDC.Classifier.Core.Connectors;

/// <summary>
/// Connector for Microsoft Fabric Lakehouse via OneLake REST API.
/// Lists tables and queries data stored in the lakehouse.
/// </summary>
public sealed class FabricLakehouseConnector
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<FabricLakehouseConnector> _logger;
    private readonly string _workspaceId;
    private readonly string _lakehouseId;

    /// <summary>
    /// Initializes a new instance of <see cref="FabricLakehouseConnector"/>.
    /// </summary>
    /// <param name="httpClient">HTTP client for OneLake REST API calls.</param>
    /// <param name="workspaceId">Fabric workspace identifier.</param>
    /// <param name="lakehouseId">Lakehouse identifier.</param>
    /// <param name="logger">Logger instance.</param>
    public FabricLakehouseConnector(
        HttpClient httpClient,
        string workspaceId,
        string lakehouseId,
        ILogger<FabricLakehouseConnector> logger)
    {
        _httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));
        _workspaceId = workspaceId ?? throw new ArgumentNullException(nameof(workspaceId));
        _lakehouseId = lakehouseId ?? throw new ArgumentNullException(nameof(lakehouseId));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <summary>
    /// Validates connectivity to the Fabric Lakehouse.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    public async Task ConnectAsync(CancellationToken cancellationToken = default)
    {
        // Validate connectivity by requesting lakehouse metadata
        var url = $"https://api.fabric.microsoft.com/v1/workspaces/{Uri.EscapeDataString(_workspaceId)}/lakehouses/{Uri.EscapeDataString(_lakehouseId)}";

        using var response = await _httpClient.GetAsync(url, cancellationToken);
        response.EnsureSuccessStatusCode();
        _logger.LogInformation(
            "Connected to Fabric Lakehouse {LakehouseId} in workspace {WorkspaceId}",
            _lakehouseId, _workspaceId);
    }

    /// <summary>
    /// Lists all tables available in the lakehouse.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of table names.</returns>
    public async Task<List<string>> ListTablesAsync(CancellationToken cancellationToken = default)
    {
        var url = $"https://api.fabric.microsoft.com/v1/workspaces/{Uri.EscapeDataString(_workspaceId)}/lakehouses/{Uri.EscapeDataString(_lakehouseId)}/tables";

        using var response = await _httpClient.GetAsync(url, cancellationToken);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync(cancellationToken);
        using var doc = JsonDocument.Parse(json);

        var tables = new List<string>();
        if (doc.RootElement.TryGetProperty("data", out var dataArray) && dataArray.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in dataArray.EnumerateArray())
            {
                if (item.TryGetProperty("name", out var name))
                {
                    var tableName = name.GetString();
                    if (tableName is not null)
                        tables.Add(tableName);
                }
            }
        }

        _logger.LogInformation("Found {TableCount} tables in lakehouse {LakehouseId}", tables.Count, _lakehouseId);
        return tables;
    }

    /// <summary>
    /// Queries a table in the lakehouse and returns results as JSON.
    /// </summary>
    /// <param name="tableName">Name of the table to query.</param>
    /// <param name="filter">Optional filter expression.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Query results as a JSON string.</returns>
    public async Task<string> QueryAsync(
        string tableName,
        string? filter = null,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(tableName);

        // Use the Fabric SQL analytics endpoint to query Delta tables
        var url = $"https://api.fabric.microsoft.com/v1/workspaces/{Uri.EscapeDataString(_workspaceId)}/lakehouses/{Uri.EscapeDataString(_lakehouseId)}/query";

        var query = $"SELECT * FROM {tableName}";
        if (!string.IsNullOrWhiteSpace(filter))
            query += $" WHERE {filter}";
        query += " LIMIT 1000";

        var payload = JsonSerializer.Serialize(new { query });
        using var content = new StringContent(payload, System.Text.Encoding.UTF8, "application/json");

        _logger.LogDebug("Querying Fabric lakehouse table: {Table} with filter: {Filter}", tableName, filter ?? "(none)");

        using var response = await _httpClient.PostAsync(url, content, cancellationToken);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadAsStringAsync(cancellationToken);
    }
}
