from datetime import datetime
from typing import Optional

from src.app.domain.entities import Epic, IssueStatus, UserStory
from src.app.infrastructure.external.jira.adf_to_markdown import adf_to_markdown

class JiraApiHelpers:
    @staticmethod
    def parse_jira_datetime(dt_str: str) -> datetime:
        """Parse Jira datetime format to a Python datetime object."""
        if dt_str[-5] in ('+', '-') and dt_str[-3] != ':':
            dt_str = dt_str[:-2] + ':' + dt_str[-2:]
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

    @staticmethod
    def _extract_description(data: dict) -> str:
        """
        Extracts a readable description from Jira API response data.

        Jira Cloud's GET issue API returns "description" as a full ADF
        object (dict), not a plain string - convert it to markdown text so
        it's actually readable rather than a raw dict repr.
        """
        return adf_to_markdown(data["fields"].get("description", ""))

    @staticmethod
    def map_epic(data: dict) -> Epic:
        """
        Map Jira API response data to the Epic domain entity.

        Args:
            data (dict): Jira API response data.

        Returns:
            Epic: The mapped Epic entity.
        """
        return Epic.create(
            key=data["key"],
            numeric_id=int(data["id"]),
            summary=data["fields"].get("summary", ""),
            description=JiraApiHelpers._extract_description(data),
            status=IssueStatus.from_jira_status(data["fields"]["status"]["name"]),
            created_at=JiraApiHelpers.parse_jira_datetime(data["fields"]["created"]),
            updated_at=JiraApiHelpers.parse_jira_datetime(data["fields"]["updated"]),
            reporter=data["fields"].get("reporter", {}).get("displayName"),
            priority=data["fields"].get("priority", {}).get("name") if data["fields"].get("priority") else None,
            labels=data["fields"].get("labels", []),
            story_points=data["fields"].get("customfield_10011"),
        )

    @staticmethod
    def map_user_story(data: dict, epic_key: Optional[str] = None) -> UserStory:
        """
        Map a Jira API issue response to the UserStory domain entity.

        Args:
            data (dict): Jira API response data.
            epic_key (Optional[str]): Parent epic key, when known from the
                creation/query context rather than the response payload.

        Returns:
            UserStory: The mapped UserStory entity.
        """
        return UserStory.create(
            key=data["key"],
            numeric_id=int(data["id"]),
            summary=data["fields"].get("summary", ""),
            description=JiraApiHelpers._extract_description(data),
            status=IssueStatus.from_jira_status(data["fields"]["status"]["name"]),
            created_at=JiraApiHelpers.parse_jira_datetime(data["fields"]["created"]),
            updated_at=JiraApiHelpers.parse_jira_datetime(data["fields"]["updated"]),
            reporter=data["fields"].get("reporter", {}).get("displayName"),
            priority=data["fields"].get("priority", {}).get("name") if data["fields"].get("priority") else None,
            labels=data["fields"].get("labels", []),
            story_points=data["fields"].get("customfield_10011"),
            epic_key=epic_key,
        )