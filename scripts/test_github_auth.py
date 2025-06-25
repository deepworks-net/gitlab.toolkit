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

if __name__ == "__main__":
    success = test_github_auth()
    sys.exit(0 if success else 1)