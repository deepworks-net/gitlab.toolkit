# Version Calculator Action

Calculate semantic versions based on git tags and commit history. Compatible with both GitHub Actions and GitLab CI environments.

## Usage

### GitHub Actions

```yaml
- name: Calculate Version
  id: version
  uses: ./actions/core/version_calculator
  with:
    default_version: "v0.1.0"
    version_prefix: "v"
    tag_pattern: "v*"
```

### GitLab CI

```yaml
version-calculation:
  extends: .version_operation
  variables:
    DEFAULT_VERSION: "v0.1.0"
    VERSION_PREFIX: "v" 
    TAG_PATTERN: "v*"
```

## Inputs

| Name | Description | Required | Default |
|------|-------------|----------|---------|
| `default_version` | Default version when no tags exist | No | `v0.1.0` |
| `version_prefix` | Prefix for version tags | No | `v` |
| `tag_pattern` | Pattern to match version tags | No | `v*` |

## Outputs

| Name | Description |
|------|-------------|
| `current_version` | Current version (latest tag or default) |
| `next_version` | Calculated next version |
| `commit_count` | Number of commits since last tag |

## Version Calculation Logic

1. Find the latest tag matching the specified pattern
2. Count commits since that tag
3. Calculate next version by incrementing patch number by commit count
4. If no tags exist, use the default version

## Examples

### Basic Usage
Latest tag: `v1.2.0`, 3 commits since tag
- Current Version: `v1.2.0`
- Next Version: `v1.2.3`
- Commit Count: `3`

### No Tags
No tags exist
- Current Version: `v0.1.0` (default)
- Next Version: `v0.1.0`
- Commit Count: `0`

### Custom Prefix
Using `release-` prefix with tag `release-2.1.0`
- Current Version: `release-2.1.0`
- Next Version: `release-2.1.X` (where X = commit count)

## Testing

Run the test suite:

```bash
cd actions/core/version_calculator
python -m pytest
```

Tests include both unit tests and integration tests with real git operations.