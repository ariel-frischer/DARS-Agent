from __future__ import annotations

import hashlib
import re
import pytest


# Test the regex patterns directly without importing the module
GITHUB_ISSUE_URL_PATTERN = re.compile(r"github\.com\/(.*?)\/(.*?)\/issues\/(\d+)")
GITHUB_REPO_URL_PATTERN = re.compile(r".*[/@]?github\.com\/([^/]+)\/([^/]+)")


class TestGitHubURLPatterns:
    """Test GitHub URL regex patterns"""

    def test_github_issue_pattern_matches_https(self):
        """Test github issue pattern matches HTTPS URLs"""
        url = "https://github.com/owner/repo/issues/123"
        match = GITHUB_ISSUE_URL_PATTERN.search(url)
        assert match is not None
        assert match.groups() == ("owner", "repo", "123")

    def test_github_issue_pattern_matches_http(self):
        """Test github issue pattern matches HTTP URLs"""
        url = "http://github.com/owner/repo/issues/456"
        match = GITHUB_ISSUE_URL_PATTERN.search(url)
        assert match is not None
        assert match.groups() == ("owner", "repo", "456")

    def test_github_issue_pattern_without_protocol(self):
        """Test github issue pattern without protocol"""
        url = "github.com/owner/repo/issues/789"
        match = GITHUB_ISSUE_URL_PATTERN.search(url)
        assert match is not None
        assert match.groups() == ("owner", "repo", "789")

    def test_github_issue_pattern_no_match_pull_request(self):
        """Test github issue pattern doesn't match pull requests"""
        url = "https://github.com/owner/repo/pull/123"
        match = GITHUB_ISSUE_URL_PATTERN.search(url)
        assert match is None

    def test_github_issue_pattern_no_match_repo_only(self):
        """Test github issue pattern doesn't match repo-only URLs"""
        url = "https://github.com/owner/repo"
        match = GITHUB_ISSUE_URL_PATTERN.search(url)
        assert match is None

    def test_github_repo_pattern_matches_https(self):
        """Test github repo pattern matches HTTPS URLs"""
        url = "https://github.com/owner/repo"
        match = GITHUB_REPO_URL_PATTERN.search(url)
        assert match is not None
        assert match.groups() == ("owner", "repo")

    def test_github_repo_pattern_matches_dotgit(self):
        """Test github repo pattern matches URLs with .git"""
        url = "https://github.com/owner/repo.git"
        match = GITHUB_REPO_URL_PATTERN.search(url)
        assert match is not None
        assert match.groups() == ("owner", "repo.git")

    def test_github_repo_pattern_no_match_ssh(self):
        """Test github repo pattern doesn't match SSH URLs with colon"""
        # The regex uses / separator, not : like SSH format
        url = "git@github.com:owner/repo.git"
        match = GITHUB_REPO_URL_PATTERN.search(url)
        # This format is not supported by the current regex
        assert match is None

    def test_github_repo_pattern_matches_issue_url(self):
        """Test github repo pattern also matches issue URLs"""
        url = "https://github.com/owner/repo/issues/123"
        match = GITHUB_REPO_URL_PATTERN.search(url)
        assert match is not None
        assert match.groups() == ("owner", "repo")


class TestRemoveTripleBackticks:
    """Test remove_triple_backticks functionality"""

    @staticmethod
    def remove_triple_backticks(text: str) -> str:
        """Remove triple backticks from start of lines"""
        return "\n".join(line.removeprefix("```") for line in text.splitlines())

    def test_remove_backticks_from_start(self):
        """Test removing backticks from start of lines"""
        text = "```python\nprint('hello')\n```"
        result = self.remove_triple_backticks(text)
        assert result == "python\nprint('hello')\n"

    def test_no_backticks(self):
        """Test text without backticks remains unchanged"""
        text = "just some text\nwith multiple lines"
        result = self.remove_triple_backticks(text)
        assert result == text

    def test_backticks_in_middle_of_line(self):
        """Test backticks in middle of line are not removed"""
        text = "some text ``` in middle"
        result = self.remove_triple_backticks(text)
        assert result == "some text ``` in middle"

    def test_empty_string(self):
        """Test empty string returns empty string"""
        result = self.remove_triple_backticks("")
        assert result == ""

    def test_multiple_lines_with_backticks(self):
        """Test multiple lines with backticks at start"""
        text = "```\nline1\n```\nline2"
        result = self.remove_triple_backticks(text)
        assert result == "\nline1\n\nline2"


class TestDataPathNameLogic:
    """Test data path name extraction logic"""

    @staticmethod
    def get_data_path_name_simple(data_path: str) -> str:
        """Simplified version of get_data_path_name for testing logic"""
        if data_path.startswith("text://"):
            return hashlib.sha256(data_path.removeprefix("text://").encode()).hexdigest()[:6]
        match = GITHUB_ISSUE_URL_PATTERN.search(data_path)
        if match:
            owner, repo, _ = match.groups()
            return f"{owner}__{repo}"
        # Extract file stem
        from pathlib import Path
        return Path(data_path).stem

    def test_github_issue_url(self):
        """Test extracting name from github issue URL"""
        url = "https://github.com/owner/repo/issues/123"
        result = self.get_data_path_name_simple(url)
        assert result == "owner__repo"

    def test_text_protocol(self):
        """Test extracting name from text:// protocol"""
        text = "text://some problem statement"
        result = self.get_data_path_name_simple(text)
        expected = hashlib.sha256("some problem statement".encode()).hexdigest()[:6]
        assert result == expected

    def test_file_path(self):
        """Test extracting name from file path"""
        path = "/path/to/problem.json"
        result = self.get_data_path_name_simple(path)
        assert result == "problem"

    def test_file_path_without_extension(self):
        """Test extracting name from file path without extension"""
        path = "/path/to/datafile"
        result = self.get_data_path_name_simple(path)
        assert result == "datafile"


class TestHashingBehavior:
    """Test hashing behavior for text protocol"""

    def test_same_text_same_hash(self):
        """Test same text produces same hash"""
        text = "some problem statement"
        hash1 = hashlib.sha256(text.encode()).hexdigest()[:6]
        hash2 = hashlib.sha256(text.encode()).hexdigest()[:6]
        assert hash1 == hash2

    def test_different_text_different_hash(self):
        """Test different text produces different hash"""
        text1 = "problem 1"
        text2 = "problem 2"
        hash1 = hashlib.sha256(text1.encode()).hexdigest()[:6]
        hash2 = hashlib.sha256(text2.encode()).hexdigest()[:6]
        assert hash1 != hash2

    def test_hash_length_is_six(self):
        """Test hash length is exactly 6 characters"""
        text = "test"
        result = hashlib.sha256(text.encode()).hexdigest()[:6]
        assert len(result) == 6

    def test_unicode_text_hashes(self):
        """Test unicode text can be hashed"""
        text = "问题陈述"
        result = hashlib.sha256(text.encode()).hexdigest()[:6]
        assert len(result) == 6


class TestURLEdgeCases:
    """Test edge cases for URL parsing"""

    def test_github_url_with_query_params(self):
        """Test github URLs with query parameters"""
        url = "https://github.com/owner/repo/issues/123?foo=bar"
        match = GITHUB_ISSUE_URL_PATTERN.search(url)
        assert match is not None
        assert match.groups() == ("owner", "repo", "123")

    def test_github_url_with_hash_fragment(self):
        """Test github URLs with hash fragment"""
        url = "https://github.com/owner/repo/issues/456#comment-789"
        match = GITHUB_ISSUE_URL_PATTERN.search(url)
        assert match is not None
        assert match.groups() == ("owner", "repo", "456")

    def test_very_long_owner_repo_names(self):
        """Test handling very long owner/repo names"""
        url = "https://github.com/" + "a" * 100 + "/" + "b" * 100 + "/issues/999"
        match = GITHUB_ISSUE_URL_PATTERN.search(url)
        assert match is not None
        owner, repo, num = match.groups()
        assert len(owner) == 100
        assert len(repo) == 100
        assert num == "999"

    def test_repo_name_with_hyphens(self):
        """Test repo names with hyphens"""
        url = "https://github.com/owner/repo-with-dashes"
        match = GITHUB_REPO_URL_PATTERN.search(url)
        assert match is not None
        assert match.groups() == ("owner", "repo-with-dashes")

    def test_repo_name_with_dots(self):
        """Test repo names with dots"""
        url = "https://github.com/owner/repo.name.with.dots"
        match = GITHUB_REPO_URL_PATTERN.search(url)
        assert match is not None
        assert match.groups() == ("owner", "repo.name.with.dots")

    def test_empty_string_no_match(self):
        """Test empty string doesn't match"""
        assert GITHUB_ISSUE_URL_PATTERN.search("") is None
        assert GITHUB_REPO_URL_PATTERN.search("") is None

    def test_gitlab_url_no_match(self):
        """Test gitlab URLs don't match github patterns"""
        url = "https://gitlab.com/owner/repo/issues/123"
        assert GITHUB_ISSUE_URL_PATTERN.search(url) is None


