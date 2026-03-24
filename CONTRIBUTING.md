# Contributing to UDC Enterprise Platform

Thank you for your interest in contributing! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Branch Strategy](#branch-strategy)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch from `main`
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend services |
| Node.js | 20+ | Frontend portal |
| .NET SDK | 8.0+ | Classifier service |
| Docker Desktop | 4.x+ | Local environment |
| uv | latest | Python package manager |

### Quick Setup

```bash
# Clone and enter project
git clone https://github.com/NormanMul/GenerativeUIDataClassifier.git
cd GenerativeUIDataClassifier

# Copy environment template
cp .env.example .env

# Start infrastructure
docker compose up -d postgres redis chromadb

# Python backend (any service)
cd src/udc_metacatalog
uv sync
uv run uvicorn udc_metacatalog.main:app --reload --port 8001

# Frontend
cd src/udc_portal
npm install
npm run dev

# .NET Classifier
cd src/UDC.Classifier
dotnet run
```

### Demo Mode (No External Dependencies)

```bash
pip install fastapi uvicorn
python demo/mock_backend.py
# Open http://localhost:8006/demo
```

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code |
| `feature/*` | New features |
| `fix/*` | Bug fixes |
| `docs/*` | Documentation changes |

## Coding Standards

### Python (Backend Services)

- **Formatter**: `black` (line length: 120)
- **Linter**: `ruff` (see `pyproject.toml` for rule set)
- **Type Checker**: `mypy` (strict mode)
- **Imports**: sorted by `isort` (via ruff)

```bash
# Check all
ruff check src/
mypy src/
black --check src/
```

### TypeScript (Frontend Portal)

- **Linter**: ESLint (see `.eslintrc.cjs`)
- **Formatter**: Prettier (via ESLint)
- **Framework**: React 18 + Vite

```bash
cd src/udc_portal
npm run lint
npx tsc --noEmit
```

### .NET (Classifier)

- **Style**: `dotnet format`
- **Framework**: .NET 8 + Semantic Kernel

```bash
cd src/UDC.Classifier
dotnet format --verify-no-changes
dotnet build --warnaserrors
```

### Protobuf

- Definitions in `shared/proto/`
- Generate stubs: `bash scripts/generate_grpc.sh`

## Testing

```bash
# Python — all services
uv run pytest src/ -v

# Python — specific service
uv run pytest src/udc_metacatalog/ -v

# .NET
cd src/UDC.Classifier && dotnet test

# Frontend
cd src/udc_portal && npm test

# Integration tests (requires Docker)
uv run pytest src/ -v -m integration
```

## Pull Request Process

1. **Branch**: Create from `main` with descriptive name (`feature/add-lineage-export`)
2. **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/) format:
   - `feat: add CSV export to lineage graph`
   - `fix: correct PII detection for email columns`
   - `docs: update API reference for trust scores`
3. **Tests**: All tests must pass; add tests for new functionality
4. **CI**: All CI checks must pass (lint, type check, test, CodeQL)
5. **Review**: At least one approval from a code owner (see `.github/CODEOWNERS`)
6. **Merge**: Squash-merge to `main`

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated (if API changed)
- [ ] No secrets or credentials in code
- [ ] `ruff check` / `eslint` / `dotnet format` pass
- [ ] Docker build succeeds
- [ ] Protobuf regenerated (if `.proto` files changed)
