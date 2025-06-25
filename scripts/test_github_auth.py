#!/usr/bin/env python3
"""
Minimal test script to verify GitHub token authentication
"""

import os
import subprocess
import sys

def test_github_auth():
    """Test GitHub authentication with minimal operations"""
    
    # Get environment variables
    github_token = os.environ.get('GITHUB_TOKEN', '')
    github_org = os.environ.get('GITHUB_ORG', 'deepworks-net')
    target_repo = os.environ.get('TARGET_REPO', 'gitlab.toolkit')
    
    print("=== GitHub Authentication Test ===")
    print(f"Organization: {github_org}")
    print(f"Repository: {target_repo}")
    print(f"Token present: {'Yes' if github_token else 'No'}")
    print()
    
    if not github_token:
        print("❌ GITHUB_TOKEN not set!")
        return False
    
    # Extract repo name if full URL provided
    if target_repo.startswith('http'):
        repo_name = target_repo.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        target_repo = repo_name
        print(f"Extracted repo name: {target_repo}")
    
    # Test different authentication formats
    test_formats = [
        ('Token only', f'https://{github_token}@github.com/{github_org}/{target_repo}.git'),
        ('Token with empty password', f'https://{github_token}:@github.com/{github_org}/{target_repo}.git'),
        ('Token as x-oauth-basic', f'https://{github_token}:x-oauth-basic@github.com/{github_org}/{target_repo}.git'),
        ('Token as password', f'https://oauth2:{github_token}@github.com/{github_org}/{target_repo}.git'),
    ]
    
    for format_name, url in test_formats:
        print(f"\n🔍 Testing format: {format_name}")
        # Mask the token in display
        display_url = url.replace(github_token, '[MASKED]')
        print(f"   URL: {display_url}")
        
        try:
            # Use git ls-remote to test authentication
            result = subprocess.run(
                ['git', 'ls-remote', url, 'HEAD'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"   ✅ SUCCESS - Authentication working!")
                print(f"   HEAD: {result.stdout.strip()}")
                return True
            else:
                print(f"   ❌ FAILED - Exit code: {result.returncode}")
                if result.stderr:
                    # Clean error message to not expose token
                    error = result.stderr.replace(github_token, '[MASKED]')
                    print(f"   Error: {error.strip()}")
        except subprocess.TimeoutExpired:
            print(f"   ❌ TIMEOUT - Request took too long")
        except Exception as e:
            print(f"   ❌ ERROR - {type(e).__name__}: {e}")
    
    print("\n❌ All authentication formats failed!")
    return False

def test_git_clone():
    """Test actual git clone with the working authentication"""
    print("\n=== Testing Git Clone ===")
    
    github_token = os.environ.get('GITHUB_TOKEN', '')
    github_org = os.environ.get('GITHUB_ORG', 'deepworks-net')
    target_repo = os.environ.get('TARGET_REPO', 'gitlab.toolkit')
    
    # Extract repo name if full URL
    if target_repo.startswith('http'):
        repo_name = target_repo.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        target_repo = repo_name
    
    # Use the format that worked in ls-remote
    clone_url = f'https://{github_token}@github.com/{github_org}/{target_repo}.git'
    
    print("🔍 Testing git clone...")
    print(f"   Target: https://[MASKED]@github.com/{github_org}/{target_repo}.git")
    
    try:
        # Clean up any existing test directory
        subprocess.run(['rm', '-rf', 'test-clone'], capture_output=True)
        
        # Try to clone
        result = subprocess.run(
            ['git', 'clone', clone_url, 'test-clone'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✅ Clone successful!")
            # Clean up
            subprocess.run(['rm', '-rf', 'test-clone'], capture_output=True)
            return True
        else:
            print(f"   ❌ Clone failed - Exit code: {result.returncode}")
            error = result.stderr.replace(github_token, '[MASKED]')
            print(f"   Error: {error}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR - {type(e).__name__}: {e}")
        return False

def test_mirror_push():
    """Test mirror clone and push like the actual mirror script"""
    print("\n=== Testing Mirror Push ===")
    
    github_token = os.environ.get('GITHUB_TOKEN', '')
    github_org = os.environ.get('GITHUB_ORG', 'deepworks-net')
    target_repo = os.environ.get('TARGET_REPO', 'gitlab.toolkit')
    repo_url = os.environ.get('CI_REPOSITORY_URL', '')
    
    # Extract repo name if full URL
    if target_repo.startswith('http'):
        repo_name = target_repo.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        target_repo = repo_name
    
    print("🔍 Testing mirror clone and push...")
    print(f"   Source: {repo_url}")
    print(f"   Target: https://github.com/{github_org}/{target_repo}.git")
    
    try:
        # Clean up
        subprocess.run(['rm', '-rf', 'test-mirror'], capture_output=True)
        
        # Clone as mirror
        print("   📥 Cloning as mirror...")
        result = subprocess.run(
            ['git', 'clone', '--mirror', repo_url, 'test-mirror'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"   ❌ Mirror clone failed - Exit code: {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False
            
        # Add GitHub remote
        github_url = f'https://{github_token}@github.com/{github_org}/{target_repo}.git'
        print("   🔗 Adding GitHub remote...")
        result = subprocess.run(
            ['git', 'remote', 'add', 'github', github_url],
            cwd='test-mirror',
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"   ❌ Add remote failed - Exit code: {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False
            
        # Debug: Check what URL git actually has
        print("   🔍 Checking remote URL...")
        result = subprocess.run(
            ['git', 'remote', '-v'],
            cwd='test-mirror',
            capture_output=True,
            text=True
        )
        print(f"   Remotes: {result.stdout.replace(github_token, '[MASKED]')}")
            
        # Try push with --dry-run first
        print("   🧪 Testing push (dry run)...")
        # Push to the remote name, not the URL
        result = subprocess.run(
            ['git', 'push', 'github', '--mirror', '--dry-run'],
            cwd='test-mirror',
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✅ Mirror push test successful (dry run)!")
            # Clean up
            subprocess.run(['rm', '-rf', 'test-mirror'], capture_output=True)
            return True
        else:
            print(f"   ❌ Mirror push failed - Exit code: {result.returncode}")
            error = result.stderr.replace(github_token, '[MASKED]')
            print(f"   Error: {error}")
            # Clean up
            subprocess.run(['rm', '-rf', 'test-mirror'], capture_output=True)
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR - {type(e).__name__}: {e}")
        subprocess.run(['rm', '-rf', 'test-mirror'], capture_output=True)
        return False

if __name__ == "__main__":
    # First test authentication
    auth_success = test_github_auth()
    
    if auth_success:
        # If auth works, test clone
        clone_success = test_git_clone()
        
        if clone_success:
            # If clone works, test mirror push
            mirror_success = test_mirror_push()
            sys.exit(0 if mirror_success else 1)
        else:
            sys.exit(1)
    else:
        sys.exit(1)