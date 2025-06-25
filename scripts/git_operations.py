#!/usr/bin/env python3
"""
GitLab runtime implementation for git operations
Implements the actual logic for FCM-defined git operations
"""

import os
import sys
import subprocess
import json
from pathlib import Path


class GitOperations:
    """Handle git operations based on FCM definitions"""
    
    def __init__(self):
        self.operation = os.environ.get('OPERATION', '').lower()
        self.branch_name = os.environ.get('BRANCH_NAME', '')
        self.target_branch = os.environ.get('TARGET_BRANCH', '')
        self.remote = os.environ.get('REMOTE', 'false').lower() == 'true'
        self.force = os.environ.get('FORCE', 'false').lower() == 'true'
        self.include_remote = os.environ.get('INCLUDE_REMOTE', 'false').lower() == 'true'
        self.pattern = os.environ.get('PATTERN', '')
        
        # For outputs
        self.outputs = {}
    
    def run(self):
        """Execute the requested git operation"""
        operations = {
            'create': self.create_branch,
            'delete': self.delete_branch,
            'list': self.list_branches,
            'checkout': self.checkout_branch,
            'merge': self.merge_branch
        }
        
        if self.operation not in operations:
            print(f"ERROR: Unknown operation '{self.operation}'")
            sys.exit(1)
        
        try:
            operations[self.operation]()
            self._write_outputs()
            print(f"✓ Operation '{self.operation}' completed successfully")
        except Exception as e:
            print(f"ERROR: Operation failed - {e}")
            sys.exit(1)
    
    def create_branch(self):
        """Create a new branch"""
        if not self.branch_name:
            raise ValueError("BRANCH_NAME is required for create operation")
        
        base_branch = self.target_branch or 'main'
        
        # Fetch latest from remote
        self._run_git(['fetch', 'origin'])
        
        # Create branch from base
        self._run_git(['checkout', '-b', self.branch_name, f'origin/{base_branch}'])
        
        # Push to remote if requested
        if self.remote:
            self._run_git(['push', '-u', 'origin', self.branch_name])
        
        self.outputs['branch_created'] = self.branch_name
        self.outputs['operation_status'] = 'success'
    
    def delete_branch(self):
        """Delete a branch"""
        if not self.branch_name:
            raise ValueError("BRANCH_NAME is required for delete operation")
        
        # Delete local branch
        delete_args = ['branch', '-d', self.branch_name]
        if self.force:
            delete_args[1] = '-D'
        
        self._run_git(delete_args)
        
        # Delete remote branch if requested
        if self.remote:
            self._run_git(['push', 'origin', '--delete', self.branch_name])
        
        self.outputs['branch_deleted'] = self.branch_name
        self.outputs['operation_status'] = 'success'
    
    def list_branches(self):
        """List branches"""
        list_args = ['branch']
        
        if self.include_remote:
            list_args.append('-a')
        
        if self.pattern:
            list_args.extend(['--list', self.pattern])
        
        result = self._run_git(list_args, capture=True)
        
        # Parse branch names
        branches = []
        for line in result.strip().split('\n'):
            if line:
                # Remove leading * and spaces
                branch = line.strip().lstrip('* ')
                # Remove remote prefix for remote branches
                if branch.startswith('remotes/origin/'):
                    branch = branch.replace('remotes/origin/', '')
                branches.append(branch)
        
        self.outputs['branches_list'] = ','.join(branches)
        self.outputs['operation_status'] = 'success'
    
    def checkout_branch(self):
        """Checkout a branch"""
        if not self.branch_name:
            raise ValueError("BRANCH_NAME is required for checkout operation")
        
        checkout_args = ['checkout', self.branch_name]
        if self.force:
            checkout_args.insert(1, '-f')
        
        self._run_git(checkout_args)
        
        # Get current branch
        current = self._run_git(['rev-parse', '--abbrev-ref', 'HEAD'], capture=True).strip()
        
        self.outputs['current_branch'] = current
        self.outputs['operation_status'] = 'success'
    
    def merge_branch(self):
        """Merge branches"""
        if not self.branch_name:
            raise ValueError("BRANCH_NAME is required for merge operation")
        
        target = self.target_branch or 'main'
        
        # Checkout target branch
        self._run_git(['checkout', target])
        
        # Merge source branch
        merge_args = ['merge', self.branch_name]
        if not self.force:
            merge_args.append('--no-ff')
        
        self._run_git(merge_args)
        
        self.outputs['merge_result'] = f"Merged {self.branch_name} into {target}"
        self.outputs['operation_status'] = 'success'
    
    def _run_git(self, args, capture=False):
        """Run a git command"""
        cmd = ['git'] + args
        print(f"Running: {' '.join(cmd)}")
        
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        else:
            subprocess.run(cmd, check=True)
    
    def _write_outputs(self):
        """Write outputs to dotenv file for GitLab"""
        with open('operation_outputs.env', 'w') as f:
            for key, value in self.outputs.items():
                # GitLab dotenv format
                f.write(f'{key.upper()}="{value}"\n')


def main():
    """Main entry point"""
    print("GitLab Git Operations Runner")
    print(f"Operation: {os.environ.get('OPERATION', 'none')}")
    print(f"Model: {os.environ.get('FCM_MODEL', 'unknown')}")
    print(f"Version: {os.environ.get('FCM_VERSION', 'unknown')}")
    print()
    
    operations = GitOperations()
    operations.run()


if __name__ == "__main__":
    main()