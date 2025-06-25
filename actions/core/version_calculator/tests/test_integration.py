import pytest
import os
import subprocess
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to import main
sys.path.insert(0, str(Path(__file__).parent.parent))
import main


class TestVersionCalculatorIntegration:
    """Integration tests for version calculator with real git operations"""

    def test_version_calculation_no_tags(self, temp_git_repo, clean_env, mock_env):
        """Test version calculation when no tags exist"""
        mock_env(DEFAULT_VERSION='v0.1.0')
        
        # Create output file
        output_file = temp_git_repo / 'operation_outputs.env'
        
        main.main()
        
        # Check outputs
        assert output_file.exists()
        content = output_file.read_text()
        assert 'CURRENT_VERSION=v0.1.0' in content
        assert 'NEXT_VERSION=v0.1.0' in content
        assert 'COMMIT_COUNT=0' in content

    def test_version_calculation_with_tag_no_commits(self, temp_git_repo, clean_env, mock_env):
        """Test version calculation with existing tag and no new commits"""
        # Create a tag
        subprocess.run(['git', 'tag', 'v1.0.0'], cwd=temp_git_repo, check=True)
        
        mock_env(VERSION_PREFIX='v', TAG_PATTERN='v*')
        
        main.main()
        
        # Check outputs
        output_file = temp_git_repo / 'operation_outputs.env'
        content = output_file.read_text()
        assert 'CURRENT_VERSION=v1.0.0' in content
        assert 'NEXT_VERSION=v1.0.0' in content
        assert 'COMMIT_COUNT=0' in content

    def test_version_calculation_with_tag_and_commits(self, temp_git_repo, clean_env, mock_env):
        """Test version calculation with existing tag and new commits"""
        # Create a tag
        subprocess.run(['git', 'tag', 'v1.0.0'], cwd=temp_git_repo, check=True)
        
        # Add more commits
        for i in range(3):
            test_file = temp_git_repo / f'test{i}.txt'
            test_file.write_text(f'commit {i}')
            subprocess.run(['git', 'add', f'test{i}.txt'], cwd=temp_git_repo, check=True)
            subprocess.run(['git', 'commit', '-m', f'Commit {i}'], cwd=temp_git_repo, check=True)
        
        mock_env(VERSION_PREFIX='v', TAG_PATTERN='v*')
        
        main.main()
        
        # Check outputs
        output_file = temp_git_repo / 'operation_outputs.env'
        content = output_file.read_text()
        assert 'CURRENT_VERSION=v1.0.0' in content
        assert 'NEXT_VERSION=v1.0.3' in content  # patch incremented by commit count
        assert 'COMMIT_COUNT=3' in content

    def test_version_calculation_multiple_tags(self, temp_git_repo, clean_env, mock_env):
        """Test version calculation with multiple tags"""
        # Create multiple tags (git sorts them)
        subprocess.run(['git', 'tag', 'v1.0.0'], cwd=temp_git_repo, check=True)
        
        # Add commit and new tag
        test_file = temp_git_repo / 'test2.txt'
        test_file.write_text('another commit')
        subprocess.run(['git', 'add', 'test2.txt'], cwd=temp_git_repo, check=True)
        subprocess.run(['git', 'commit', '-m', 'Another commit'], cwd=temp_git_repo, check=True)
        subprocess.run(['git', 'tag', 'v1.1.0'], cwd=temp_git_repo, check=True)
        
        # Add more commits after latest tag
        for i in range(2):
            test_file = temp_git_repo / f'test_after_{i}.txt'
            test_file.write_text(f'commit after tag {i}')
            subprocess.run(['git', 'add', f'test_after_{i}.txt'], cwd=temp_git_repo, check=True)
            subprocess.run(['git', 'commit', '-m', f'After tag {i}'], cwd=temp_git_repo, check=True)
        
        mock_env(VERSION_PREFIX='v', TAG_PATTERN='v*')
        
        main.main()
        
        # Check outputs - should use latest tag (v1.1.0)
        output_file = temp_git_repo / 'operation_outputs.env'
        content = output_file.read_text()
        assert 'CURRENT_VERSION=v1.1.0' in content
        assert 'NEXT_VERSION=v1.1.2' in content  # 2 commits since v1.1.0
        assert 'COMMIT_COUNT=2' in content

    def test_custom_tag_pattern(self, temp_git_repo, clean_env, mock_env):
        """Test version calculation with custom tag pattern"""
        # Create tags with different patterns
        subprocess.run(['git', 'tag', 'v1.0.0'], cwd=temp_git_repo, check=True)
        subprocess.run(['git', 'tag', 'release-2.0.0'], cwd=temp_git_repo, check=True)
        
        mock_env(VERSION_PREFIX='release-', TAG_PATTERN='release-*')
        
        main.main()
        
        # Should only consider release-* tags
        output_file = temp_git_repo / 'operation_outputs.env'
        content = output_file.read_text()
        assert 'CURRENT_VERSION=release-2.0.0' in content

    def test_github_actions_compatibility(self, temp_git_repo, clean_env, mock_env):
        """Test GitHub Actions environment variable compatibility"""
        github_output = temp_git_repo / 'github_output'
        
        mock_env(
            GITHUB_OUTPUT=str(github_output),
            INPUT_DEFAULT_VERSION='v0.5.0',
            INPUT_VERSION_PREFIX='v',
            INPUT_TAG_PATTERN='v*'
        )
        
        main.main()
        
        # Check GitHub output format
        assert github_output.exists()
        github_content = github_output.read_text()
        assert 'current_version=v0.5.0' in github_content
        assert 'next_version=v0.5.0' in github_content
        assert 'commit_count=0' in github_content
        
        # Check GitLab output still created
        gitlab_output = temp_git_repo / 'operation_outputs.env'
        assert gitlab_output.exists()
        gitlab_content = gitlab_output.read_text()
        assert 'CURRENT_VERSION=v0.5.0' in gitlab_content