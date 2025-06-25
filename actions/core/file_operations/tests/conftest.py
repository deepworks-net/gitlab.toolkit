"""
Test configuration and fixtures for file operations
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing"""
    files = {}
    
    # Create test files
    files['text_file'] = temp_dir / "test.txt"
    files['text_file'].write_text("Hello, World!")
    
    files['json_file'] = temp_dir / "test.json"
    files['json_file'].write_text('{"key": "value"}')
    
    files['empty_file'] = temp_dir / "empty.txt"
    files['empty_file'].touch()
    
    # Create subdirectory with file
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    files['subdir_file'] = subdir / "nested.txt"
    files['subdir_file'].write_text("Nested content")
    
    return files


@pytest.fixture
def mock_gitlab_env(monkeypatch):
    """Mock GitLab CI environment variables"""
    env_vars = {
        'CI': 'true',
        'GITLAB_CI': 'true',
        'CI_PROJECT_NAME': 'test-project',
        'CI_COMMIT_SHA': 'abc123',
        'FCM_MODEL': 'system.file-operations',
        'FCM_VERSION': '1.0.0'
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars