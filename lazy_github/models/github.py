from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class User(BaseModel):
    login: str
    id: int
    name: str | None = None
    html_url: str
    followers: int | None = None
    following: int | None = None


class RepositoryPermission(BaseModel):
    admin: bool
    maintain: bool
    push: bool
    triage: bool
    pull: bool


class Repository(BaseModel):
    name: str
    full_name: str
    default_branch: str
    private: bool
    archived: bool
    owner: User
    description: str | None = None
    permissions: RepositoryPermission | None = None


class IssueState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class Issue(BaseModel):
    id: int
    number: int
    comments: int
    locked: bool
    state: IssueState
    title: str
    body: str | None = None
    user: User
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None
    closed_by: User | None = None
    assignee: User | None = None
    assignees: list[User] | None
    repo: Repository


class Ref(BaseModel):
    user: User
    ref: str


class PartialPullRequest(Issue):
    """
    A pull request that may be included in the response to a list issues API call and is missing some information
    """

    draft: bool


class FullPullRequest(PartialPullRequest):
    """More comprehensive details on a pull request from the API"""

    additions: int
    deletions: int
    changed_files: int
    commits: int
    head: Ref
    base: Ref
    html_url: str
    merged_at: datetime | None
