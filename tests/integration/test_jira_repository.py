import pytest
import respx
from httpx import Response
from src.app.application.dtos.story_dtos import CreateStoryDtoRequest
from src.app.domain.entities import Epic, UserStory
from src.app.domain.value_objects import IssueId, Priority
from src.app.infrastructure.external.jira.jira_api_repository_impl import JiraApiRepositoryImpl
from src.app.domain.exceptions import BusinessRuleViolationException
from datetime import datetime


@pytest.fixture
def jira_repository():
    """
    Fixture to create a JiraApiRepository instance for testing.
    """
    jira_config = {
        "base_url": "https://test-jira.atlassian.net",
        "email": "test@example.com",
        "api_token": "test_key",
        "project_key": "PROJ-1",
    }

    return JiraApiRepositoryImpl(jira_config)


@pytest.mark.asyncio
@respx.mock
async def test_get_epic_success(jira_repository):
    """
    Test successful retrieval of an Epic from the Jira API.
    """
    # Arrange
    epic_key = "PROJ-1"
    mock_response = {
        "id": "10001",
        "key": epic_key,
        "fields": {
            "summary": "Test Epic from API",
            "description": "A detailed description.",
            "status": {"name": "To Do"},
            "creator": {"displayName": "Test User"},
            "reporter": {"displayName": "Test User"},
            "priority": {"name": "High"},
            "labels": ["backend", "api"],
            "customfield_10011": 8.0,  # Story Points
            "created": "2025-01-01T10:00:00.000-0500",
            "updated": "2025-01-02T11:00:00.000-0500",
        },
    }

    respx.get(
        f"https://test-jira.atlassian.net/rest/api/3/issue/{epic_key}"
    ).mock(
        return_value=Response(200, json=mock_response)
    )

    # Act
    epic = await jira_repository.get_epic(IssueId.from_string(epic_key))

    # Assert
    assert epic is not None
    assert isinstance(epic, Epic)
    assert epic.key == epic_key
    assert epic.summary == "Test Epic from API"
    assert epic.story_points.value == 8
    assert len(epic.labels) == 2
    assert epic.labels.has_label_named("backend")


@pytest.mark.asyncio
@respx.mock
async def test_get_user_story_success(jira_repository):
    """
    Test successful retrieval of a User Story from the Jira API.
    """
    # Arrange
    story_key = "PROJ-101"
    mock_response = {
        "id": "10002",
        "key": story_key,
        "fields": {
            "summary": "Test Story from API",
            "description": "A detailed description.",
            "status": {"name": "To Do"},
            "reporter": {"displayName": "Test User"},
            "parent": {"key": "PROJ-100"},
            "created": "2025-01-01T10:00:00.000-0500",
            "updated": "2025-01-02T11:00:00.000-0500",
        },
    }

    respx.get(f"https://test-jira.atlassian.net/rest/api/3/issue/{story_key}").mock(
        return_value=Response(200, json=mock_response)
    )

    # Act
    story = await jira_repository.get_user_story(IssueId.from_string(story_key))

    # Assert
    assert story is not None
    assert isinstance(story, UserStory)
    assert story.key == story_key
    assert story.summary == "Test Story from API"
    assert story.epic_link.key == "PROJ-100"


@pytest.mark.asyncio
@respx.mock
async def test_get_user_story_not_found(jira_repository):
    """
    Test retrieval of a non-existent User Story returns None.
    """
    story_key = "PROJ-404"
    respx.get(f"https://test-jira.atlassian.net/rest/api/3/issue/{story_key}").mock(
        return_value=Response(404, json={"errorMessages": ["Issue does not exist"]})
    )

    story = await jira_repository.get_user_story(IssueId.from_string(story_key))

    assert story is None


