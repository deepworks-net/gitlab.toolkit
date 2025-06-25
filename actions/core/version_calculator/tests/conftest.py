import pytest
import os
import tempfile
import subprocess
from pathlib import Path


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_path, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, check=True)
        
        # Create initial commit
        test_file = repo_path / 'test.txt'
        test_file.write_text('initial commit')
        subprocess.run(['git', 'add', 'test.txt'], cwd=repo_path, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, check=True)
        
        # Change to repo directory for tests
        original_cwd = os.getcwd()
        os.chdir(repo_path)
        
        yield repo_path
        
        # Restore original directory
        os.chdir(original_cwd)


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables"""
    def _mock_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)
    return _mock_env


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment of GitHub/GitLab specific variables"""
    env_vars = ['GITHUB_OUTPUT', 'CI_PROJECT_DIR', 'INPUT_DEFAULT_VERSION', 
                'INPUT_VERSION_PREFIX', 'INPUT_TAG_PATTERN', 'DEFAULT_VERSION',
                'VERSION_PREFIX', 'TAG_PATTERN']
    
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)