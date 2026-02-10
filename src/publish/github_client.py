"""GitHub client for committing files to a repository."""

import logging
from typing import Dict, Any, List
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
    
    
    def create_or_update_files(
        self,
        files: Dict[str, str],
        commit_message: str
    ) -> Dict[str, Any]:
        """Create or update multiple files in a single commit.
        
        Uses the Git Data API to build a tree with all file changes
        and commit them atomically. Preserves all existing files via base_tree.
        
        Args:
            files: Dictionary mapping repo file paths to content strings.
            commit_message: Commit message for the single commit.
            
        Returns:
            Dictionary with commit information.
        """
        try:
            # Get current HEAD commit and its tree
            ref = self.repo.get_git_ref(f"heads/{self.target_branch}")
            head_sha = ref.object.sha
            base_tree = self.repo.get_git_tree(head_sha)
            
            # Build tree elements for each file
            from github import InputGitTreeElement
            tree_elements = []
            for file_path, content in files.items():
                element = InputGitTreeElement(
                    path=file_path,
                    mode="100644",
                    type="blob",
                    content=content,
                )
                tree_elements.append(element)
                logger.info(f"Adding file to commit: {file_path}")
            
            # Create new tree on top of existing base tree
            new_tree = self.repo.create_git_tree(tree_elements, base_tree)
            
            # Create commit
            head_commit = self.repo.get_git_commit(head_sha)
            new_commit = self.repo.create_git_commit(
                message=commit_message,
                tree=new_tree,
                parents=[head_commit],
            )
            
            # Update branch ref to point to new commit
            ref.edit(sha=new_commit.sha)
            
            logger.info(f"Committed {len(files)} files: {new_commit.sha}")
            
            return {
                'sha': new_commit.sha,
                'url': new_commit.html_url,
                'message': commit_message,
                'file_paths': list(files.keys()),
            }
            
        except GithubException as e:
            error_msg = f"GitHub API error during multi-file commit: {str(e)}"
            logger.error(error_msg)
            raise GitHubClientError(error_msg)

