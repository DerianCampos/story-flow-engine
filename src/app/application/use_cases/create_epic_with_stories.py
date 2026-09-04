from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.app.application.dtos.story_dtos import CreateStoryDtoRequest
from src.app.application.interfaces.jira_repository import JiraRepository
from src.app.application.parsers import build_story_description, parse_epic_markdown, parse_stories_markdown
from src.app.domain.entities import Epic
from src.app.domain.exceptions import BusinessRuleViolationException


@dataclass
class StoryUploadResult:
    """Outcome of creating a single story from a batch."""

    story_id: str
    success: bool
    key: Optional[str] = None
    error: Optional[str] = None


@dataclass
class CreateEpicWithStoriesResult:
    epic: Epic
    story_results: list[StoryUploadResult]


class CreateEpicWithStories:
    """
    Use case to load an epic and its stories from a folder of markdown files
    and create all of them in Jira, with stories linked to the new epic.

    Epic creation failures abort the whole operation (there is nothing to
    link stories to). Individual story creation failures are collected and
    do not stop the remaining stories from being attempted.
    """

    _EPIC_FILENAME = "epic.md"
    _STORIES_FILENAME = "stories.md"

    def __init__(self, jira_repository: JiraRepository):
        self.jira_repository = jira_repository

    async def execute(self, folder_path: str) -> CreateEpicWithStoriesResult:
        """
        Args:
            folder_path: Path to a folder containing `epic.md` and, optionally,
                `stories.md` (e.g. "data/EPIC-0-foundational").

        Raises:
            BusinessRuleViolationException: If the epic file is unreadable,
                malformed, or Jira rejects the epic creation.
        """
        folder = Path(folder_path)
        epic_markdown = self._read_required_file(folder / self._EPIC_FILENAME)

        summary, description = parse_epic_markdown(epic_markdown)
        epic = await self.jira_repository.create_epic(summary=summary, description=description)

        story_results = await self._create_stories(folder / self._STORIES_FILENAME, epic)

        return CreateEpicWithStoriesResult(epic=epic, story_results=story_results)

    async def _create_stories(self, stories_file: Path, epic: Epic) -> list[StoryUploadResult]:
        if not stories_file.exists():
            return []

        stories_markdown = stories_file.read_text()
        parsed_stories = parse_stories_markdown(stories_markdown)

        results: list[StoryUploadResult] = []
        for story in parsed_stories:
            try:
                request = CreateStoryDtoRequest(
                    summary=f"{story.story_id} - {story.title}",
                    description=build_story_description(story),
                    epic_key=epic.key,
                    story_points=story.story_points,
                )
                created_story = await self.jira_repository.create_story(request)
                results.append(
                    StoryUploadResult(story_id=story.story_id, success=True, key=created_story.key)
                )
            except BusinessRuleViolationException as e:
                results.append(StoryUploadResult(story_id=story.story_id, success=False, error=str(e)))

        return results

    @staticmethod
    def _read_required_file(path: Path) -> str:
        try:
            return path.read_text()
        except OSError as e:
            raise BusinessRuleViolationException(
                "Cannot read epic file", details=str(e)
            ) from e
