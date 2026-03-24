using UDC.Classifier.Core.Agents;
using UDC.Classifier.Core.Configuration;
using UDC.Classifier.Core.Middleware;

var builder = WebApplication.CreateBuilder(args);

// Semantic Kernel + Azure OpenAI
builder.Services.ConfigureSemanticKernel(builder.Configuration);

// Connector configuration
builder.Services.Configure<ConnectorConfig>(
    builder.Configuration.GetSection(ConnectorConfig.SectionName));

// Agents
builder.Services.AddScoped<ClassifierAgent>();
builder.Services.AddScoped<PipelineDocAgent>();
builder.Services.AddScoped<DashboardBuilderAgent>();
builder.Services.AddScoped<QualityGateAgent>();

// Controllers + Swagger
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new()
    {
        Title = "UDC Classifier API",
        Version = "v1",
        Description = "AI-powered data classification, pipeline documentation, quality gating, and dashboard generation."
    });
});

var app = builder.Build();

// Middleware pipeline
app.UseMiddleware<AuditLogMiddleware>();
app.UseMiddleware<AuthMiddleware>();
app.UseMiddleware<PolicyEnforcementMiddleware>();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.MapControllers();

app.Run();
