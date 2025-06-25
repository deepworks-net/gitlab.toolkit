#!/usr/bin/env python3
"""
GitLab File Operations Implementation
Adapted from github.toolkit complete-action-example for GitLab CI/CD
"""

import os
import sys
import glob
import shutil
import base64
from pathlib import Path
from typing import Optional, List, Union, Tuple


class FileOperations:
    """Handles atomic file system operations following LCMCP principles."""
    
    def __init__(self):
        self.outputs = {}
    
    def create_file(self, file_path: str, content: str = "", 
                   encoding: str = "utf-8", create_dirs: bool = True,
                   overwrite: bool = False) -> Tuple[bool, str]:
        """Create a new file with specified content."""
        try:
            path = Path(file_path)
            
            # Check if file exists and overwrite is False
            if path.exists() and not overwrite:
                return False, f"File already exists: {file_path}"
            
            # Create parent directories if requested
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle different encodings
            if encoding == "base64":
                # Decode base64 content
                decoded_content = base64.b64decode(content)
                with open(path, 'wb') as f:
                    f.write(decoded_content)
            else:
                # Write as text
                with open(path, 'w', encoding=encoding) as f:
                    f.write(content)
            
            # Set outputs
            self.outputs['file_created'] = str(path.absolute())
            self.outputs['file_size'] = str(path.stat().st_size)
            self.outputs['file_exists'] = 'true'
            
            return True, f"File created successfully: {file_path}"
            
        except Exception as e:
            return False, f"Failed to create file: {str(e)}"
    
    def read_file(self, file_path: str, encoding: str = "utf-8") -> Tuple[bool, str, str]:
        """Read content from a file."""
        try:
            path = Path(file_path)
            
            if not path.exists():
                self.outputs['file_exists'] = 'false'
                return False, "", f"File not found: {file_path}"
            
            if encoding == "base64":
                # Read as binary and encode to base64
                with open(path, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('ascii')
            else:
                # Read as text
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
            
            # Set outputs
            self.outputs['file_content'] = content
            self.outputs['file_size'] = str(path.stat().st_size)
            self.outputs['file_exists'] = 'true'
            
            return True, content, f"File read successfully: {file_path}"
            
        except Exception as e:
            return False, "", f"Failed to read file: {str(e)}"
    
    def update_file(self, file_path: str, content: str, 
                   encoding: str = "utf-8") -> Tuple[bool, str]:
        """Update an existing file with new content."""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False, f"File not found: {file_path}"
            
            # Handle different encodings
            if encoding == "base64":
                decoded_content = base64.b64decode(content)
                with open(path, 'wb') as f:
                    f.write(decoded_content)
            else:
                with open(path, 'w', encoding=encoding) as f:
                    f.write(content)
            
            # Set outputs
            self.outputs['file_size'] = str(path.stat().st_size)
            self.outputs['file_exists'] = 'true'
            
            return True, f"File updated successfully: {file_path}"
            
        except Exception as e:
            return False, f"Failed to update file: {str(e)}"
    
    def delete_file(self, file_path: str) -> Tuple[bool, str]:
        """Delete a file."""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False, f"File not found: {file_path}"
            
            path.unlink()
            
            # Set outputs
            self.outputs['file_deleted'] = str(path.absolute())
            self.outputs['file_exists'] = 'false'
            
            return True, f"File deleted successfully: {file_path}"
            
        except Exception as e:
            return False, f"Failed to delete file: {str(e)}"
    
    def copy_file(self, file_path: str, destination: str,
                 create_dirs: bool = True, overwrite: bool = False) -> Tuple[bool, str]:
        """Copy a file to a new location."""
        try:
            src_path = Path(file_path)
            dest_path = Path(destination)
            
            if not src_path.exists():
                return False, f"Source file not found: {file_path}"
            
            if dest_path.exists() and not overwrite:
                return False, f"Destination already exists: {destination}"
            
            # Create parent directories if requested
            if create_dirs:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_path, dest_path)
            
            # Set outputs
            self.outputs['file_size'] = str(dest_path.stat().st_size)
            self.outputs['file_exists'] = 'true'
            
            return True, f"File copied successfully: {file_path} -> {destination}"
            
        except Exception as e:
            return False, f"Failed to copy file: {str(e)}"
    
    def move_file(self, file_path: str, destination: str,
                 create_dirs: bool = True, overwrite: bool = False) -> Tuple[bool, str]:
        """Move a file to a new location."""
        try:
            src_path = Path(file_path)
            dest_path = Path(destination)
            
            if not src_path.exists():
                return False, f"Source file not found: {file_path}"
            
            if dest_path.exists() and not overwrite:
                return False, f"Destination already exists: {destination}"
            
            # Create parent directories if requested
            if create_dirs:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dest_path))
            
            # Set outputs
            self.outputs['file_size'] = str(dest_path.stat().st_size)
            self.outputs['file_exists'] = 'true'
            
            return True, f"File moved successfully: {file_path} -> {destination}"
            
        except Exception as e:
            return False, f"Failed to move file: {str(e)}"
    
    def search_files(self, pattern: str, base_path: str = ".") -> Tuple[bool, List[str], str]:
        """Search for files matching a pattern."""
        try:
            # Use glob to find matching files
            search_pattern = os.path.join(base_path, pattern)
            found_files = glob.glob(search_pattern, recursive=True)
            
            # Convert to relative paths
            found_files = [os.path.relpath(f) for f in found_files]
            
            # Set outputs
            self.outputs['files_found'] = ','.join(found_files)
            
            return True, found_files, f"Found {len(found_files)} files matching pattern: {pattern}"
            
        except Exception as e:
            return False, [], f"Failed to search files: {str(e)}"


