using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace UDC.Classifier.Core.Skills;

/// <summary>
/// Semantic Kernel plugin for looking up business glossary terms
/// and resolving business formulas to technical definitions.
/// </summary>
public sealed class BusinessGlossarySkill
{
    /// <summary>
    /// Looks up a business term in the glossary and returns its definition.
    /// </summary>
    /// <param name="term">Business term to look up.</param>
    /// <returns>Glossary entry as JSON with definition, owner, and related terms.</returns>
    [KernelFunction, Description("Look up a business glossary term.")]
    public Task<string> LookupTermAsync(
        [Description("Business term to look up")] string term)
    {
        throw new NotImplementedException("Not yet implemented");
    }

    /// <summary>
    /// Resolves a business formula (e.g., "Net Revenue") to its technical SQL/DAX expression.
    /// </summary>
    /// <param name="formulaName">Name of the business formula.</param>
    /// <returns>Resolved technical expression as a string.</returns>
    [KernelFunction, Description("Resolve a business formula to a technical expression.")]
    public Task<string> ResolveFormulaAsync(
        [Description("Business formula name")] string formulaName)
    {
        throw new NotImplementedException("Not yet implemented");
    }
}
