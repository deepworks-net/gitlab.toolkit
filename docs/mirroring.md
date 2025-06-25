# Repository Mirroring to GitHub

The GitLab Toolkit includes an FCM-based repository mirroring system that enables selective publishing of internal repositories to GitHub with different strategies.

## Overview

The mirroring system follows the FCM principle of "same source, different outputs":

- **Internal GitLab**: Full source code, private configurations, development history
- **Public GitHub**: Selective mirror based on strategy (source-only, artifacts-only, or custom)

## Mirroring Strategies

### 1. Full Mirror (`full-mirror`)

Complete repository mirror including all files and history.

**Use case**: Open source projects with no sensitive content
**Output**: Exact replica on GitHub

```yaml
variables:
  MIRROR_STRATEGY: "full-mirror"
```

### 2. Source Only (`source-only`)

Source code, documentation, and configuration files without generated artifacts.

**Use case**: Open source libraries where you want to share source but not CI artifacts
**Includes**:
- Source code (*.py, *.fcm, etc.)
- Documentation (*.md)
- Configuration (*.yml, *.yaml)
- Scripts and actions
- License and legal files

**Excludes**:
- Generated CI/CD templates
- Virtual environments
- Cache files
- Secrets and environment files

```yaml
variables:
  MIRROR_STRATEGY: "source-only"
```

### 3. Artifacts Only (`artifacts-only`)

Generated CI/CD templates and documentation only.

**Use case**: Sharing reusable CI/CD components without exposing source
**Includes**:
- Generated `.gitlab-ci/` templates
- Documentation
- License files

**Excludes**:
- Source code
- Development scripts
- Configuration files

```yaml
variables:
  MIRROR_STRATEGY: "artifacts-only"
  GITHUB_REPO_NAME: "gitlab.toolkit-artifacts"
```

### 4. Selective (`selective`)

Custom selection based on specific include/exclude patterns.

**Use case**: Projects with mixed public/private components
**Configuration**: Define custom patterns per project

```yaml
variables:
  MIRROR_STRATEGY: "selective"
  INCLUDE_PATTERNS: "public/,docs/public/,README.md,LICENSE"
  EXCLUDE_PATTERNS: "internal/,secrets/,config/"
```

## Configuration

### Environment Variables

Required for GitHub mirroring:

```bash
# GitHub Configuration
GITHUB_TOKEN=ghp_xxxxxxxxxxxx        # GitHub Personal Access Token
GITHUB_ORG=deepworks-net             # GitHub organization
GITHUB_REPO_NAME=gitlab.toolkit       # Target repository name

# SSH Configuration (alternative to token)
GITHUB_SSH_PRIVATE_KEY=-----BEGIN ... # SSH private key for GitHub

# GitLab User Information
GITLAB_USER_EMAIL=user@example.com
GITLAB_USER_NAME="GitLab User"
```

### Strategy Configuration

Edit `.gitlab-ci/config/mirror-config.yml` to customize mirroring strategies:

```yaml
strategies:
  source-only:
    include_patterns:
      - "*.md"
      - "*.py" 
      - "*.fcm"
      - "scripts/"
      - "axioms/"
    exclude_patterns:
      - ".gitlab-ci/jobs/"
      - ".venv/"
      - "*.pyc"
```

## Usage

### Manual Mirroring

Trigger mirroring manually through GitLab CI/CD:

1. Go to CI/CD → Pipelines
2. Run Pipeline
3. Choose the desired mirror job:
   - `mirror-source-to-github`
   - `mirror-artifacts-to-github` 
   - `mirror-selective-to-github`

### Automatic Mirroring

Configure automatic mirroring on main branch pushes:

```yaml
# .gitlab-ci.yml
mirror-source-to-github:
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'  # Auto-mirror on main
    - when: manual                       # Manual option always available
```

### FCM-Based Jobs

Use the generated FCM jobs for programmatic mirroring:

```yaml
custom-mirror:
  extends: .system_operation
  variables:
    OPERATION: full-mirror
    TARGET_PLATFORM: github
    TARGET_REPO: my-project
    STRATEGY: source-only
  rules:
    - when: manual
```

## GitHub Setup

### 1. Create GitHub Token

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Generate new token with permissions:
   - `repo` (full repository access)
   - `workflow` (if mirroring GitHub Actions)
   - `admin:org` (if creating repos in organization)

### 2. Add to GitLab Variables

Add the token to GitLab CI/CD variables:

1. Go to Project Settings → CI/CD → Variables
2. Add variable `GITHUB_TOKEN` with the token value
3. Mark as Protected and Masked

### 3. SSH Key (Optional)

For SSH-based authentication:

1. Generate SSH key pair
2. Add public key to GitHub account
3. Add private key as GitLab CI/CD variable `GITHUB_SSH_PRIVATE_KEY`

## Examples

### Open Source Library

Mirror source code to GitHub for public contribution:

```yaml
variables:
  MIRROR_STRATEGY: "source-only"
  GITHUB_REPO_NAME: "my-library"
  MIRROR_BRANCHES: "main,develop"
```

### CI/CD Templates Repository

Share generated templates without source:

```yaml
variables:
  MIRROR_STRATEGY: "artifacts-only"
  GITHUB_REPO_NAME: "ci-templates"
```

### Mixed Public/Private Project

Selective mirroring of public components:

```yaml
variables:
  MIRROR_STRATEGY: "selective"
  INCLUDE_PATTERNS: "public/,docs/api/,README.md,LICENSE"
  EXCLUDE_PATTERNS: "internal/,secrets/,private/"
  GITHUB_REPO_NAME: "project-public"
```

## Troubleshooting

### Authentication Issues

1. Verify GitHub token has correct permissions
2. Check token hasn't expired
3. Ensure GitLab variables are properly configured

### Repository Creation Failures

1. Verify GitHub organization exists
2. Check token has admin:org permissions for organization repos
3. Ensure repository name doesn't conflict

### Mirroring Failures

1. Check include/exclude patterns are correct
2. Verify source files exist
3. Review GitLab CI logs for specific errors

### Pattern Matching

Test patterns locally before deploying:

```bash
# Test include patterns
find . -name "*.py" -o -name "*.md"

# Test exclude patterns  
find . -name "__pycache__" -type d
```

## Security Considerations

1. **Never mirror secrets**: Always exclude configuration files with sensitive data
2. **Review patterns carefully**: Ensure no unintended files are included
3. **Use protected variables**: Mark GitLab CI/CD variables as protected and masked
4. **Audit public repositories**: Regularly review what's published to GitHub
5. **Rotate tokens**: Periodically rotate GitHub tokens and SSH keys

## FCM Integration

The mirroring system is built on FCM principles:

- **Axiom**: `system.repository-mirror` FCM defines the mirroring capability
- **Bridge**: GitLab bridge generates CI/CD jobs from the FCM
- **Implementation**: Python script handles the actual mirroring logic
- **Configuration**: YAML-based strategy definitions

This ensures consistent mirroring behavior across different projects and platforms.