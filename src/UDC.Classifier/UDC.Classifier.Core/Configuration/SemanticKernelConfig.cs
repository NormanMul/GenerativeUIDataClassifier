using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using UDC.Classifier.Core.Skills;

namespace UDC.Classifier.Core.Configuration;

/// <summary>
/// Configures the Semantic Kernel with Azure OpenAI and registers all SK plugins.
/// </summary>
public static class SemanticKernelConfig
{
    /// <summary>
    /// Configures Semantic Kernel services, registers Azure OpenAI chat completion
    /// and embedding generation, and adds all classifier plugins.
    /// </summary>
    /// <param name="services">Service collection to configure.</param>
    /// <param name="configuration">Application configuration.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection ConfigureSemanticKernel(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        var endpoint = configuration["AzureOpenAI:Endpoint"]
            ?? throw new InvalidOperationException("AzureOpenAI:Endpoint is required.");
        var apiKey = configuration["AzureOpenAI:ApiKey"]
            ?? throw new InvalidOperationException("AzureOpenAI:ApiKey is required.");
        var chatDeployment = configuration["AzureOpenAI:DeploymentChat"]
            ?? "gpt-4o";
        var embeddingDeployment = configuration["AzureOpenAI:DeploymentEmbedding"]
            ?? "text-embedding-3-large";

        services.AddKernel();

        services.AddAzureOpenAIChatCompletion(chatDeployment, endpoint, apiKey);
#pragma warning disable SKEXP0010 // Embedding generation is experimental
        services.AddAzureOpenAITextEmbeddingGeneration(embeddingDeployment, endpoint, apiKey);
#pragma warning restore SKEXP0010

        // Register SK plugins
        services.AddSingleton<DataProfilingSkill>();
        services.AddSingleton<SchemaInferenceSkill>();
        services.AddSingleton<LineageTrackingSkill>();
        services.AddSingleton<BusinessGlossarySkill>();
        services.AddSingleton<DashboardRenderSkill>();
        services.AddSingleton<NaturalLanguageQuerySkill>();

        return services;
    }
}
