import httpx
import re
from typing import Dict, List, Any
from backend.config import settings

class GitHubService:
    """Service to handle fetching PR details, processing raw diffs, and writing code comments to GitHub PRs."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    @staticmethod
    async def get_access_token(code: str) -> str:
        """Exchanges the temporary GitHub authorization code for a permanent access token."""
        url = "https://github.com/login/oauth/access_token"
        headers = {"Accept": "application/json"}
        payload = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_REDIRECT_URI
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                raise Exception(f"GitHub token exchange failed: {response.text}")
            
            data = response.json()
            access_token = data.get("access_token")
            if not access_token:
                error_desc = data.get("error_description", "Unknown error")
                raise Exception(f"OAuth exchange returned no access token: {error_desc}")
            return access_token

    @staticmethod
    async def get_user_info(access_token: str) -> dict:
        """Fetches the GitHub profile info of the authenticated user."""
        url = "https://api.github.com/user"
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Failed to retrieve GitHub user details: {response.text}")
            return response.json()

    @staticmethod
    async def get_pr_diff(pr_url: str, access_token: str) -> str:
        """Parses the GitHub PR URL and fetches the raw diff content of the PR."""
        match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL format: {pr_url}")
        
        owner, repo, pr_number = match.groups()
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3.diff"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch PR diff content: {response.text}")
            return response.text

    @staticmethod
    async def post_review_comment(repo: str, pr_number: int, body: str, access_token: str) -> dict:
        """Posts a general top-level summary comment on the Pull Request."""
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {"body": body}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code not in (200, 201):
                raise Exception(f"Failed to post general review comment to GitHub: {response.text}")
            return response.json()

    @staticmethod
    async def post_inline_comment(repo: str, pr_number: int, commit_id: str, 
                                 path: str, line: int, body: str, access_token: str) -> dict:
        """Posts an inline code-review comment on a specific line within a file of the GitHub PR."""
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "body": body,
            "commit_id": commit_id,
            "path": path,
            "line": line,
            "side": "RIGHT"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code not in (200, 201):
                raise Exception(f"Failed to post inline file comment to GitHub: {response.text}")
            return response.json()

    async def fetch_pr_diff_instance(self, repo_name: str, pr_number: int) -> str:
        """Instance method helper to fetch the raw diff text of a specific Pull Request from GitHub."""
        return await self.get_pr_diff(f"https://github.com/{repo_name}/pull/{pr_number}", self.access_token)

    async def post_review_comment_instance(self, repo_name: str, pr_number: int, commit_id: str, 
                                          file_path: str, line_number: int, comment_body: str):
        """Instance method helper to post an inline review comment on a specific line within a file of the GitHub PR."""
        return await self.post_inline_comment(repo_name, pr_number, commit_id, file_path, line_number, comment_body, self.access_token)
