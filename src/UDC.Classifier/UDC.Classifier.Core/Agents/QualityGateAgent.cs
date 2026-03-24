using Microsoft.SemanticKernel;
using UDC.Classifier.Core.Models;

namespace UDC.Classifier.Core.Agents;

/// <summary>
/// Quality gate agent — profiles data assets, validates quality rules,
/// and generates quality reports with pass/fail outcomes.
/// </summary>
public class QualityGateAgent
{
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of <see cref="QualityGateAgent"/>.
    /// </summary>
    /// <param name="kernel">Configured Semantic Kernel instance.</param>
    public QualityGateAgent(Kernel kernel)
    {
        _kernel = kernel ?? throw new ArgumentNullException(nameof(kernel));
    }

    /// <summary>
    /// Runs statistical profiling on a data asset's columns.
    /// </summary>
    /// <param name="asset">The data asset to profile.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Updated asset with profiling results.</returns>
    public virtual Task<DataAsset> RunProfilingAsync(
        DataAsset asset,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(asset);

        // Compute aggregate quality score from column-level profiles
        if (asset.Columns.Count == 0)
        {
            asset.QualityScore = 1.0;
            return Task.FromResult(asset);
        }

        double totalScore = 0;
        foreach (var col in asset.Columns)
        {
            // Completeness: percentage of non-null values (higher is better)
            double completeness = (100.0 - col.NullPercentage) / 100.0;
            // Uniqueness score: normalize percentage to 0-1
            double uniqueness = col.UniquePercentage / 100.0;
            // Column score: weighted average (completeness 70%, uniqueness 30%)
            double colScore = (completeness * 0.7) + (uniqueness * 0.3);
            totalScore += colScore;
        }

        asset.QualityScore = Math.Round(totalScore / asset.Columns.Count, 4);
        return Task.FromResult(asset);
    }

    /// <summary>
    /// Validates a data asset against quality rules.
    /// </summary>
    /// <param name="asset">The data asset to validate.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>True if all quality checks pass.</returns>
    public virtual async Task<bool> ValidateQualityAsync(
        DataAsset asset,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(asset);

        var profiledAsset = await RunProfilingAsync(asset, cancellationToken);

        // Rule 1: Overall quality score must be >= 0.7
        if (profiledAsset.QualityScore < 0.7)
            return false;

        // Rule 2: Each column must have completeness > 95% (null% < 5%)
        foreach (var col in profiledAsset.Columns)
        {
            if (col.NullPercentage > 5.0)
                return false;
        }

        // Rule 3: Primary key columns must have 100% uniqueness
        foreach (var col in profiledAsset.Columns.Where(c => c.IsPrimaryKey))
        {
            if (col.UniquePercentage < 100.0)
                return false;
        }

        return true;
    }

    /// <summary>
    /// Generates a full quality report for a data asset.
    /// </summary>
    /// <param name="asset">The data asset to report on.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Quality report with scores and check results.</returns>
    public virtual async Task<QualityReport> GenerateQualityReportAsync(
        DataAsset asset,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(asset);

        var profiledAsset = await RunProfilingAsync(asset, cancellationToken);
        var report = new QualityReport
        {
            AssetId = profiledAsset.Id,
            GeneratedBy = nameof(QualityGateAgent)
        };

        // Check 1: Overall quality score
        report.Checks.Add(new QualityCheck
        {
            RuleName = "OverallQualityScore",
            Description = "Overall quality score must be >= 0.7",
            Score = profiledAsset.QualityScore,
            Passed = profiledAsset.QualityScore >= 0.7,
            Details = $"Score: {profiledAsset.QualityScore:F4}"
        });

        // Check 2: Completeness per column (null% < 5%)
        foreach (var col in profiledAsset.Columns)
        {
            double completeness = (100.0 - col.NullPercentage) / 100.0;
            report.Checks.Add(new QualityCheck
            {
                RuleName = $"Completeness:{col.Name}",
                Description = $"Column '{col.Name}' must have > 95% completeness",
                Score = completeness,
                Passed = col.NullPercentage <= 5.0,
                Details = $"Null%: {col.NullPercentage:F1}, Completeness: {completeness:P1}"
            });
        }

        // Check 3: Primary key uniqueness
        foreach (var col in profiledAsset.Columns.Where(c => c.IsPrimaryKey))
        {
            double uniqueness = col.UniquePercentage / 100.0;
            report.Checks.Add(new QualityCheck
            {
                RuleName = $"PKUniqueness:{col.Name}",
                Description = $"Primary key '{col.Name}' must have 100% uniqueness",
                Score = uniqueness,
                Passed = col.UniquePercentage >= 100.0,
                Details = $"Unique%: {col.UniquePercentage:F1}"
            });
        }

        report.Passed = report.Checks.TrueForAll(c => c.Passed);
        report.OverallScore = report.Checks.Count > 0
            ? report.Checks.Average(c => c.Score)
            : 1.0;

        return report;
    }
}