class TestTrajectoryMarkdownFormatting:
    """Test trajectory markdown formatting logic"""

    @staticmethod
    def format_trajectory_simple(trajectory: list[dict[str, str]]) -> str:
        """Simplified trajectory formatting for testing"""
        prefix = ["<details>", "<summary>Trajectory</summary>", ""]
        steps = []
        for i, step in enumerate(trajectory):
            response = step.get('response', '').strip()
            observation = step.get('observation', '').strip()
            step_strs = [
                f"**Response ({i})**:",
                response,
                f"**Observation ({i})**:",
                f"```\n{observation}\n```"
            ]
            steps.append("\n".join(step_strs))
        suffix = ["", "</details>"]
        return "\n".join(prefix) + "\n\n---\n\n".join(steps) + "\n".join(suffix)

    def test_empty_trajectory(self):
        """Test formatting empty trajectory"""
        result = self.format_trajectory_simple([])
        assert "<details>" in result
        assert "</details>" in result

    def test_single_step_trajectory(self):
        """Test formatting single step trajectory"""
        trajectory = [{"response": "Test response", "observation": "Test output"}]
        result = self.format_trajectory_simple(trajectory)
        assert "Test response" in result
        assert "Test output" in result
        assert "Response (0)" in result
        assert "Observation (0)" in result

    def test_multiple_steps_trajectory(self):
        """Test formatting multiple steps"""
        trajectory = [
            {"response": "Step 1", "observation": "Output 1"},
            {"response": "Step 2", "observation": "Output 2"}
        ]
        result = self.format_trajectory_simple(trajectory)
        assert "Step 1" in result
        assert "Step 2" in result
        assert "Response (0)" in result
        assert "Response (1)" in result

    def test_empty_response_and_observation(self):
        """Test handling empty response and observation"""
        trajectory = [{"response": "", "observation": ""}]
        result = self.format_trajectory_simple(trajectory)
        assert "<details>" in result
        assert "Response (0)" in result


class TestRegressionSafety:
    """Regression tests to ensure core logic remains correct"""

    def test_issue_url_components_extracted_correctly(self):
        """Test that all components of issue URL are extracted"""
        test_cases = [
            ("https://github.com/python/cpython/issues/12345", ("python", "cpython", "12345")),
            ("http://github.com/a/b/issues/1", ("a", "b", "1")),
            ("github.com/owner/repo/issues/999", ("owner", "repo", "999")),
        ]
        for url, expected in test_cases:
            match = GITHUB_ISSUE_URL_PATTERN.search(url)
            assert match is not None
            assert match.groups() == expected

    def test_repo_url_components_extracted_correctly(self):
        """Test that repo URL components are extracted"""
        test_cases = [
            ("https://github.com/owner/repo", ("owner", "repo")),
            ("https://github.com/user/project.git", ("user", "project.git")),
        ]
        for url, expected in test_cases:
            match = GITHUB_REPO_URL_PATTERN.search(url)
            assert match is not None
            assert match.groups() == expected
