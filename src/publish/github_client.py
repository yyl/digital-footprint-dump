"""GitHub client for committing files to a repository."""

import logging
from typing import Dict, Any
from github import Github, GithubException

logger = logging.getLogger(__name__)


class GitHubClientError(Exception):
    """Custom exception for GitHub client errors."""
    pass


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, token: str, repo_owner: str, repo_name: str, target_branch: str = 'main'):
        """Initialize GitHub client.
        
        Args:
            token: GitHub personal access token.
            repo_owner: Repository owner username.
            repo_name: Repository name.
            target_branch: Branch to commit to.
        """
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.target_branch = target_branch
        
        self.github = Github(token)
        
        try:
            self.repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            logger.info(f"Connected to repository: {repo_owner}/{repo_name}")
        except GithubException as e:
            raise GitHubClientError(f"Failed to access repository {repo_owner}/{repo_name}: {str(e)}")
    
    def create_or_update_file(self, file_path: str, content: str, commit_message: str) -> Dict[str, Any]:
        """Create a new file or update an existing file in the repository.
        
        Args:
            file_path: Path to the file in the repository.
            content: File content as string.
            commit_message: Commit message.
            
        Returns:
            Dictionary with commit information.
        """
        try:
            # Check if file already exists
            file_exists = False
            existing_file = None
            
            try:
                existing_file = self.repo.get_contents(file_path, ref=self.target_branch)
                file_exists = True
                logger.info(f"File {file_path} exists, will update")
            except GithubException as e:
                if e.status == 404:
                    logger.info(f"File {file_path} does not exist, will create")
                else:
                    raise GitHubClientError(f"Error checking file existence: {str(e)}")
            
            # Create or update the file
            if file_exists:
                result = self.repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=existing_file.sha,
                    branch=self.target_branch
                )
                logger.info(f"Updated file: {file_path}")
            else:
                result = self.repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    branch=self.target_branch
                )
                logger.info(f"Created file: {file_path}")
            
            return {
                'sha': result['commit'].sha,
                'url': result['commit'].html_url,
                'message': commit_message,
                'file_path': file_path
            }
            
        except GithubException as e:
            error_msg = f"GitHub API error for {file_path}: {str(e)}"
            logger.error(error_msg)
            raise GitHubClientError(error_msg)