@pytest.mark.asyncio
@respx.mock
async def test_get_epic_with_adf_description(jira_repository):
    """
    Jira Cloud's GET issue API returns "description" as an ADF object, not
    a plain string - confirm it's converted to readable markdown, not left
    as a raw dict.
    """
    epic_key = "PROJ-1"
    mock_response = {
        "id": "10001",
        "key": epic_key,
        "fields": {
            "summary": "Test Epic from API",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Release Checklist"}]},
                    {
                        "type": "bulletList",
                        "content": [
                            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "First item"}]}]}
                        ],
                    },
                ],
            },
            "status": {"name": "To Do"},
            "created": "2025-01-01T10:00:00.000-0500",
            "updated": "2025-01-02T11:00:00.000-0500",
        },
    }

    respx.get(f"https://test-jira.atlassian.net/rest/api/3/issue/{epic_key}").mock(
        return_value=Response(200, json=mock_response)
    )

    epic = await jira_repository.get_epic(IssueId.from_string(epic_key))

    assert isinstance(epic.description, str)
    assert "{'type': 'doc'" not in epic.description
    assert "## Release Checklist" in epic.description
    assert "- First item" in epic.description


@pytest.mark.asyncio
@respx.mock
async def test_get_stories_in_epic_success(jira_repository):
    """
    Test successful retrieval of stories linked to an epic via JQL search.
    """
    epic_key = "PROJ-100"
    mock_response = {
        "issues": [
            {
                "id": "10002",
                "key": "PROJ-101",
                "fields": {
                    "summary": "First Story",
                    "description": "Desc",
                    "status": {"name": "To Do"},
                    "created": "2026-01-01T10:00:00.000-0500",
                    "updated": "2026-01-01T11:00:00.000-0500",
                },
            },
            {
                "id": "10003",
                "key": "PROJ-102",
                "fields": {
                    "summary": "Second Story",
                    "description": "Desc",
                    "status": {"name": "In Progress"},
                    "created": "2026-01-01T10:00:00.000-0500",
                    "updated": "2026-01-01T11:00:00.000-0500",
                },
            },
        ]
    }

    respx.get("https://test-jira.atlassian.net/rest/api/3/search/jql").mock(
        return_value=Response(200, json=mock_response)
    )

    stories = await jira_repository.get_stories_in_epic(IssueId.from_string(epic_key))

    assert len(stories) == 2
    assert stories[0].key == "PROJ-101"
    assert stories[0].epic_link.key == epic_key
    assert stories[1].key == "PROJ-102"


@pytest.mark.asyncio
@respx.mock
async def test_get_stories_in_epic_empty(jira_repository):
    """
    Test an epic with no linked stories returns an empty list.
    """
    respx.get("https://test-jira.atlassian.net/rest/api/3/search/jql").mock(
        return_value=Response(200, json={"issues": []})
    )

    stories = await jira_repository.get_stories_in_epic(IssueId.from_string("PROJ-100"))

    assert stories == []


@pytest.mark.asyncio
@respx.mock
async def test_create_epic_success(jira_repository):
    """
    Test successful creation of an Epic in the Jira API.
    """
    # Arrange
    epic_key = "PROJ-100"

    # Jira's issue create response only contains {id, key, self}, not the
    # full "fields" object - the repository re-fetches the created issue.
    create_response = {"id": "10001", "key": epic_key, "self": "https://test-jira.atlassian.net/rest/api/3/issue/10001"}
    fetched_response = {
        "id": "10001",
        "key": epic_key,
        "fields": {
            "summary": "Test Epic Creation",
            "description": "A test epic for unit testing integration with Jira.",
            "priority": {"name": "High"},
            "status": {"name": "To Do"},
            "created": "2026-01-01T10:00:00.000-0500",
            "updated": "2026-01-01T11:00:00.000-0500",
        },
    }

    respx.post("https://test-jira.atlassian.net/rest/api/3/issue").mock(
        return_value=Response(201, json=create_response)
    )
    respx.get(f"https://test-jira.atlassian.net/rest/api/3/issue/{epic_key}").mock(
        return_value=Response(200, json=fetched_response)
    )

    # Act
    epic = await jira_repository.create_epic(
        summary="Test Epic Creation",
        description="A test epic for unit testing integration with Jira."
    )

    # Assert
    assert epic is not None
    assert isinstance(epic, Epic)
    assert epic.key == epic_key
    assert epic.summary == "Test Epic Creation"
    assert epic.description == "A test epic for unit testing integration with Jira."
    assert epic.priority == Priority.high()
    assert epic.created_at == datetime.fromisoformat("2026-01-01T10:00:00-05:00")
    assert epic.updated_at == datetime.fromisoformat("2026-01-01T11:00:00-05:00")


