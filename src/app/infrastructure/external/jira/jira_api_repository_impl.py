from typing import List, Optional

import httpx
from src.app.infrastructure.external.jira.helpers import JiraApiHelpers

from src.app.application.interfaces.jira_repository import JiraRepository
from src.app.domain import UserStory
from src.app.domain.exceptions import UnauthorizedWorkspaceAccess, BusinessRuleViolationException
from src.app.shared.log_config import get_logger
from src.app.domain.entities import Epic, IssueStatus
from src.app.domain.value_objects import IssueId, Priority

logger = get_logger(__name__)


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
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description.strip()
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"name": "Epic"},
            }
        }

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

        return JiraApiHelpers.map_epic(data)

    async def get_user_story(self, issue_id: IssueId) -> Optional[UserStory]:
        pass

    async def get_stories_in_epic(self, epic_id: IssueId) -> List[UserStory]:
        pass

    async def find_epics_by_project(self, project_key: str) -> List[Epic]:
        if project_key != self.project_space_key:
            raise UnauthorizedWorkspaceAccess(project_key, self.project_space_key)
        # Implementation for fetching epics will go here.

    async def update_story_status(self, issue_id: IssueId, new_status: str) -> None:
        pass

    async def create_story(self, story: UserStory) -> UserStory:
        pass
