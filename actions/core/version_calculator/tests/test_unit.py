import pytest
import os
import subprocess
import tempfile
from unittest.mock import patch, mock_open
import sys
from pathlib import Path

# Add parent directory to path to import main
sys.path.insert(0, str(Path(__file__).parent.parent))
import main


class TestVersionCalculator:
    """Unit tests for version calculator functions"""

    def test_validate_version_format_valid(self):
        """Test validation of valid version formats"""
        assert main.validate_version_format('v1.0.0', 'v') is True
        assert main.validate_version_format('v10.25.100', 'v') is True
        assert main.validate_version_format('1.0.0', '') is True

    def test_validate_version_format_invalid(self):
        """Test validation rejects invalid version formats"""
        with pytest.raises(SystemExit):
            main.validate_version_format('1.0', 'v')
        
        with pytest.raises(SystemExit):
            main.validate_version_format('v1.0.0.0', 'v')
        
        with pytest.raises(SystemExit):
            main.validate_version_format('invalid', 'v')

    @patch('subprocess.check_output')
    def test_get_latest_tag_with_tags(self, mock_subprocess):
        """Test getting latest tag when tags exist"""
        mock_subprocess.return_value = 'v1.2.0\nv1.1.0\nv1.0.0'
        
        result = main.get_latest_tag('v*')
        assert result == 'v1.2.0'
        mock_subprocess.assert_called_once_with(
            ['git', 'tag', '-l', 'v*', '--sort=-v:refname'], text=True
        )

    @patch('subprocess.check_output')
    def test_get_latest_tag_no_tags(self, mock_subprocess):
        """Test getting latest tag when no tags exist"""
        mock_subprocess.return_value = ''
        
        result = main.get_latest_tag('v*')
        assert result is None

    @patch('subprocess.check_output')
    def test_get_commit_count_since_tag(self, mock_subprocess):
        """Test getting commit count since tag"""
        mock_subprocess.return_value = '5'
        
        result = main.get_commit_count_since_tag('v1.0.0')
        assert result == 5
        mock_subprocess.assert_called_once_with(
            ['git', 'rev-list', 'v1.0.0..HEAD', '--count'], text=True
        )

    @patch('subprocess.check_output')
    def test_setup_git(self, mock_subprocess):
        """Test git setup configuration"""
        mock_subprocess.return_value = ''
        
        # Test with CI_PROJECT_DIR
        with patch.dict(os.environ, {'CI_PROJECT_DIR': '/test/project'}):
            main.setup_git()
            mock_subprocess.assert_called_with(
                ['git', 'config', '--global', '--add', 'safe.directory', '/test/project'],
                text=True
            )

    @patch('builtins.open', new_callable=mock_open)
    def test_write_outputs_github(self, mock_file):
        """Test writing outputs for GitHub Actions"""
        with patch.dict(os.environ, {'GITHUB_OUTPUT': '/tmp/github_output'}):
            main.write_outputs('v1.0.0', 'v1.0.1', 5)
        
        # Check GitHub output was written
        mock_file.assert_any_call('/tmp/github_output', 'a')

    @patch('builtins.open', new_callable=mock_open)
    def test_write_outputs_gitlab(self, mock_file):
        """Test writing outputs for GitLab CI"""
        main.write_outputs('v1.0.0', 'v1.0.1', 5)
        
        # Check GitLab output was written
        mock_file.assert_any_call('operation_outputs.env', 'w')

    def test_main_environment_variable_priority(self, mock_env, clean_env):
        """Test that INPUT_ variables take priority over regular variables"""
        mock_env(
            INPUT_DEFAULT_VERSION='v2.0.0',
            DEFAULT_VERSION='v1.0.0',
            INPUT_VERSION_PREFIX='rel-',
            VERSION_PREFIX='v'
        )
        
        with patch.object(main, 'validate_version_format') as mock_validate, \
             patch.object(main, 'setup_git'), \
             patch.object(main, 'get_latest_tag') as mock_get_tag, \
             patch.object(main, 'write_outputs') as mock_write:
            
            mock_get_tag.return_value = None
            
            main.main()
            
            # Should use INPUT_ variables
            mock_validate.assert_called_with('v2.0.0', 'rel-')
            mock_get_tag.assert_called_with('v*')  # Default tag pattern