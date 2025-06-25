"""
Unit tests for file operations
"""

import pytest
import os
import base64
from pathlib import Path
from scripts.system_operations import FileOperations, GitLabFileOperationsRunner


@pytest.mark.unit
class TestFileOperations:
    """Unit tests for the FileOperations class"""
    
    def test_create_file_success(self, temp_dir):
        """Test successful file creation"""
        file_ops = FileOperations()
        file_path = temp_dir / "new_file.txt"
        content = "Test content"
        
        success, message = file_ops.create_file(str(file_path), content)
        
        assert success is True
        assert "created successfully" in message
        assert file_path.exists()
        assert file_path.read_text() == content
        assert file_ops.outputs['file_created'] == str(file_path.absolute())
    
    def test_create_file_with_dirs(self, temp_dir):
        """Test file creation with directory creation"""
        file_ops = FileOperations()
        file_path = temp_dir / "new" / "nested" / "file.txt"
        content = "Nested content"
        
        success, message = file_ops.create_file(str(file_path), content, create_dirs=True)
        
        assert success is True
        assert file_path.exists()
        assert file_path.read_text() == content
    
    def test_create_file_without_overwrite(self, sample_files):
        """Test file creation fails when file exists and overwrite is False"""
        file_ops = FileOperations()
        existing_file = sample_files['text_file']
        
        success, message = file_ops.create_file(str(existing_file), "new content", overwrite=False)
        
        assert success is False
        assert "already exists" in message
    
    def test_create_file_with_overwrite(self, sample_files):
        """Test file creation succeeds when overwrite is True"""
        file_ops = FileOperations()
        existing_file = sample_files['text_file']
        new_content = "Overwritten content"
        
        success, message = file_ops.create_file(str(existing_file), new_content, overwrite=True)
        
        assert success is True
        assert existing_file.read_text() == new_content
    
    def test_read_file_success(self, sample_files):
        """Test successful file reading"""
        file_ops = FileOperations()
        file_path = sample_files['text_file']
        
        success, content, message = file_ops.read_file(str(file_path))
        
        assert success is True
        assert content == "Hello, World!"
        assert "read successfully" in message
        assert file_ops.outputs['file_content'] == content
    
    def test_read_nonexistent_file(self, temp_dir):
        """Test reading non-existent file"""
        file_ops = FileOperations()
        file_path = temp_dir / "nonexistent.txt"
        
        success, content, message = file_ops.read_file(str(file_path))
        
        assert success is False
        assert content == ""
        assert "not found" in message
        assert file_ops.outputs['file_exists'] == 'false'
    
    def test_update_file_success(self, sample_files):
        """Test successful file update"""
        file_ops = FileOperations()
        file_path = sample_files['text_file']
        new_content = "Updated content"
        
        success, message = file_ops.update_file(str(file_path), new_content)
        
        assert success is True
        assert file_path.read_text() == new_content
        assert "updated successfully" in message
    
    def test_delete_file_success(self, sample_files):
        """Test successful file deletion"""
        file_ops = FileOperations()
        file_path = sample_files['text_file']
        
        success, message = file_ops.delete_file(str(file_path))
        
        assert success is True
        assert not file_path.exists()
        assert "deleted successfully" in message
        assert file_ops.outputs['file_deleted'] == str(file_path.absolute())
    
    def test_copy_file_success(self, sample_files, temp_dir):
        """Test successful file copy"""
        file_ops = FileOperations()
        source = sample_files['text_file']
        destination = temp_dir / "copied.txt"
        
        success, message = file_ops.copy_file(str(source), str(destination))
        
        assert success is True
        assert destination.exists()
        assert destination.read_text() == source.read_text()
        assert "copied successfully" in message
    
    def test_move_file_success(self, sample_files, temp_dir):
        """Test successful file move"""
        file_ops = FileOperations()
        source = sample_files['text_file']
        destination = temp_dir / "moved.txt"
        original_content = source.read_text()
        
        success, message = file_ops.move_file(str(source), str(destination))
        
        assert success is True
        assert destination.exists()
        assert not source.exists()
        assert destination.read_text() == original_content
        assert "moved successfully" in message
    
    def test_search_files_success(self, sample_files):
        """Test successful file search"""
        file_ops = FileOperations()
        base_path = str(sample_files['text_file'].parent)
        
        success, files, message = file_ops.search_files("*.txt", base_path)
        
        assert success is True
        assert len(files) >= 2  # At least test.txt and empty.txt
        assert any("test.txt" in f for f in files)
        assert "Found" in message
    
    def test_base64_operations(self, temp_dir):
        """Test base64 encoding/decoding operations"""
        file_ops = FileOperations()
        file_path = temp_dir / "base64_test.txt"
        original_content = "Hello, Base64!"
        encoded_content = base64.b64encode(original_content.encode()).decode('ascii')
        
        # Create file with base64 content
        success, message = file_ops.create_file(str(file_path), encoded_content, encoding="base64")
        assert success is True
        assert file_path.read_text() == original_content
        
        # Read file as base64
        success, content, message = file_ops.read_file(str(file_path), encoding="base64")
        assert success is True
        assert content == encoded_content


@pytest.mark.unit
class TestGitLabFileOperationsRunner:
    """Unit tests for the GitLab runner"""
    
    def test_create_operation(self, mock_gitlab_env, temp_dir, monkeypatch):
        """Test create operation through runner"""
        file_path = temp_dir / "runner_test.txt"
        
        # Set environment variables
        monkeypatch.setenv('OPERATION', 'create')
        monkeypatch.setenv('FILE_PATH', str(file_path))
        monkeypatch.setenv('CONTENT', 'Runner test content')
        
        runner = GitLabFileOperationsRunner()
        
        # Mock the _write_outputs method to avoid file creation
        def mock_write_outputs():
            pass
        runner._write_outputs = mock_write_outputs
        
        # This should not raise an exception
        runner.run()
        
        assert file_path.exists()
        assert file_path.read_text() == 'Runner test content'
    
    def test_invalid_operation(self, mock_gitlab_env, monkeypatch):
        """Test invalid operation handling"""
        monkeypatch.setenv('OPERATION', 'invalid_operation')
        
        runner = GitLabFileOperationsRunner()
        
        with pytest.raises(SystemExit) as exc_info:
            runner.run()
        
        assert exc_info.value.code == 1