#!/usr/bin/env python3
"""
GitLab Repository Mirror Script
Handles mirroring GitLab repositories to GitHub with different strategies
"""

import os
import sys
import yaml
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class RepositoryMirror:
    """Handle repository mirroring operations"""
    
    def __init__(self):
        self.strategy = os.environ.get('STRATEGY', 'source-only')
        self.target_platform = os.environ.get('TARGET_PLATFORM', 'github')
        self.target_repo = self._extract_repo_name(os.environ.get('TARGET_REPO', ''))
        self.github_org = os.environ.get('GITHUB_ORG', 'deepworks-net')
        self.github_token = os.environ.get('GITHUB_TOKEN', '')
        self.source_ref = os.environ.get('SOURCE_REF', 'main')
        self.force_push = os.environ.get('FORCE_PUSH', 'false').lower() == 'true'
        
        self.outputs = {}
        self.config = self._load_config()
    
    def _extract_repo_name(self, target_repo: str) -> str:
        """Extract repository name from URL or return as-is if already a name"""
        if not target_repo:
            return ''
        
        # If it's a URL, extract the repository name
        if target_repo.startswith('http'):
            # Remove .git suffix if present
            repo_name = target_repo.rstrip('/')
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            # Extract just the repository name (last part of path)
            repo_name = repo_name.split('/')[-1]
            return repo_name
        
        # If it's already just a name, return as-is
        return target_repo
    
    def _load_config(self) -> Dict:
        """Load mirror configuration"""
        config_path = Path('.gitlab-ci/config/mirror-config.yml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _run_command(self, cmd: List[str], capture=False, cwd=None) -> str:
        """Run a shell command"""
        print(f"Running: {' '.join(cmd)}")
        
        try:
            if capture:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=True)
                return result.stdout.strip()
            else:
                subprocess.run(cmd, check=True, cwd=cwd)
                return ""
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed with exit code {e.returncode}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"❌ Error output: {e.stderr}")
            if hasattr(e, 'stdout') and e.stdout:
                print(f"📄 Standard output: {e.stdout}")
            raise
    
    def setup_git_config(self):
        """Configure git for mirroring operations"""
        email = os.environ.get('GITLAB_USER_EMAIL', 'gitlab-ci@example.com')
        name = os.environ.get('GITLAB_USER_NAME', 'GitLab CI')
        
        self._run_command(['git', 'config', '--global', 'user.email', email])
        self._run_command(['git', 'config', '--global', 'user.name', name])
        
        print("✅ Git configuration complete")
    
    def create_github_repo_if_needed(self, repo_name: str) -> bool:
        """Create GitHub repository if it doesn't exist"""
        # Check if GitHub CLI is available
        try:
            self._run_command(['which', 'gh'], capture=True)
            gh_available = True
        except subprocess.CalledProcessError:
            gh_available = False
            print("⚠️ GitHub CLI not available - assuming repository exists or will be created manually")
        
        if gh_available:
            try:
                # Check if repo exists
                self._run_command(['gh', 'repo', 'view', f'{self.github_org}/{repo_name}'])
                print(f"📦 Repository {repo_name} already exists")
                return False
            except subprocess.CalledProcessError:
                # Repository doesn't exist, create it
                print(f"📦 Creating GitHub repository: {repo_name}")
                
                description = f"GitLab Toolkit - {self.strategy} mirror"
                self._run_command([
                    'gh', 'repo', 'create', f'{self.github_org}/{repo_name}',
                    '--description', description,
                    '--public',
                    '--clone=false'
                ])
                return True
        else:
            print(f"📦 Skipping repository creation check - assuming {repo_name} exists")
            return False
    
    def mirror_full_repository(self) -> bool:
        """Mirror complete repository with history"""
        print("🔄 Starting full repository mirror...")
        
        repo_url = os.environ.get('CI_REPOSITORY_URL', '')
        
        # Build GitHub URL with authentication
        if self.github_token:
            target_url = f"https://{self.github_token}@github.com/{self.github_org}/{self.target_repo}.git"
        else:
            target_url = f"https://github.com/{self.github_org}/{self.target_repo}.git"
        
        print(f"Source: {repo_url}")
        print(f"Target: https://github.com/{self.github_org}/{self.target_repo}.git")
        
        # Clone as mirror
        self._run_command(['git', 'clone', '--mirror', repo_url, 'repo-mirror'])
        
        # Add GitHub remote and push
        self._run_command(['git', 'remote', 'add', 'github', target_url], cwd='repo-mirror')
        
        print("🔄 Pushing full mirror to existing GitHub repository...")
        # Use --force to overwrite any existing content in the GitHub repo
        self._run_command(['git', 'push', 'github', '--mirror', '--force'], cwd='repo-mirror')
        
        self.outputs['mirror_status'] = 'success'
        self.outputs['target_url'] = f"https://github.com/{self.github_org}/{self.target_repo}"
        
        print("✅ Full mirror completed")
        return True
    
    def mirror_source_only(self) -> bool:
        """Mirror source code without generated artifacts"""
        print("📝 Starting source-only mirror...")
        
        # Get strategy config
        strategy_config = self.config.get('strategies', {}).get('source-only', {})
        include_patterns = strategy_config.get('include_patterns', [])
        exclude_patterns = strategy_config.get('exclude_patterns', [])
        
        # Create new repository
        target_dir = Path('source-mirror')
        target_dir.mkdir(exist_ok=True)
        
        self._run_command(['git', 'init'], cwd=target_dir)
        
        # Copy files based on patterns
        for pattern in include_patterns:
            self._copy_pattern(pattern, target_dir)
        
        # Remove excluded files
        for pattern in exclude_patterns:
            self._remove_pattern(pattern, target_dir)
        
        # Commit and push
        return self._commit_and_push(target_dir, "source-only mirror")
    
    def mirror_artifacts_only(self) -> bool:
        """Mirror generated artifacts and documentation only"""
        print("📦 Starting artifacts-only mirror...")
        
        # Get strategy config
        strategy_config = self.config.get('strategies', {}).get('artifacts-only', {})
        include_patterns = strategy_config.get('include_patterns', [])
        
        # Create new repository
        target_dir = Path('artifacts-mirror')
        target_dir.mkdir(exist_ok=True)
        
        self._run_command(['git', 'init'], cwd=target_dir)
        
        # Copy artifacts
        for pattern in include_patterns:
            self._copy_pattern(pattern, target_dir)
        
        # Create custom README for artifacts
        if strategy_config.get('custom_readme', False):
            self._create_artifacts_readme(target_dir)
        
        return self._commit_and_push(target_dir, "artifacts mirror")
    
    def mirror_selective(self) -> bool:
        """Mirror with custom selection patterns"""
        print("🎯 Starting selective mirror...")
        
        include_patterns = os.environ.get('INCLUDE_PATTERNS', '').split(',')
        exclude_patterns = os.environ.get('EXCLUDE_PATTERNS', '').split(',')
        
        target_dir = Path('selective-mirror')
        target_dir.mkdir(exist_ok=True)
        
        self._run_command(['git', 'init'], cwd=target_dir)
        
        # Copy selected files
        for pattern in include_patterns:
            if pattern.strip():
                self._copy_pattern(pattern.strip(), target_dir)
        
        # Remove excluded files
        for pattern in exclude_patterns:
            if pattern.strip():
                self._remove_pattern(pattern.strip(), target_dir)
        
        return self._commit_and_push(target_dir, "selective mirror")
    
    def _copy_pattern(self, pattern: str, target_dir: Path):
        """Copy files matching pattern to target directory"""
        source_path = Path(pattern)
        target_path = target_dir / pattern
        
        try:
            if source_path.exists():
                if source_path.is_file():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, target_path)
                    print(f"📁 Copied file: {pattern}")
                elif source_path.is_dir():
                    shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                    print(f"📁 Copied directory: {pattern}")
            else:
                print(f"⚠️ Pattern not found: {pattern}")
        except Exception as e:
            print(f"❌ Error copying {pattern}: {e}")
    
    def _remove_pattern(self, pattern: str, target_dir: Path):
        """Remove files matching pattern from target directory"""
        try:
            for path in target_dir.rglob(pattern):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                print(f"🗑️ Removed: {path}")
        except Exception as e:
            print(f"❌ Error removing {pattern}: {e}")
    
    def _create_artifacts_readme(self, target_dir: Path):
        """Create custom README for artifacts repository"""
        readme_content = f"""# GitLab Toolkit - Generated Artifacts

This repository contains generated CI/CD templates and documentation from the GitLab Toolkit.

## Generated Content

- `.gitlab-ci/` - Generated GitLab CI/CD templates from FCM definitions
- Documentation and usage examples

## Source Repository

The source code and FCM definitions are maintained in an internal GitLab instance.

## Usage

Include these templates in your GitLab CI/CD pipelines:

```yaml
include:
  - project: '{self.github_org}/{self.target_repo}'
    file: '.gitlab-ci/includes.yml'
```

## Generated From

- Commit: {os.environ.get('CI_COMMIT_SHA', 'unknown')}
- Pipeline: {os.environ.get('CI_PIPELINE_URL', 'unknown')}
- Generated: {os.environ.get('CI_JOB_STARTED_AT', 'unknown')}
"""
        
        readme_path = target_dir / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        print("📝 Created artifacts README")
    
    def _commit_and_push(self, target_dir: Path, mirror_type: str) -> bool:
        """Commit changes and push to GitHub"""
        try:
            # Add all files
            self._run_command(['git', 'add', '.'], cwd=target_dir)
            
            # Commit
            commit_msg = f"chore: Update {mirror_type} from GitLab CI/CD\n\nSource commit: {os.environ.get('CI_COMMIT_SHA', 'unknown')}\nPipeline: {os.environ.get('CI_PIPELINE_URL', 'unknown')}"
            self._run_command(['git', 'commit', '-m', commit_msg], cwd=target_dir)
            
            # Add remote and push
            if self.github_token:
                target_url = f"https://{self.github_token}@github.com/{self.github_org}/{self.target_repo}.git"
            else:
                target_url = f"https://github.com/{self.github_org}/{self.target_repo}.git"
            self._run_command(['git', 'remote', 'add', 'origin', target_url], cwd=target_dir)
            self._run_command(['git', 'branch', '-M', 'main'], cwd=target_dir)
            
            push_cmd = ['git', 'push', '-u', 'origin', 'main']
            if self.force_push:
                push_cmd.insert(2, '--force')
            
            self._run_command(push_cmd, cwd=target_dir)
            
            self.outputs['mirror_status'] = 'success'
            self.outputs['target_url'] = f"https://github.com/{self.github_org}/{self.target_repo}"
            
            print(f"✅ {mirror_type} completed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to commit and push: {e}")
            self.outputs['mirror_status'] = 'failed'
            return False
    
    def run(self):
        """Execute the mirroring operation"""
        print(f"🚀 Starting repository mirror with strategy: {self.strategy}")
        
        # Validate required environment variables
        if not self.target_repo:
            print("❌ TARGET_REPO environment variable is required")
            sys.exit(1)
        
        if not self.github_token:
            print("⚠️ GITHUB_TOKEN not provided - some operations may fail")
        
        # Setup
        self.setup_git_config()
        self.create_github_repo_if_needed(self.target_repo)
        
        # Execute strategy
        strategies = {
            'full-mirror': self.mirror_full_repository,
            'source-only': self.mirror_source_only,
            'artifacts-only': self.mirror_artifacts_only,
            'selective': self.mirror_selective
        }
        
        if self.strategy in strategies:
            success = strategies[self.strategy]()
            
            if success:
                print(f"✅ Mirror operation completed successfully")
                print(f"🔗 Repository available at: {self.outputs.get('target_url', 'unknown')}")
            else:
                print(f"❌ Mirror operation failed")
                sys.exit(1)
        else:
            print(f"❌ Unknown strategy: {self.strategy}")
            sys.exit(1)
        
        self._write_outputs()
    
    def _write_outputs(self):
        """Write outputs to dotenv file for GitLab"""
        with open('operation_outputs.env', 'w') as f:
            for key, value in self.outputs.items():
                f.write(f'{key.upper()}="{value}"\n')


def main():
    """Main entry point"""
    print("GitLab Repository Mirror Runner")
    print(f"Strategy: {os.environ.get('STRATEGY', 'source-only')}")
    print(f"Target: {os.environ.get('TARGET_PLATFORM', 'github')}")
    print(f"Repository: {os.environ.get('TARGET_REPO', 'unknown')}")
    print()
    
    mirror = RepositoryMirror()
    mirror.run()


if __name__ == "__main__":
    main()