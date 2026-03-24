# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following channels:

1. **Email**: Send details to the repository maintainer at the email listed in the GitHub profile.
2. **GitHub Private Vulnerability Reporting**: Use the "Report a vulnerability" button on the Security tab of this repository.

### What to Include

- A description of the vulnerability and its potential impact
- Step-by-step instructions to reproduce the issue
- Any proof-of-concept code (if applicable)
- Your recommended fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Resolution Target**: Within 30 days for critical issues

## Security Best Practices for Contributors

### Secrets Management
- **Never** commit credentials, API keys, or tokens to the repository
- Use `.env` files locally (already in `.gitignore`)
- Use Azure Key Vault for production secrets
- Rotate credentials regularly

### Authentication & Authorization
- All API endpoints require authentication (Azure AD JWT or API key)
- Role-based access control (RBAC) is enforced via PolicyGuard
- API keys are hashed before storage (SHA-256 + salt)

### Data Protection
- PII is automatically detected and classified by the Classifier service
- Access to PII-tagged columns requires explicit policy approval
- All data access is logged in the audit trail
- TLS 1.2+ is required for all external connections

### Dependency Management
- Dependencies are automatically scanned via GitHub CodeQL (see `.github/workflows/codeql.yml`)
- Python dependencies are pinned and audited via `pip-audit`
- .NET dependencies are scanned via `dotnet list package --vulnerable`
- npm packages are audited via `npm audit`

### Container Security
- Docker images use minimal base images (slim/alpine variants)
- Containers run as non-root users
- No secrets are baked into Docker images
- Container images are scanned in CI before deployment
