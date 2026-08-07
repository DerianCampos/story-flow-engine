# Story Flow Engine

A CLI tool that transforms structured Markdown files into Jira issues. Write your epics and user stories once in Markdown, push them to Jira automatically.

![story-cli-home](./docs/images/story-cli-preview.png)

## 🚀 Quick Start

```bash
git clone <repo-url> && cd story-flow-engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # edit with your Jira credentials
./scripts/run-cli
```

## ✨ Features

- **Markdown Parsing** — Parse structured epic and user story templates
- **Jira Integration** — Create and fetch issues via REST API
- **Hierarchical Support** — Manage Epic → Stories relationships
- **Interactive CLI** — Menu-driven interface with InquirerPy, or direct commands for scripting
- **Clean Architecture** — Domain-Driven Design with clear separation of concerns

## 💻 Usage

### Interactive Menu

```bash
./scripts/run-cli
# or
python -m src.app.presentation.cli
```

Three options available:

1. **Retrieve an epic** — Fetch epic details from Jira by key (e.g., `PROJ-123`)
2. **Create a new epic** — Parse a Markdown file and create the epic in Jira
3. **Exit**

### Direct Commands (for scripts / CI)

The CLI also supports argument-based invocation:

```bash
# Fetch an epic by Jira key
python -m src.app.presentation.cli fetch-epic PROJ-123

# Create an epic from a markdown file
python -m src.app.presentation.cli create-epic data/EPIC-0-foundational/epic.md
```

> Full CLI reference: [CLI Reference Guide](docs/guides/cli-reference.md)

## 📝 Markdown Format

Place epics and stories under `data/EPIC-N-description/` with `epic.md` and `stories.md` files.

### Epics

```markdown
# Epic: My Feature

**Epic Title**: My Feature
**Epic Key**: EPIC-1
**Summary**: Short description of the epic
**Labels**: frontend, api
**Priority**: Must Have

---

**Epic Description:**
Detailed description here...
```

### User Stories

```markdown
# Story: User Authentication

**Story Title**: User Authentication
**Story Key**: STORY-1
**As a** visitor
**I want** to sign in securely
**So that** I can access my private dashboard
**Labels**: backend, auth
**Priority**: Should Have
**Story Points**: 5

---

**Acceptance Criteria:**

- User can sign in with email and password
- Invalid credentials return a clear error message
- Session remains active until logout
```

> Full template spec: [Markdown Format Guide](docs/guides/markdown-format.md)

## 🏗️ Architecture

```text
src/app/
├── main.py                      # Entry point
├── config/                      # YAML-based configuration
├── domain/                      # Entities, value objects, exceptions
│   ├── entities/                # Epic, UserStory
│   ├── value_objects/           # IssueId, Priority, StoryPoints, Label
│   └── exceptions/              # BusinessRule, NotFound, Duplicate, etc.
├── application/                 # Use cases, DTOs, repository interfaces
│   ├── use_cases/               # GetEpicWithStories
│   ├── dtos/                    # EpicDTO, StoryDTO
│   ├── interfaces/              # JiraRepository (port)
│   └── mappers/                 # Entity ↔ DTO mapping
├── infrastructure/              # External adapters
│   └── external/jira/           # httpx-based Jira REST client
├── presentation/                # Typer CLI + InquirerPy menus
└── shared/                      # Cross-cutting utilities
    ├── logging.py               # Structured logger (JSON or plain text)
    └── utils/                   # Retry decorator
```

The project follows **Clean Architecture** with **Domain-Driven Design**. Entities use factory methods, value objects are immutable, and the application layer depends only on abstractions (ports), not concrete implementations.

> Deep dive: [Architecture Overview](docs/architecture/overview.md)

## 🛠️ Development

```bash
pytest                  # run all tests
pytest --cov=src        # with coverage
pytest tests/unit/domain/   # specific path
```

- **Style**: PEP 8, Google-style docstrings, full type hints
- **Naming**: camelCase variables, PascalCase classes

> Dev setup guide: [Development Setup](docs/development/setup.md) · Testing: [Testing Guide](docs/development/testing.md)

## 📚 Documentation

| Topic             | Link                                                         |
| ----------------- | ------------------------------------------------------------ |
| Installation      | [Installation Guide](docs/getting-started/installation.md)   |
| Configuration     | [Configuration Guide](docs/getting-started/configuration.md) |
| CLI Reference     | [CLI Reference Guide](docs/guides/cli-reference.md)          |
| Markdown Format   | [Markdown Format Guide](docs/guides/markdown-format.md)      |
| Architecture      | [Architecture Overview](docs/architecture/overview.md)       |
| Development Setup | [Development Setup](docs/development/setup.md)               |
| Testing Guide     | [Testing Guide](docs/development/testing.md)                 |
| Contributing      | [Contributing Guide](CONTRIBUTING.md)                        |

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. ✨ Any contributions you make are **greatly appreciated** — whether it's fixing a typo 📝, improving documentation 📚, squashing a bug 🐛, or proposing a new feature 🚀.

If you have an idea 💡, open an issue to discuss it first, then submit a pull request. New to the codebase? The [Contributing Guide](CONTRIBUTING.md) walks you through setup, conventions, and your first contribution. 🎉

## ⚖️ License

MIT — see [LICENSE](LICENSE).