class GitLabFileOperationsRunner:
    """GitLab CI/CD runner for file operations"""
    
    def __init__(self):
        self.operation = os.environ.get('OPERATION', '').lower()
        self.file_path = os.environ.get('FILE_PATH', '')
        self.content = os.environ.get('CONTENT', '')
        self.destination = os.environ.get('DESTINATION', '')
        self.pattern = os.environ.get('PATTERN', '')
        self.encoding = os.environ.get('ENCODING', 'utf-8')
        self.create_dirs = os.environ.get('CREATE_DIRS', 'true').lower() == 'true'
        self.overwrite = os.environ.get('OVERWRITE', 'false').lower() == 'true'
        
        self.file_ops = FileOperations()
    
    def run(self):
        """Execute the requested file operation"""
        operations = {
            'create': self._create,
            'read': self._read,
            'update': self._update,
            'delete': self._delete,
            'copy': self._copy,
            'move': self._move,
            'search': self._search
        }
        
        if self.operation not in operations:
            print(f"ERROR: Unknown operation '{self.operation}'")
            sys.exit(1)
        
        try:
            success, message = operations[self.operation]()
            
            if success:
                self.file_ops.outputs['operation_status'] = 'success'
                self._write_outputs()
                print(f"✓ {message}")
            else:
                self.file_ops.outputs['operation_status'] = 'failure'
                self._write_outputs()
                print(f"ERROR: {message}")
                sys.exit(1)
                
        except Exception as e:
            print(f"ERROR: Operation failed - {e}")
            sys.exit(1)
    
    def _create(self):
        if not self.file_path:
            return False, "FILE_PATH is required for create operation"
        return self.file_ops.create_file(
            self.file_path, self.content, self.encoding, 
            self.create_dirs, self.overwrite
        )
    
    def _read(self):
        if not self.file_path:
            return False, "FILE_PATH is required for read operation"
        success, content, message = self.file_ops.read_file(self.file_path, self.encoding)
        return success, message
    
    def _update(self):
        if not self.file_path:
            return False, "FILE_PATH is required for update operation"
        return self.file_ops.update_file(self.file_path, self.content, self.encoding)
    
    def _delete(self):
        if not self.file_path:
            return False, "FILE_PATH is required for delete operation"
        return self.file_ops.delete_file(self.file_path)
    
    def _copy(self):
        if not self.file_path or not self.destination:
            return False, "FILE_PATH and DESTINATION are required for copy operation"
        return self.file_ops.copy_file(
            self.file_path, self.destination, self.create_dirs, self.overwrite
        )
    
    def _move(self):
        if not self.file_path or not self.destination:
            return False, "FILE_PATH and DESTINATION are required for move operation"
        return self.file_ops.move_file(
            self.file_path, self.destination, self.create_dirs, self.overwrite
        )
    
    def _search(self):
        if not self.pattern:
            return False, "PATTERN is required for search operation"
        success, files, message = self.file_ops.search_files(self.pattern)
        return success, message
    
    def _write_outputs(self):
        """Write outputs to dotenv file for GitLab"""
        with open('operation_outputs.env', 'w') as f:
            for key, value in self.file_ops.outputs.items():
                # GitLab dotenv format
                f.write(f'{key.upper()}="{value}"\n')


def main():
    """Main entry point"""
    print("GitLab File Operations Runner")
    print(f"Operation: {os.environ.get('OPERATION', 'none')}")
    print(f"Model: {os.environ.get('FCM_MODEL', 'unknown')}")
    print(f"Version: {os.environ.get('FCM_VERSION', 'unknown')}")
    print()
    
    runner = GitLabFileOperationsRunner()
    runner.run()


if __name__ == "__main__":
    main()