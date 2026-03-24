using System.ComponentModel;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Npgsql;
using UDC.Classifier.Core.Models;

namespace UDC.Classifier.Core.Skills;

/// <summary>
/// Semantic Kernel plugin for profiling data columns and tables,
/// computing statistics such as null percentages, uniqueness, and sample values.
/// </summary>
public sealed class DataProfilingSkill
{
    /// <summary>
    /// Profiles a single column, computing statistics and detecting anomalies.
    /// </summary>
    /// <param name="columnName">Name of the column to profile.</param>
    /// <param name="tableName">Fully qualified table name.</param>
    /// <param name="connectionString">Connection string to the data source.</param>
    /// <returns>Serialized column profile JSON.</returns>
    [KernelFunction, Description("Profile a single column to compute statistics.")]
    public async Task<string> ProfileColumnAsync(
        [Description("Name of the column")] string columnName,
        [Description("Fully qualified table name")] string tableName,
        [Description("Connection string")] string connectionString)
    {
        await using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync();

        // Use parameterized identifiers via quoting (column/table names can't be parameterized in SQL)
        var safeTable = tableName.Replace("\"", "\"\"");
        var safeCol = columnName.Replace("\"", "\"\"");

        var sql = $"""
            SELECT
                COUNT(*) AS total_rows,
                COUNT(\"{safeCol}\") AS non_null_count,
                COUNT(DISTINCT \"{safeCol}\") AS distinct_count,
                MIN(\"{safeCol}\"::text) AS min_value,
                MAX(\"{safeCol}\"::text) AS max_value
            FROM \"{safeTable}\"
            """;

        await using var cmd = new NpgsqlCommand(sql, conn);
        await using var reader = await cmd.ExecuteReaderAsync();

        if (!await reader.ReadAsync())
            return JsonSerializer.Serialize(new { error = "No data returned" });

        var totalRows = reader.GetInt64(0);
        var nonNullCount = reader.GetInt64(1);
        var distinctCount = reader.GetInt64(2);
        var minValue = reader.IsDBNull(3) ? null : reader.GetString(3);
        var maxValue = reader.IsDBNull(4) ? null : reader.GetString(4);

        double nullPct = totalRows > 0 ? (double)(totalRows - nonNullCount) / totalRows * 100.0 : 0;
        double uniquePct = totalRows > 0 ? (double)distinctCount / totalRows * 100.0 : 0;

        var profile = new
        {
            columnName,
            tableName,
            totalRows,
            nonNullCount,
            distinctCount,
            nullPercentage = Math.Round(nullPct, 2),
            uniquePercentage = Math.Round(uniquePct, 2),
            minValue,
            maxValue
        };

        return JsonSerializer.Serialize(profile);
    }

    /// <summary>
    /// Profiles all columns in a table and returns aggregated statistics.
    /// </summary>
    /// <param name="tableName">Fully qualified table name.</param>
    /// <param name="connectionString">Connection string to the data source.</param>
    /// <returns>Serialized list of column profiles as JSON.</returns>
    [KernelFunction, Description("Profile all columns in a table.")]
    public async Task<string> ProfileTableAsync(
        [Description("Fully qualified table name")] string tableName,
        [Description("Connection string")] string connectionString)
    {
        await using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync();

        // Parse schema.table or default to public schema
        var parts = tableName.Split('.');
        var schema = parts.Length > 1 ? parts[0] : "public";
        var table = parts.Length > 1 ? parts[1] : parts[0];

        var columnSql = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
            """;

        await using var cmd = new NpgsqlCommand(columnSql, conn);
        cmd.Parameters.AddWithValue(schema);
        cmd.Parameters.AddWithValue(table);
        await using var reader = await cmd.ExecuteReaderAsync();

        var columnNames = new List<(string name, string dataType, bool nullable)>();
        while (await reader.ReadAsync())
        {
            columnNames.Add((
                reader.GetString(0),
                reader.GetString(1),
                reader.GetString(2) == "YES"
            ));
        }
        await reader.CloseAsync();

        var profiles = new List<string>();
        foreach (var (colName, dataType, nullable) in columnNames)
        {
            var profile = await ProfileColumnAsync(colName, tableName, connectionString);
            profiles.Add(profile);
        }

        return $"[{string.Join(",", profiles)}]";
    }
}
