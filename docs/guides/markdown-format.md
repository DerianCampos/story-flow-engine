# Markdown Format Specification

Story Flow Engine parses structured Markdown files to create Jira issues. This document defines the supported format for epics and user stories.

## Directory Convention

Place your epics and stories under `data/` using this structure:

```
data/
├── EPIC-0-foundational/
│   ├── epic.md          # Epic definition
│   └── stories.md       # User stories belonging to this epic
├── EPIC-1-my-feature/
│   ├── epic.md
│   └── stories.md
└── ...
```

- One subdirectory per epic, named `EPIC-N-description`
- Each directory contains `epic.md` and `stories.md`
- Use `data/.gitkeep` to track the directory in version control

## Epic Format (`epic.md`)

### Required Fields (used by `create_epic`)

| Field                   | Description                | Example                                              |
| ----------------------- | -------------------------- | ---------------------------------------------------- |
| `**Epic Key**`          | Unique identifier          | `EPIC-0`                                             |
| `**Epic Title**`        | Human-readable title       | `Project and Local Development Setup (Foundational)` |
| `**Epic Description:**` | Detailed description block | Multi-line text after the heading                    |

### Optional Fields (recognized but not yet pushed to Jira)

| Field             | Description               | Example                                       |
| ----------------- | ------------------------- | --------------------------------------------- |
| `**Summary**`     | Short summary of the epic | `Establish foundational project structure...` |
| `**Labels**`      | Comma-separated labels    | `foundational, setup, ci-cd`                  |
| `**Priority**`    | Priority level            | `Must Have`                                   |
| `**Components**`  | Jira components           | `Backend, Frontend, Database`                 |
| `**Fix Version**` | Target fix version        | `MVP-1`                                       |

### Full Example

```markdown
# Epic: Project and Local Development Setup (Foundational)

**Epic Title**: Project and Local Development Setup (Foundational)
**Epic Key**: EPIC-0
**Summary**: Establish foundational project structure, local environment setup, and deployment baseline.
**Labels**: foundational, setup, ci-cd
**Priority**: Must Have
**Components**: Backend, Frontend, Database
**Fix Version**: MVP-1

---

**Epic Description:**
Problem Statement: Delivery teams cannot begin engineering work until the
development environment, CI/CD, database schema, seed data, and deployment
foundations are configured.

Objective: Establish the foundational project structure, local environment
setup, and deployment baseline so all engineering teams can work in parallel
on MVP features downstream.

Included scope:

- Repository structure and folder organization
- Local development environment setup (Python, Node.js, Docker, database)
- CI/CD pipeline scaffolding and basic testing framework integration

Excluded scope:

- Feature-specific implementation beyond structure and scaffolding
- Advanced deployment automation or multi-region strategies

Measurable success criteria:

- Every engineer can clone and run local dev environments in under 15 minutes.
- CI/CD pipeline runs on every commit and reports clear pass/fail status.
```

### How It's Parsed

The `create_epic` command reads the file line by line and extracts:

1. **Epic Key** — from `**Epic Key**:`
2. **Epic Title** — from `**Epic Title**:`
3. **Epic Description** — all lines after `**Epic Description:**`

The Jira issue summary is built as: `{Epic Key} - {Epic Title}`

The description block is joined and sent as plain text in a Jira paragraph node.

> **Note**: Epic Key, Title, Description, and Labels are parsed and sent to Jira. Priority, Components, and Fix Version in the Markdown are recognized but not yet passed to the Jira API.

## User Story Format (`stories.md`)

### Full Example

```markdown
# Stories for Epic: Foundational Infrastructure and Setup

## Backend Engineer

### US-EP0-BE-001: Backend Modular Monolith Structure and Scaffolding

**Story ID**: US-EP0-BE-001
**Epic Link**: EPIC-0
**Priority**: Must Have
**Effort Estimate**: 8

**As a** Backend Engineer,
**I want to** establish a backend modular monolith repository structure,
**So that** all team members can develop and test code consistently.

**Acceptance Criteria**:

- [ ] Given the backend repository is cloned, then folder structure includes
      modules/, shared/, config/, and tests/ directories.
- [ ] Given a developer runs setup script, then all dependencies are installed
      and project is ready for local development.

**Deliverables**:

- Backend repository root with modules/, shared/, config/, and tests/ directories.
- Setup script for fast local environment configuration.

**Dependencies**:

- [Architecture Solution Design](../../03-architecture/architecture-solution-design.md).

**Success Metrics**:

- First-time setup completes in under 15 minutes.
- All imports follow agreed pattern.
```

### User Story Fields

| Field                      | Required | Description                         |
| -------------------------- | -------- | ----------------------------------- |
| `### US-EP0-BE-001: Title` | Yes      | H3 heading with story ID and title  |
| `**Story ID**`             | Yes      | Unique story identifier             |
| `**Epic Link**`            | Yes      | Parent epic key                     |
| `**Priority**`             | Optional | Priority level                      |
| `**Effort Estimate**`      | Optional | Story points or hours               |
| `**Labels**`               | Optional | Comma-separated labels, sent to Jira |
| `**As a**`                 | Yes      | User role                           |
| `**I want to**`            | Yes      | Desired capability                  |
| `**So that**`              | Yes      | Business value                      |
| `**Acceptance Criteria**`  | Yes      | Checklist of gherkin-style criteria |
| `**Deliverables**`         | Optional | Expected outputs                    |
| `**Dependencies**`         | Optional | Links to related docs or issues     |
| `**Success Metrics**`      | Optional | Measurable outcomes                 |
