import re
from dataclasses import dataclass, field
from typing import Optional

from src.app.domain.exceptions import BusinessRuleViolationException

_STORY_HEADING_RE = re.compile(r"^###\s+(?P<story_id>[^:]+):\s*(?P<title>.+)$")
_FIELD_RE = re.compile(r"^\*\*([^*]+)\*\*:\s*(.*)$")
_AS_A_RE = re.compile(r"^\*\*As(?: a)?\*\*\s*(.*)$")  # "As a <role>," or persona-named "As <Name>, a <role>,"
_WANT_RE = re.compile(r"^\*\*I want to\*\*\s*(.*)$")
_SO_THAT_RE = re.compile(r"^\*\*So that\*\*\s*(.*)$")
_ACCEPTANCE_HEADER_RE = re.compile(r"^\*\*Acceptance Criteria\*\*:?\s*$")
_CHECKLIST_ITEM_RE = re.compile(r"^[-*]\s+\[[ xX]\]\s+(.*)$")


@dataclass
class ParsedStory:
    """A single user story parsed from a project's `stories.md` file."""

    story_id: str
    title: str
    epic_key: str
    as_a: str
    i_want_to: str
    so_that: str
    acceptance_criteria: list[str] = field(default_factory=list)
    priority: Optional[str] = None
    story_points: Optional[int] = None


def parse_epic_markdown(markdown_content: str) -> tuple[str, str]:
    """
    Extracts ``(summary, description)`` from an Epic markdown document.

    Raises:
        BusinessRuleViolationException: If 'Epic Key' or 'Epic Title' is missing.
    """
    lines = markdown_content.splitlines()

    epic_key = None
    epic_title = None
    description_lines: list[str] = []

    for idx, line in enumerate(lines):
        if line.startswith("**Epic Key**:"):
            epic_key = line.split(":", 1)[1].strip()
        elif line.startswith("**Epic Title**:"):
            epic_title = line.split(":", 1)[1].strip()
        elif line.startswith("**Epic Description:**"):
            description_lines = lines[idx + 1:]

    if not epic_key or not epic_title:
        raise BusinessRuleViolationException(
            "Epic markdown is missing required fields",
            details="'Epic Key' and 'Epic Title' are required",
        )

    summary = f"{epic_key} - {epic_title}"
    description = "\n".join(line.strip() for line in description_lines).strip()
    return summary, description


def parse_stories_markdown(markdown_content: str) -> list[ParsedStory]:
    """
    Extracts all user stories from a `stories.md` document.

    Each story starts at a ``### <Story ID>: <Title>`` heading and runs until
    the next such heading (role sections, dividers, and optional sections
    like Deliverables/Dependencies/Success Metrics are ignored).

    Raises:
        BusinessRuleViolationException: If a story block is missing a
            required field ('Story ID', 'Epic Link', 'As a', 'I want to',
            'So that', or at least one Acceptance Criteria item).
    """
    lines = markdown_content.splitlines()
    block_start_indices = [
        idx for idx, line in enumerate(lines) if _STORY_HEADING_RE.match(line.strip())
    ]

    stories: list[ParsedStory] = []
    for position, start in enumerate(block_start_indices):
        end = (
            block_start_indices[position + 1]
            if position + 1 < len(block_start_indices)
            else len(lines)
        )
        stories.append(_parse_story_block(lines[start:end]))

    return stories


def build_story_description(story: ParsedStory) -> str:
    """Renders a ParsedStory's narrative and acceptance criteria back into markdown."""
    lines = [
        f"**As a** {story.as_a}",
        f"**I want to** {story.i_want_to}",
        f"**So that** {story.so_that}",
        "",
        "**Acceptance Criteria**",
        "",
    ]
    lines.extend(f"- [ ] {criterion}" for criterion in story.acceptance_criteria)
    return "\n".join(lines)


def _parse_story_block(block_lines: list[str]) -> ParsedStory:
    heading_match = _STORY_HEADING_RE.match(block_lines[0].strip())
    assert heading_match is not None  # guaranteed by parse_stories_markdown's block split
    heading_story_id = heading_match.group("story_id").strip()
    title = heading_match.group("title").strip()

    story_id: Optional[str] = None
    epic_key: Optional[str] = None
    priority: Optional[str] = None
    story_points: Optional[int] = None
    as_a: Optional[str] = None
    i_want_to: Optional[str] = None
    so_that: Optional[str] = None
    acceptance_criteria: list[str] = []

    collecting_acceptance_criteria = False

    for raw_line in block_lines[1:]:
        line = raw_line.strip()
        if not line:
            continue

        if collecting_acceptance_criteria:
            checklist_match = _CHECKLIST_ITEM_RE.match(line)
            if checklist_match:
                acceptance_criteria.append(checklist_match.group(1).strip())
                continue
            collecting_acceptance_criteria = False

        if _ACCEPTANCE_HEADER_RE.match(line):
            collecting_acceptance_criteria = True
            continue

        as_a_match = _AS_A_RE.match(line)
        if as_a_match:
            as_a = as_a_match.group(1).strip()
            continue

        want_match = _WANT_RE.match(line)
        if want_match:
            i_want_to = want_match.group(1).strip()
            continue

        so_that_match = _SO_THAT_RE.match(line)
        if so_that_match:
            so_that = so_that_match.group(1).strip()
            continue

        field_match = _FIELD_RE.match(line)
        if field_match:
            field_name = field_match.group(1).strip().lower()
            field_value = field_match.group(2).strip()
            if field_name == "story id":
                story_id = field_value
            elif field_name == "epic link":
                epic_key = field_value
            elif field_name == "priority":
                priority = field_value
            elif field_name == "effort estimate":
                try:
                    story_points = int(field_value)
                except ValueError:
                    story_points = None

    story_id = story_id or heading_story_id

    if not story_id or not epic_key or not as_a or not i_want_to or not so_that or not acceptance_criteria:
        raise BusinessRuleViolationException(
            "Story markdown is missing required fields",
            entity_key=story_id,
            details=(
                "'Story ID', 'Epic Link', 'As a', 'I want to', 'So that', and at least "
                "one Acceptance Criteria item are required"
            ),
        )

    return ParsedStory(
        story_id=story_id,
        title=title,
        epic_key=epic_key,
        priority=priority,
        story_points=story_points,
        as_a=as_a,
        i_want_to=i_want_to,
        so_that=so_that,
        acceptance_criteria=acceptance_criteria,
    )