@pytest.mark.asyncio
@respx.mock
async def test_create_epic_unauthorized(jira_repository):
    """
    Test Epic creation fails with 401 Unauthorized.
    """
    # Arrange
    respx.post("https://test-jira.atlassian.net/rest/api/3/issue").mock(
        return_value=Response(401, json={"errorMessages": ["Unauthorized"], "errors": {}})
    )

    # Act & Assert
    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await jira_repository.create_epic(
            summary="Unauthorized Epic",
            description="Testing unauthorized response handling."
        )

    assert "Unauthorized" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_create_epic_internal_server_error(jira_repository):
    """
    Test Epic creation fails with 500 Internal Server Error.
    """
    # Arrange
    respx.post("https://test-jira.atlassian.net/rest/api/3/issue").mock(
        return_value=Response(500, json={"errorMessages": ["Internal Server Error"], "errors": {}})
    )

    # Act & Assert
    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await jira_repository.create_epic(
            summary="Epic causing 500",
            description="Testing internal server error handling."
        )

    assert "Internal Server Error" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_create_epic_invalid_payload(jira_repository):
    """
    Test Epic creation fails with 400 Bad Request due to invalid payload.
    """
    # Arrange
    respx.post("https://test-jira.atlassian.net/rest/api/3/issue").mock(
        return_value=Response(400, json={"errorMessages": ["Invalid payload"], "errors": {"summary": "Summary is required"}})
    )

    # Act & Assert
    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await jira_repository.create_epic(
            summary="",  # Invalid because the summary is empty
            description="Epic with invalid payload."
        )

    assert "Invalid payload" in str(exc_info.value)
    assert "Summary is required" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_create_story_success(jira_repository):
    """
    Test successful creation of a Story in the Jira API, linked to its epic.
    """
    # Arrange
    story_key = "PROJ-101"

    # Jira's issue create response only contains {id, key, self}, not the
    # full "fields" object - the repository re-fetches the created issue.
    create_response = {"id": "10002", "key": story_key, "self": "https://test-jira.atlassian.net/rest/api/3/issue/10002"}
    fetched_response = {
        "id": "10002",
        "key": story_key,
        "fields": {
            "summary": "US-EP0-BE-001 - Backend Scaffolding",
            "description": "**As a** Backend Engineer",
            "status": {"name": "To Do"},
            "reporter": {"displayName": "Test User"},
            "parent": {"key": "PROJ-100"},
            "created": "2026-01-01T10:00:00.000-0500",
            "updated": "2026-01-01T11:00:00.000-0500",
        },
    }

    respx.post("https://test-jira.atlassian.net/rest/api/3/issue").mock(
        return_value=Response(201, json=create_response)
    )
    respx.get(f"https://test-jira.atlassian.net/rest/api/3/issue/{story_key}").mock(
        return_value=Response(200, json=fetched_response)
    )

    request = CreateStoryDtoRequest(
        summary="US-EP0-BE-001 - Backend Scaffolding",
        description="**As a** Backend Engineer",
        epic_key="PROJ-100",
        story_points=8,
    )

    # Act
    story = await jira_repository.create_story(request)

    # Assert
    assert isinstance(story, UserStory)
    assert story.key == story_key
    assert story.epic_link.key == "PROJ-100"


@pytest.mark.asyncio
@respx.mock
async def test_create_story_invalid_payload(jira_repository):
    """
    Test Story creation fails with 400 Bad Request due to invalid payload.
    """
    respx.post("https://test-jira.atlassian.net/rest/api/3/issue").mock(
        return_value=Response(
            400,
            json={"errorMessages": ["Invalid payload"], "errors": {"parent": "Parent is invalid"}},
        )
    )

    request = CreateStoryDtoRequest(
        summary="Bad Story",
        description="Description",
        epic_key="PROJ-999",
    )

    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await jira_repository.create_story(request)

    assert "Invalid payload" in str(exc_info.value)
    assert "Parent is invalid" in str(exc_info.value)