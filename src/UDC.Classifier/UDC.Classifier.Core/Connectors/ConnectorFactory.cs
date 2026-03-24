using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace UDC.Classifier.Core.Connectors;

/// <summary>
/// Factory for creating source-system connectors based on the source type identifier.
/// </summary>
public static class ConnectorFactory
{
    /// <summary>
    /// Creates the appropriate connector instance for the given source type.
    /// </summary>
    /// <param name="sourceType">Source type identifier (e.g., "postgresql", "sap_s4hana", "fabric_lakehouse").</param>
    /// <param name="serviceProvider">Service provider for resolving dependencies.</param>
    /// <returns>An object representing the connector (caller casts to the specific type).</returns>
    /// <exception cref="ArgumentException">Thrown when the source type is not supported.</exception>
    public static object CreateConnector(string sourceType, IServiceProvider serviceProvider)
    {
        ArgumentNullException.ThrowIfNull(sourceType);
        ArgumentNullException.ThrowIfNull(serviceProvider);

        return sourceType.ToLowerInvariant() switch
        {
            "postgresql" => serviceProvider.GetRequiredService<PostgresConnector>(),
            "sap_s4hana" => serviceProvider.GetRequiredService<SapS4HanaConnector>(),
            "fabric_lakehouse" => serviceProvider.GetRequiredService<FabricLakehouseConnector>(),
            _ => throw new ArgumentException($"Unsupported source type: {sourceType}", nameof(sourceType))
        };
    }
}
