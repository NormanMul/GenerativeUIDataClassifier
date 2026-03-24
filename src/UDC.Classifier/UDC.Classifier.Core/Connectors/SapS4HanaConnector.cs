using System.Text.Json;
using System.Xml.Linq;
using Microsoft.Extensions.Logging;

namespace UDC.Classifier.Core.Connectors;

/// <summary>
/// OData client connector for SAP S/4HANA.
/// Connects to SAP services, retrieves entity sets, and executes OData queries.
/// </summary>
public sealed class SapS4HanaConnector
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<SapS4HanaConnector> _logger;
    private readonly string _baseUrl;

    /// <summary>
    /// Initializes a new instance of <see cref="SapS4HanaConnector"/>.
    /// </summary>
    /// <param name="httpClient">HTTP client for OData requests.</param>
    /// <param name="baseUrl">SAP S/4HANA OData service base URL.</param>
    /// <param name="logger">Logger instance.</param>
    public SapS4HanaConnector(HttpClient httpClient, string baseUrl, ILogger<SapS4HanaConnector> logger)
    {
        _httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));
        _baseUrl = baseUrl ?? throw new ArgumentNullException(nameof(baseUrl));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <summary>
    /// Validates the connection to the SAP S/4HANA OData service.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    public async Task ConnectAsync(CancellationToken cancellationToken = default)
    {
        // Validate connectivity by requesting the OData service root
        var requestUri = _baseUrl.TrimEnd('/') + "/";
        using var response = await _httpClient.GetAsync(requestUri, cancellationToken);
        response.EnsureSuccessStatusCode();
        _logger.LogInformation("Successfully connected to SAP S/4HANA OData service at {BaseUrl}", _baseUrl);
    }

    /// <summary>
    /// Retrieves available entity sets from the SAP OData service.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of entity set names.</returns>
    public async Task<List<string>> GetEntitiesAsync(CancellationToken cancellationToken = default)
    {
        var metadataUrl = _baseUrl.TrimEnd('/') + "/$metadata";
        using var response = await _httpClient.GetAsync(metadataUrl, cancellationToken);
        response.EnsureSuccessStatusCode();

        var xml = await response.Content.ReadAsStringAsync(cancellationToken);
        var doc = XDocument.Parse(xml);

        // OData $metadata has EntitySet elements within EntityContainer
        XNamespace edmx = "http://schemas.microsoft.com/ado/2007/06/edmx";
        XNamespace edm = "http://schemas.microsoft.com/ado/2008/09/edm";

        var entities = doc.Descendants()
            .Where(e => e.Name.LocalName == "EntitySet")
            .Select(e => e.Attribute("Name")?.Value)
            .Where(name => name is not null)
            .Select(name => name!)
            .ToList();

        _logger.LogInformation("Found {EntityCount} entity sets in SAP OData service", entities.Count);
        return entities;
    }

    /// <summary>
    /// Executes an OData query against the specified entity set.
    /// </summary>
    /// <param name="entitySet">Name of the entity set to query.</param>
    /// <param name="filter">OData $filter expression (optional).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Query results as a JSON string.</returns>
    public async Task<string> QueryAsync(
        string entitySet,
        string? filter = null,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(entitySet);

        var url = $"{_baseUrl.TrimEnd('/')}/{Uri.EscapeDataString(entitySet)}?$format=json";
        if (!string.IsNullOrWhiteSpace(filter))
            url += $"&$filter={Uri.EscapeDataString(filter)}";

        _logger.LogDebug("Querying SAP entity set: {EntitySet} with filter: {Filter}", entitySet, filter ?? "(none)");

        using var response = await _httpClient.GetAsync(url, cancellationToken);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync(cancellationToken);

        // Return the 'value' array from the OData response, or the raw JSON
        try
        {
            using var doc = JsonDocument.Parse(json);
            if (doc.RootElement.TryGetProperty("value", out var valueArray))
                return valueArray.GetRawText();
            if (doc.RootElement.TryGetProperty("d", out var dElement))
            {
                if (dElement.TryGetProperty("results", out var results))
                    return results.GetRawText();
                return dElement.GetRawText();
            }
        }
        catch (JsonException) { /* return raw */ }

        return json;
    }
}
