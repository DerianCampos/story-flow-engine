from typing import List, Optional

import httpx
from src.app.infrastructure.external.jira.helpers import JiraApiHelpers
from src.app.infrastructure.external.jira.markdown_to_adf import markdown_to_adf

from src.app.application.dtos.story_dtos import CreateStoryDtoRequest
from src.app.application.interfaces.jira_repository import JiraRepository
from src.app.domain import UserStory
from src.app.domain.exceptions import UnauthorizedWorkspaceAccess, BusinessRuleViolationException
from src.app.infrastructure.logging.logger import AppLogger
from src.app.domain.entities import Epic, IssueStatus
from src.app.domain.value_objects import IssueId, Priority

# TBD (specs/2026-09-03-epic-story-jira-upload-with-adf-formatting.md, Phase 1):
# confirm against the target Jira project's actual issue type scheme before
# relying on this in production.
_STORY_ISSUE_TYPE = "Story"
# Story points are intentionally not sent on story creation: customfield_10011
# (the epic's story-points field) is confirmed NOT valid for the Story issue
# type's create screen on this Jira project ("Field 'customfield_10011'
# cannot be set. It is not on the appropriate screen, or unknown."). Wire the
# correct field once it's identified for stories specifically.


class JiraApiRepositoryImpl(JiraRepository):
    def __init__(self, jira_config: dict):
        """
        Initialize the JiraApiRepository with configuration from AppConfig.

        Args:
            jira_config (dict): A dictionary containing Jira configuration parameters such as:
                - base_url: The base URL of the Jira instance.
                - email: The email address of the Jira instance.
                - api_token: The API token of the Jira instance.
                - project_space_key: The project space key of the Jira instance.
        """
        self.base_url = jira_config.get("base_url")
        self.email = jira_config.get("email")
        self.api_token = jira_config.get("api_token")
        self.project_space_key = jira_config.get("project_key")

    async def get_epic(self, issue_id: IssueId) -> Optional[Epic]:
        """
        Retrieve details of an epic by its key from Jira.

        Args:
            issue_id (IssueId): The IssueId of the epic to retrieve.

        Returns:
            Epic: The Epic domain entity.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_id.key}"
        logger = AppLogger.instance()
        logger.info("Making JIRA API call", extra={"email": self.email, "url": url})

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                auth=(self.email, self.api_token),
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
        data = response.json()
        logger.info("Raw JIRA API response", extra={"response": data})

        return JiraApiHelpers.map_epic(data)

    async def create_epic(self, summary: str, description: str) -> Epic:
        """
        Create a new Epic in Jira.

        Args:
            summary (str): Summary of the epic.
            description (str): Description of the epic.

        Returns:
            Epic: The created Epic.

        Raises:
            BusinessRuleViolationException: If the creation fails due to invalid input or configuration.
        """
        url = f"{self.base_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_space_key},
                "summary": summary,
                "description": markdown_to_adf(description),
                "issuetype": {"name": "Epic"},
            }
        }

        logger = AppLogger.instance()
        logger.info("Creating a new Epic in Jira", extra={"payload": payload})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, auth=(self.email, self.api_token), json=payload
            )

        if response.status_code != 201:
            error_message = response.json().get('errorMessages', ['Unknown error'])
            logger.error("Failed to create Epic in Jira", extra={"response_body": response.text})
            raise BusinessRuleViolationException(
                f"Failed to create an Epic: {error_message}",
                details=response.json().get("errors", {}),
            )

        data = response.json()
        logger.info("Epic successfully created in Jira", extra={"response": data})

        # Jira's issue create response only contains {id, key, self}, not the
        # full "fields" object, so fetch the created issue to map it fully.
        created_epic = await self.get_epic(IssueId(key=data["key"], numeric_id=int(data["id"])))
        if created_epic is None:
            raise BusinessRuleViolationException(
                "Epic was created in Jira but could not be re-fetched", entity_key=data["key"]
            )
        return created_epic

    async def get_user_story(self, issue_id: IssueId) -> Optional[UserStory]:
        """
        Retrieve details of a User Story by its key from Jira.

        Args:
            issue_id (IssueId): The IssueId of the story to retrieve.

        Returns:
            UserStory: The User Story domain entity, or None if not found.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_id.key}"
        logger = AppLogger.instance()
        logger.info("Making JIRA API call", extra={"email": self.email, "url": url})

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                auth=(self.email, self.api_token),
                headers={"Accept": "application/json"},
            )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        data = response.json()
        logger.info("Raw JIRA API response", extra={"response": data})

        epic_key = data["fields"].get("parent", {}).get("key")
        return JiraApiHelpers.map_user_story(data, epic_key=epic_key)

    async def get_stories_in_epic(self, epic_id: IssueId) -> List[UserStory]:
        """
        Retrieve all user stories whose parent is the given epic.

        Args:
            epic_id (IssueId): The IssueId of the parent epic.

        Returns:
            List[UserStory]: Stories linked to the epic (empty if none).

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        jql = f'parent = "{epic_id.key}" AND issuetype = "{_STORY_ISSUE_TYPE}"'
        # Jira Cloud deprecated GET/POST /rest/api/3/search (now 410 Gone) in
        # favor of /rest/api/3/search/jql.
        url = f"{self.base_url}/rest/api/3/search/jql"
        logger = AppLogger.instance()
        logger.info("Fetching stories for epic", extra={"epic_key": epic_id.key})

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                auth=(self.email, self.api_token),
                headers={"Accept": "application/json"},
                params={
                    "jql": jql,
                    "maxResults": 100,
                    # Jira's search endpoint doesn't return full fields by
                    # default the way a single-issue GET does - request
                    # exactly what the mapper needs.
                    "fields": "summary,description,status,created,updated,"
                              "reporter,priority,labels,customfield_10011,parent",
                },
            )
        response.raise_for_status()
        data = response.json()

        return [
            JiraApiHelpers.map_user_story(issue, epic_key=epic_id.key)
            for issue in data.get("issues", [])
        ]

    async def find_epics_by_project(self, project_key: str) -> List[Epic]:
        if project_key != self.project_space_key:
            raise UnauthorizedWorkspaceAccess(project_key, self.project_space_key)
        # Implementation for fetching epics will go here.

    async def update_story_status(self, issue_id: IssueId, new_status: str) -> None:
        pass

    async def create_story(self, request: CreateStoryDtoRequest) -> UserStory:
        """
        Create a new User Story in Jira, linked to a parent epic.

        Args:
            request: Fields needed to create the story (summary, description,
                parent epic key, optional story points).

        Returns:
            UserStory: The created User Story.

        Raises:
            BusinessRuleViolationException: If the creation fails due to
                invalid input or configuration.
        """
        url = f"{self.base_url}/rest/api/3/issue"
        fields = {
            "project": {"key": self.project_space_key},
            "summary": request.summary,
            "description": markdown_to_adf(request.description),
            "issuetype": {"name": _STORY_ISSUE_TYPE},
            # TBD (specs/2026-09-03-epic-story-jira-upload-with-adf-formatting.md,
            # Phase 1): "parent" links a story to its epic on team-managed Jira
            # projects; company-managed projects may need a dedicated Epic Link
            # custom field instead. Confirm against the real project before relying
            # on this in production.
            "parent": {"key": request.epic_key},
        }

        payload = {"fields": fields}

        logger = AppLogger.instance()
        logger.info("Creating a new Story in Jira", extra={"epic_key": request.epic_key})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, auth=(self.email, self.api_token), json=payload
            )

        if response.status_code != 201:
            error_message = response.json().get('errorMessages', ['Unknown error'])
            logger.error("Failed to create Story in Jira", extra={"response_body": response.text})
            raise BusinessRuleViolationException(
                f"Failed to create a Story: {error_message}",
                details=response.json().get("errors", {}),
            )

        data = response.json()
        logger.info("Story successfully created in Jira", extra={"response": data})

        # Jira's issue create response only contains {id, key, self}, not the
        # full "fields" object, so fetch the created issue to map it fully.
        created_story = await self.get_user_story(IssueId(key=data["key"], numeric_id=int(data["id"])))
        if created_story is None:
            raise BusinessRuleViolationException(
                "Story was created in Jira but could not be re-fetched", entity_key=data["key"]
            )
        return created_story
