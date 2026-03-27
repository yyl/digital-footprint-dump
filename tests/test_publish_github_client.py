import unittest
from unittest.mock import MagicMock, patch

from src.publish.github_client import GitHubClient, GitHubClientError


class FakeGithubException(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class TestPublishGitHubClient(unittest.TestCase):
    @patch("src.publish.github_client.Github")
    @patch("src.publish.github_client.Auth")
    def test_init_uses_auth_token(self, mock_auth, mock_github):
        mock_auth.Token.return_value = "auth-token"
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient("token", "owner", "repo")

        mock_auth.Token.assert_called_once_with("token")
        mock_github.assert_called_once_with(auth="auth-token")
        self.assertEqual(client.repo, mock_repo)

    @patch("src.publish.github_client.time.sleep")
    @patch("src.publish.github_client.Github")
    @patch("src.publish.github_client.Auth")
    def test_retries_non_fast_forward(self, mock_auth, mock_github, mock_sleep):
        mock_auth.Token.return_value = "auth-token"
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient("token", "owner", "repo")
        expected = {
            "sha": "abc123",
            "url": "https://example.com/commit/abc123",
            "message": "msg",
            "file_paths": ["file.md"],
        }

        non_fast_forward = FakeGithubException(422, "Update is not a fast forward")

        attempts = {"count": 0}

        def side_effect(*args, **kwargs):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise non_fast_forward
            return expected

        with patch("src.publish.github_client.GithubException", FakeGithubException):
            with patch.object(
                client,
                "_create_or_update_files_once",
                side_effect=side_effect,
            ) as mock_once:
                result = client.create_or_update_files({"file.md": "content"}, "msg")

        self.assertEqual(result, expected)
        self.assertEqual(mock_once.call_count, 2)
        mock_sleep.assert_called_once_with(0.5)

    @patch("src.publish.github_client.time.sleep")
    @patch("src.publish.github_client.Github")
    @patch("src.publish.github_client.Auth")
    def test_raises_after_retry_budget_exhausted(self, mock_auth, mock_github, mock_sleep):
        mock_auth.Token.return_value = "auth-token"
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient("token", "owner", "repo")
        non_fast_forward = FakeGithubException(422, "Update is not a fast forward")

        def side_effect(*args, **kwargs):
            raise non_fast_forward

        with patch("src.publish.github_client.GithubException", FakeGithubException):
            with patch.object(
                client,
                "_create_or_update_files_once",
                side_effect=side_effect,
            ):
                with self.assertRaises(GitHubClientError):
                    client.create_or_update_files({"file.md": "content"}, "msg")

        self.assertEqual(mock_sleep.call_count, client.MAX_NON_FAST_FORWARD_RETRIES)

    @patch("src.publish.github_client.Github")
    @patch("src.publish.github_client.Auth")
    def test_non_retryable_github_error_raises_immediately(self, mock_auth, mock_github):
        mock_auth.Token.return_value = "auth-token"
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient("token", "owner", "repo")
        error = FakeGithubException(500, "Internal Server Error")

        with patch("src.publish.github_client.GithubException", FakeGithubException):
            with patch.object(client, "_create_or_update_files_once", side_effect=error) as mock_once:
                with self.assertRaises(GitHubClientError):
                    client.create_or_update_files({"file.md": "content"}, "msg")

        self.assertEqual(mock_once.call_count, 1)
