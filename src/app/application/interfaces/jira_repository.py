from abc import ABC, abstractmethod
from typing import Optional, List

from src.app.application.dtos.story_dtos import CreateStoryDtoRequest
from src.app.domain.entities import Epic, UserStory
from src.app.domain.value_objects import IssueId


class JiraRepository(ABC):
    """
    Interface (Port) for interacting with Jira data.

    This abstracts the data source, allowing the application layer
    to be independent of the specific Jira client implementation.
    """

    @abstractmethod
    async def get_epic(self, issue_id: IssueId) -> Optional[Epic]:
        """
        Retrieves an Epic by its IssueId.

        Args:
            issue_id: The identifier of the Epic.

        Returns:
            The Epic entity, or None if not found.
        """
        pass

    @abstractmethod
    async def create_epic(self, summary: str, description: str) -> Epic:
        """
        Creates a new Epic.

        Args:
            summary: Summary of the epic.
            description: Description of the epic.

        Returns:
            The created Epic entity, including the new ID.
        """
        pass

    @abstractmethod
    async def get_user_story(self, issue_id: IssueId) -> Optional[UserStory]:
        """
        Retrieves a User Story by its IssueId.

        Args:
            issue_id: The identifier of the User Story.

        Returns:
            The UserStory entity, or None if not found.
        """
        pass

    @abstractmethod
    async def get_stories_in_epic(self, epic_id: IssueId) -> List[UserStory]:
        """
        Retrieves all User Stories belonging to a specific Epic.

        Args:
            epic_id: The identifier of the parent Epic.

        Returns:
            A list of UserStory entities.
        """
        pass

    @abstractmethod
    async def find_epics_by_project(self, project_key: str) -> List[Epic]:
        """
        Finds all Epics within a given project.

        Args:
            project_key: The Jira project key.

        Returns:
            A list of Epic entities.
        """
        pass

    @abstractmethod
    async def update_story_status(self, issue_id: IssueId, new_status: str) -> None:
        """
        Updates the status of a User Story.

        Args:
            issue_id: The identifier of the User Story to update.
            new_status: The new status to set.
        """
        pass

    @abstractmethod
    async def create_story(self, request: CreateStoryDtoRequest) -> UserStory:
        """
        Creates a new User Story in Jira, linked to a parent epic.

        Args:
            request: The fields needed to create the story (summary,
                description, parent epic key, and optional estimate/labels).

        Returns:
            The created UserStory entity, including the new ID from Jira.
        """
        pass