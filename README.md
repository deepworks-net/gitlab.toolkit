# GitLab Toolkit

GitLab CI/CD Toolkit following FCM (Formal Conceptual Model) bridge architecture.

## Structure

- `axioms/` - FCM definitions for GitLab CI operations
- `scripts/` - Python scripts for GitLab CI jobs
- `.gitlab-ci/` - Generated GitLab CI templates and jobs
- `.gitlab-bridge/` - FCM to GitLab CI generator

## Generated from FCM

This toolkit uses the same FCM definitions as the GitHub Actions toolkit but generates GitLab CI-specific implementations.

## Usage

Include generated templates in your GitLab CI pipeline:

```yaml
include:
  - local: '.gitlab-ci/includes.yml'
```