using Microsoft.Extensions.Logging;
using Npgsql;

namespace UDC.Classifier.Core.Connectors;

/// <summary>
/// Connector for PostgreSQL-based WMS (Warehouse Management System) data stores.
/// Provides methods to query tables, columns, and execute arbitrary SQL.
/// </summary>
public sealed class PostgresConnector : IAsyncDisposable
{
    private readonly string _connectionString;
    private readonly ILogger<PostgresConnector> _logger;
    private NpgsqlConnection? _connection;

    /// <summary>
    /// Initializes a new instance of <see cref="PostgresConnector"/>.
    /// </summary>
    /// <param name="connectionString">PostgreSQL connection string.</param>
    /// <param name="logger">Logger instance.</param>
    public PostgresConnector(string connectionString, ILogger<PostgresConnector> logger)
    {
        _connectionString = connectionString ?? throw new ArgumentNullException(nameof(connectionString));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <summary>
    /// Opens a connection to the PostgreSQL database.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    public async Task ConnectAsync(CancellationToken cancellationToken = default)
    {
        if (_connection is not null && _connection.State == System.Data.ConnectionState.Open)
            return;

        _connection = new NpgsqlConnection(_connectionString);
        await _connection.OpenAsync(cancellationToken);
        _logger.LogInformation("Connected to PostgreSQL at {Host}", _connection.Host);
    }

    /// <summary>
    /// Executes a SQL query and returns results as a list of dictionaries.
    /// </summary>
    /// <param name="sql">SQL query to execute.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Query results as a list of row dictionaries.</returns>
    public async Task<List<Dictionary<string, object?>>> ExecuteQueryAsync(
        string sql,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(sql);
        await ConnectAsync(cancellationToken);

        var results = new List<Dictionary<string, object?>>();
        await using var cmd = new NpgsqlCommand(sql, _connection);
        await using var reader = await cmd.ExecuteReaderAsync(cancellationToken);

        while (await reader.ReadAsync(cancellationToken))
        {
            var row = new Dictionary<string, object?>();
            for (int i = 0; i < reader.FieldCount; i++)
            {
                row[reader.GetName(i)] = reader.IsDBNull(i) ? null : reader.GetValue(i);
            }
            results.Add(row);
        }

        _logger.LogDebug("Executed query, returned {RowCount} rows", results.Count);
        return results;
    }

    /// <summary>
    /// Retrieves the list of tables in the specified schema.
    /// </summary>
    /// <param name="schema">Schema name (defaults to "public").</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of table names.</returns>
    public async Task<List<string>> GetTablesAsync(
        string schema = "public",
        CancellationToken cancellationToken = default)
    {
        await ConnectAsync(cancellationToken);

        var tables = new List<string>();
        var sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = $1 AND table_type = 'BASE TABLE' ORDER BY table_name";

        await using var cmd = new NpgsqlCommand(sql, _connection);
        cmd.Parameters.AddWithValue(schema);
        await using var reader = await cmd.ExecuteReaderAsync(cancellationToken);

        while (await reader.ReadAsync(cancellationToken))
        {
            tables.Add(reader.GetString(0));
        }

        _logger.LogInformation("Found {TableCount} tables in schema '{Schema}'", tables.Count, schema);
        return tables;
    }

    /// <summary>
    /// Retrieves column metadata for a given table.
    /// </summary>
    /// <param name="tableName">Name of the table.</param>
    /// <param name="schema">Schema name (defaults to "public").</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of column metadata dictionaries.</returns>
    public async Task<List<Dictionary<string, object?>>> GetColumnsAsync(
        string tableName,
        string schema = "public",
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(tableName);
        await ConnectAsync(cancellationToken);

        var sql = """
            SELECT column_name, data_type, is_nullable, column_default,
                   character_maximum_length, numeric_precision, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
            """;

        await using var cmd = new NpgsqlCommand(sql, _connection);
        cmd.Parameters.AddWithValue(schema);
        cmd.Parameters.AddWithValue(tableName);
        await using var reader = await cmd.ExecuteReaderAsync(cancellationToken);

        var columns = new List<Dictionary<string, object?>>();
        while (await reader.ReadAsync(cancellationToken))
        {
            columns.Add(new Dictionary<string, object?>
            {
                ["column_name"] = reader.GetString(0),
                ["data_type"] = reader.GetString(1),
                ["is_nullable"] = reader.GetString(2) == "YES",
                ["column_default"] = reader.IsDBNull(3) ? null : reader.GetString(3),
                ["max_length"] = reader.IsDBNull(4) ? null : (object)reader.GetInt32(4),
                ["numeric_precision"] = reader.IsDBNull(5) ? null : (object)reader.GetInt32(5),
                ["ordinal_position"] = reader.GetInt32(6)
            });
        }

        _logger.LogInformation("Found {ColumnCount} columns in '{Schema}.{Table}'", columns.Count, schema, tableName);
        return columns;
    }

    /// <summary>
    /// Disposes the database connection.
    /// </summary>
    public async ValueTask DisposeAsync()
    {
        if (_connection is not null)
        {
            await _connection.DisposeAsync();
            _connection = null;
        }
    }
}
