#!/usr/bin/env python3
"""
GitLab Version Calculator - Based on FCM version.calculator
Calculates semantic versions based on git tags and commit history
"""

import os
import subprocess
import re
import sys
from pathlib import Path

def setup_git():
    """Configure git for GitLab CI environment."""
    try:
        # GitLab CI already has workspace configured, but ensure it's safe
        workspace = os.environ.get('CI_PROJECT_DIR', '/builds')
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

def write_gitlab_outputs(outputs):
    """Write outputs to dotenv file for GitLab CI"""
    output_file = Path('operation_outputs.env')
    with open(output_file, 'w') as f:
        for key, value in outputs.items():
            f.write(f'{key.upper()}={value}\n')
    print(f"✓ Outputs written to {output_file}")

def main():
    """Main function."""
    print("🏷️ GitLab Version Calculator")
    print("=" * 40)
    
    # Get inputs from GitLab CI environment variables
    default_version = os.environ.get('DEFAULT_VERSION', 'v0.1.0')
    version_prefix = os.environ.get('VERSION_PREFIX', 'v')
    tag_pattern = os.environ.get('TAG_PATTERN', 'v*')
    
    print(f"Configuration:")
    print(f"  Default Version: {default_version}")
    print(f"  Version Prefix: {version_prefix}")
    print(f"  Tag Pattern: {tag_pattern}")
    print()

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
    print("Results:")
    print(f"  Current Version: {current_version}")
    print(f"  Next Version: {next_version}")
    print(f"  Commit Count: {commit_count}")
    print()
    
    # Write outputs for GitLab CI
    outputs = {
        'current_version': current_version,
        'next_version': next_version,
        'commit_count': str(commit_count)
    }
    
    write_gitlab_outputs(outputs)
    print("✅ Version calculation completed successfully")

if __name__ == "__main__":
    main()