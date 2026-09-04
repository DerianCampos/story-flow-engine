import pytest

from src.app.application.parsers import (
    build_story_description,
    parse_epic_markdown,
    parse_stories_markdown,
)
from src.app.domain.exceptions import BusinessRuleViolationException

EPIC_MARKDOWN = """# Epic: Sample

**Epic Title**: Sample Epic
**Epic Key**: EPIC-0
**Labels**: foundational

---

**Epic Description:**
Problem Statement: Something is missing.

Included scope:

- One thing
- Another thing
"""

STORIES_MARKDOWN = """# Stories for Epic: Sample

## Backend Engineer

### US-EP0-BE-001: First Story

**Story ID**: US-EP0-BE-001
**Epic Link**: EPIC-0
**Priority**: Must Have
**Effort Estimate**: 8

**As a** Backend Engineer,
**I want to** do the first thing,
**So that** value is delivered.

**Acceptance Criteria**:

- [ ] Given X, then Y.
- [ ] Given A, then B.

**Deliverables**:

- Some deliverable.

---

### US-EP0-BE-002: Second Story

**Story ID**: US-EP0-BE-002
**Epic Link**: EPIC-0

**As a** Backend Engineer,
**I want to** do the second thing,
**So that** more value is delivered.

**Acceptance Criteria**:

- [ ] Given C, then D.
"""


class TestParseEpicMarkdown:
    def test_parses_summary_and_description(self):
        summary, description = parse_epic_markdown(EPIC_MARKDOWN)

        assert summary == "EPIC-0 - Sample Epic"
        assert "Problem Statement: Something is missing." in description
        assert "- One thing" in description

    def test_missing_required_fields_raises(self):
        with pytest.raises(BusinessRuleViolationException):
            parse_epic_markdown("# Epic: Sample\n\nNo fields here.")


class TestParseStoriesMarkdown:
    def test_parses_all_stories(self):
        stories = parse_stories_markdown(STORIES_MARKDOWN)

        assert len(stories) == 2
        first, second = stories

        assert first.story_id == "US-EP0-BE-001"
        assert first.title == "First Story"
        assert first.epic_key == "EPIC-0"
        assert first.priority == "Must Have"
        assert first.story_points == 8
        assert first.as_a == "Backend Engineer,"
        assert first.i_want_to == "do the first thing,"
        assert first.so_that == "value is delivered."
        assert first.acceptance_criteria == ["Given X, then Y.", "Given A, then B."]

        assert second.story_id == "US-EP0-BE-002"
        assert second.priority is None
        assert second.story_points is None
        assert second.acceptance_criteria == ["Given C, then D."]

    def test_no_stories_returns_empty_list(self):
        assert parse_stories_markdown("# Stories for Epic: Sample\n\nNothing here.") == []

    def test_parses_persona_named_as_phrasing(self):
        persona_story = """### US-EP4-CLI-001: Guided Import Flow

**Story ID**: US-EP4-CLI-001
**Epic Link**: EPIC-4

**As** Maya, a Solo/Small-Team Developer,
**I want to** run one guided import command,
**So that** I never lose track of what's about to happen.

**Acceptance Criteria**:

- [ ] Given a valid folder, then it imports successfully.
"""
        stories = parse_stories_markdown(persona_story)

        assert len(stories) == 1
        assert stories[0].as_a == "Maya, a Solo/Small-Team Developer,"

    def test_missing_required_field_raises(self):
        broken = """### US-EP0-BE-001: Broken Story

**Story ID**: US-EP0-BE-001
**Epic Link**: EPIC-0

**As a** Backend Engineer,
**I want to** do the thing,

**Acceptance Criteria**:

- [ ] Given X, then Y.
"""
        with pytest.raises(BusinessRuleViolationException):
            parse_stories_markdown(broken)

    def test_missing_acceptance_criteria_raises(self):
        broken = """### US-EP0-BE-001: Broken Story

**Story ID**: US-EP0-BE-001
**Epic Link**: EPIC-0

**As a** Backend Engineer,
**I want to** do the thing,
**So that** value is delivered.
"""
        with pytest.raises(BusinessRuleViolationException):
            parse_stories_markdown(broken)


class TestBuildStoryDescription:
    def test_renders_narrative_and_checklist(self):
        stories = parse_stories_markdown(STORIES_MARKDOWN)
        description = build_story_description(stories[0])

        assert "**As a** Backend Engineer," in description
        assert "**I want to** do the first thing," in description
        assert "**So that** value is delivered." in description
        assert "- [ ] Given X, then Y." in description
        assert "- [ ] Given A, then B." in description
