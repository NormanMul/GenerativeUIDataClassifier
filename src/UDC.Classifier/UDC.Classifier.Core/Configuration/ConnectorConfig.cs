namespace UDC.Classifier.Core.Configuration;

/// <summary>
/// POCO configuration for data source connectors including connection strings and retry policies.
/// </summary>
public sealed class ConnectorConfig
{
    /// <summary>Section name in appsettings.json.</summary>
    public const string SectionName = "Connectors";

    /// <summary>PostgreSQL connection string.</summary>
    public string? PostgreSqlConnectionString { get; set; }

    /// <summary>SAP S/4HANA OData base URL.</summary>
    public string? SapBaseUrl { get; set; }

    /// <summary>SAP S/4HANA username.</summary>
    public string? SapUsername { get; set; }

    /// <summary>SAP S/4HANA password.</summary>
    public string? SapPassword { get; set; }

    /// <summary>Microsoft Fabric workspace identifier.</summary>
    public string? FabricWorkspaceId { get; set; }

    /// <summary>Microsoft Fabric lakehouse identifier.</summary>
    public string? FabricLakehouseId { get; set; }

    /// <summary>Maximum number of retry attempts for transient failures.</summary>
    public int MaxRetryAttempts { get; set; } = 3;

    /// <summary>Base delay between retry attempts in milliseconds.</summary>
    public int RetryDelayMs { get; set; } = 500;

    /// <summary>Connection timeout in seconds.</summary>
    public int ConnectionTimeoutSeconds { get; set; } = 30;
}
