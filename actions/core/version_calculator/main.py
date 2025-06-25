#!/usr/bin/env python3
"""
GitLab Version Calculator Action
Adapted from GitHub Actions version_calculator for GitLab CI compatibility
"""

import os
import subprocess
import re
import sys

def setup_git():
    """Configure git to trust the workspace."""
    try:
        # For GitLab CI environment
        workspace = os.environ.get('CI_PROJECT_DIR', '/github/workspace')
        subprocess.check_output(['git', 'config', '--global', '--add', 'safe.directory', workspace], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Error configuring git: {e}")
        # Continue - GitLab CI should already have git configured

def get_latest_tag(tag_pattern='v*'):
    """Retrieve the latest version tag matching pattern."""
    try:
        # Get all tags matching pattern
        output = subprocess.check_output(['git', 'tag', '-l', tag_pattern, '--sort=-v:refname'], text=True).strip()
        if output:
            return output.splitlines()[0]
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error fetching tags: {e}")
        sys.exit(1)

def get_commit_count_since_tag(tag):
    """Count commits since the specified tag."""
    try:
        output = subprocess.check_output(['git', 'rev-list', f'{tag}..HEAD', '--count'], text=True).strip()
        return int(output)
    except subprocess.CalledProcessError as e:
        print(f"Error counting commits: {e}")
        sys.exit(1)

def validate_version_format(version, prefix):
    """Validate version string format."""
    pattern = f'^{prefix}\\d+\\.\\d+\\.\\d+$'
    if not re.match(pattern, version):
        print(f"Invalid version format: {version}")
        sys.exit(1)
    return True

def write_outputs(current_version, next_version, commit_count):
    """Write outputs for both GitHub Actions and GitLab CI"""
    # GitHub Actions output
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"current_version={current_version}\n")
            f.write(f"next_version={next_version}\n")
            f.write(f"commit_count={commit_count}\n")
    
    # GitLab CI output
    gitlab_output = 'operation_outputs.env'
    with open(gitlab_output, 'w') as f:
        f.write(f"CURRENT_VERSION={current_version}\n")
        f.write(f"NEXT_VERSION={next_version}\n")
        f.write(f"COMMIT_COUNT={commit_count}\n")

def main():
    """Main function."""
    print("🏷️ Version Calculator")
    
    # Get inputs with defaults - support both GitHub Actions and GitLab CI
    default_version = os.environ.get('INPUT_DEFAULT_VERSION') or os.environ.get('DEFAULT_VERSION', 'v0.1.0')
    version_prefix = os.environ.get('INPUT_VERSION_PREFIX') or os.environ.get('VERSION_PREFIX', 'v')
    tag_pattern = os.environ.get('INPUT_TAG_PATTERN') or os.environ.get('TAG_PATTERN', 'v*')

    # Validate inputs
    validate_version_format(default_version, version_prefix)

    # Setup git
    setup_git()

    # Get latest tag
    latest_tag = get_latest_tag(tag_pattern)
    current_version = latest_tag if latest_tag else default_version
    
    # Calculate commit count
    commit_count = 0
    if latest_tag:
        commit_count = get_commit_count_since_tag(latest_tag)
    
    # Calculate next version
    if latest_tag and commit_count > 0:
        pattern = f'{version_prefix}(\\d+)\\.(\\d+)\\.(\\d+)'
        match = re.match(pattern, latest_tag)
        if not match:
            print(f"Invalid version format: {latest_tag}")
            sys.exit(1)
        major, minor, patch = map(int, match.groups())
        next_version = f"{version_prefix}{major}.{minor}.{patch + commit_count}"
    else:
        next_version = current_version

    # Output results
    print(f"Current Version: {current_version}")
    print(f"Next Version: {next_version}")
    print(f"Commit Count: {commit_count}")
    
    # Write outputs
    write_outputs(current_version, next_version, commit_count)

if __name__ == "__main__":
    main()