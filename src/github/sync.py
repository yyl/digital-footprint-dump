"""Sync manager for GitHub activity data."""

from typing import Optional, Dict, Any

from .database import GitHubDatabase
from .api_client import GitHubActivityClient


class GitHubSyncManager:
    """Orchestrates synchronization between GitHub API and local database."""
    
    def __init__(
        self,
        db: Optional[GitHubDatabase] = None,
        api: Optional[GitHubActivityClient] = None,
    ):
        """Initialize sync manager.
        
        Args:
            db: Database manager instance.
            api: API client instance.
        """
        self.db = db or GitHubDatabase()
        self.api = api or GitHubActivityClient()
    
    def sync(self) -> Dict[str, Any]:
        """Fetch commits from all owned public repos and upsert into database.
        
        Uses incremental sync: for each repo, only fetches commits newer
        than the latest already stored.
        
        Returns:
            Dictionary with sync statistics.
        """
        self.db.init_tables()
        
        repos = self.api.get_public_repos()
        
        total_commits = 0
        repos_with_commits = 0
        
        for repo_data in repos:
            repo_name = repo_data["full_name"]
            owner = repo_data["owner"]["login"]
            repo = repo_data["name"]
            
            # Fetch inclusively at the latest timestamp, then de-duplicate by SHA
            # so we do not skip sibling commits that share the same second.
            since = self.db.get_latest_commit_date(repo_name)
            
            commits = self.api.get_commits(owner, repo, since=since)
            
            if not commits:
                continue
            
            count = 0
            commits_to_upsert = []
            for commit_data in commits:
                commit_info = commit_data.get("commit", {})
                author_info = commit_info.get("author", {})
                author_date = author_info.get("date", "")
                
                if not author_date:
                    continue
                
                # Extract YYYY-MM for date_month
                date_month = author_date[:7] if len(author_date) >= 7 else ""
                if not date_month:
                    continue
                
                # First line of commit message
                message = commit_info.get("message", "")
                first_line = message.split("\n")[0][:200] if message else ""
                
                commit = {
                    "sha": commit_data.get("sha", ""),
                    "repo": repo_name,
                    "message": first_line,
                    "author_date": author_date,
                    "date_month": date_month,
                }
                
                if commit["sha"]:
                    commits_to_upsert.append(commit)

            existing_shas = self.db.get_existing_shas(
                commit["sha"] for commit in commits_to_upsert
            )
            commits_to_upsert = [
                commit for commit in commits_to_upsert
                if commit["sha"] not in existing_shas
            ]

            if commits_to_upsert:
                self.db.upsert_commits(commits_to_upsert)
                count = len(commits_to_upsert)
            
            if count > 0:
                repos_with_commits += 1
                total_commits += count
                print(f"  {repo_name}: {count} commits")
        
        print(f"Synced {total_commits} commits from {repos_with_commits} repos")
        return {"commits": total_commits, "repos": repos_with_commits}
    
    def get_status(self) -> Dict[str, Any]:
        """Get sync status.
        
        Returns:
            Dictionary with database stats.
        """
        if not self.db.exists():
            return {"status": "not initialized"}
        return self.db.get_stats()
