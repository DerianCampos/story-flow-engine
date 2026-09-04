from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.app.application.use_cases import CreateEpicWithStories
from src.app.domain.entities import Epic, IssueStatus, UserStory
from src.app.domain.exceptions import BusinessRuleViolationException


@pytest.fixture
def mock_jira_repo():
    return AsyncMock()


@pytest.fixture
def epic_folder(tmp_path):
    folder = tmp_path / "EPIC-0-foundational"
    folder.mkdir()
    (folder / "epic.md").write_text(
        "**Epic Title**: Sample Epic\n"
        "**Epic Key**: EPIC-0\n"
        "\n---\n\n"
        "**Epic Description:**\n"
        "Some description.\n"
    )
    (folder / "stories.md").write_text(
        "### US-EP0-BE-001: First Story\n\n"
        "**Story ID**: US-EP0-BE-001\n"
        "**Epic Link**: EPIC-0\n"
        "**Effort Estimate**: 5\n\n"
        "**As a** Engineer,\n"
        "**I want to** do the thing,\n"
        "**So that** value is delivered.\n\n"
        "**Acceptance Criteria**:\n\n"
        "- [ ] Given X, then Y.\n\n"
        "---\n\n"
        "### US-EP0-BE-002: Second Story\n\n"
        "**Story ID**: US-EP0-BE-002\n"
        "**Epic Link**: EPIC-0\n\n"
        "**As a** Engineer,\n"
        "**I want to** do another thing,\n"
        "**So that** more value is delivered.\n\n"
        "**Acceptance Criteria**:\n\n"
        "- [ ] Given A, then B.\n"
    )
    return folder


def _make_epic(key: str = "PROJ-1") -> Epic:
    return Epic.create(
        key=key,
        numeric_id=1,
        summary="EPIC-0 - Sample Epic",
        description="Some description.",
        status=IssueStatus.TODO,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def _make_story(key: str) -> UserStory:
    return UserStory.create(
        key=key,
        numeric_id=2,
        summary="A story",
        description="Desc",
        status=IssueStatus.TODO,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.mark.asyncio
class TestCreateEpicWithStories:
    async def test_creates_epic_and_all_stories(self, mock_jira_repo, epic_folder):
        mock_jira_repo.create_epic.return_value = _make_epic("PROJ-1")
        mock_jira_repo.create_story.side_effect = [
            _make_story("PROJ-2"),
            _make_story("PROJ-3"),
        ]

        use_case = CreateEpicWithStories(jira_repository=mock_jira_repo)
        result = await use_case.execute(str(epic_folder))

        assert result.epic.key == "PROJ-1"
        assert len(result.story_results) == 2
        assert all(r.success for r in result.story_results)
        assert [r.key for r in result.story_results] == ["PROJ-2", "PROJ-3"]

        mock_jira_repo.create_epic.assert_called_once_with(
            summary="EPIC-0 - Sample Epic", description="Some description."
        )
        assert mock_jira_repo.create_story.call_count == 2
        first_request = mock_jira_repo.create_story.call_args_list[0].args[0]
        assert first_request.epic_key == "PROJ-1"
        assert first_request.story_points == 5

    async def test_continues_after_a_story_failure(self, mock_jira_repo, epic_folder):
        mock_jira_repo.create_epic.return_value = _make_epic("PROJ-1")
        mock_jira_repo.create_story.side_effect = [
            BusinessRuleViolationException("Failed to create a Story: bad payload"),
            _make_story("PROJ-3"),
        ]

        use_case = CreateEpicWithStories(jira_repository=mock_jira_repo)
        result = await use_case.execute(str(epic_folder))

        assert mock_jira_repo.create_story.call_count == 2
        first, second = result.story_results
        assert first.success is False
        assert "bad payload" in first.error
        assert second.success is True
        assert second.key == "PROJ-3"

    async def test_missing_stories_file_creates_epic_only(self, mock_jira_repo, epic_folder):
        (epic_folder / "stories.md").unlink()
        mock_jira_repo.create_epic.return_value = _make_epic("PROJ-1")

        use_case = CreateEpicWithStories(jira_repository=mock_jira_repo)
        result = await use_case.execute(str(epic_folder))

        assert result.story_results == []
        mock_jira_repo.create_story.assert_not_called()

    async def test_missing_epic_file_raises(self, mock_jira_repo, tmp_path):
        empty_folder = tmp_path / "empty"
        empty_folder.mkdir()

        use_case = CreateEpicWithStories(jira_repository=mock_jira_repo)

        with pytest.raises(BusinessRuleViolationException):
            await use_case.execute(str(empty_folder))

        mock_jira_repo.create_epic.assert_not_called()
