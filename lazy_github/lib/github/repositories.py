from functools import partial
from typing import Literal

from lazy_github.lib.github.client import GithubClient
from lazy_github.models.github import Repository

RepoTypeFilter = Literal["all"] | Literal["owner"] | Literal["member"]
SortDirection = Literal["asc"] | Literal["desc"]
RepositorySortKey = Literal["created"] | Literal["updated"] | Literal["pushed"] | Literal["full_name"]

# This would be 2500 repos with default page size, calm down
MAX_PAGES = 30


async def _list_for_page(
    client: GithubClient,
    repo_types: RepoTypeFilter,
    sort: RepositorySortKey,
    direction: SortDirection,
    per_page: int,
    page: int,
) -> tuple[list[Repository], bool]:
    """Retrieves a single page of Github repos matching the specified criteria"""
    headers = client.headers_with_auth_accept(cache_duration=client.config.cache.list_repos_ttl)
    query_params = {"type": repo_types, "direction": direction, "sort": sort, "page": page, "per_page": per_page}
    response = await client.get("/user/repos", headers=headers, params=query_params)
    response.raise_for_status()

    link_header = response.headers.get("link")
    more_pages_remaining = bool(link_header) and 'rel="next"' in link_header

    return [Repository(**r) for r in response.json()], more_pages_remaining


async def _list(
    client: GithubClient,
    repo_types: RepoTypeFilter,
    sort: RepositorySortKey = "full_name",
    direction: SortDirection = "asc",
    per_page: int = 50,
) -> list[Repository]:
    "Pulls all of the repositories associated with a user and handles pagination"
    repositories: list[Repository] = []

    for page in range(1, MAX_PAGES):
        repos_in_page, more_pages = await _list_for_page(client, repo_types, sort, direction, per_page, page)
        repositories.extend(repos_in_page)
        if not more_pages:
            break

    return repositories


list_all = partial(_list, repo_types="all")
list_owned = partial(_list, repo_types="owner")
list_member_of = partial(_list, repo_types="member")
