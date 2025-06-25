# GitLab CI/CD Toolkit

A collection of reusable GitLab CI/CD templates and components for standardizing development processes across repositories. This toolkit mirrors the functionality of [github.toolkit](github.toolkit/) using the same Formal Conceptual Models (FCMs) as the source of truth.

## Architecture

This repository follows a **six-layer architecture** based on Formal Conceptual Models (FCM) that maintains GitLab CI/CD compatibility while achieving architectural purity:

### Six-Layer Structure

1. **Axioms** (`axioms/`) - Foundational capabilities defined as FCM models ✅ *Implemented*
2. **Logic** (`logic/`) - Compositions and relationships between axioms ⏳ *Planned*
3. **Patterns** (`patterns/`) - Reusable pipeline patterns ⏳ *Planned*
4. **Mechanics** (`mechanics/`) - Implementation templates and operational structures ⏳ *Planned*
5. **Reflection** (`reflection/`) - Self-awareness and analysis capabilities ⏳ *Planned*
6. **Emergence** (`emergence/`) - Discovered patterns and emergent capabilities ⏳ *Planned*

### Bridge System

The repository uses a **bridge architecture** to maintain GitLab CI/CD compatibility:

- **Source Layer**: FCM definitions in `axioms/` (shared with github.toolkit)
- **Interface Layer**: GitLab-compatible templates in `.gitlab-ci/`
- **Bridge Layer**: Automated generation via `.gitlab-bridge/` tools

## FCM Naming Convention

This repository uses the same FCM sources as github.toolkit but generates different platform-specific outputs:

- **FCM Sources** (`axioms/`) - Shared conceptual models between GitHub and GitLab implementations
  - Single source of truth for both platforms
  - Maintained via git submodule reference to github.toolkit
  - GitLab-specific FCMs can be added locally
  
- **Generated Templates** (`.gitlab-ci/`) - GitLab CI/CD templates and job definitions
  - Generated automatically from FCM definitions
  - Manual changes will be overwritten during regeneration
  - Use `.gitlab-bridge/generator.py` to regenerate from FCMs

## Available Components

### Core Actions

Atomic operations that can be combined to build custom pipelines:

- **File Operations**: Create, read, update, delete, copy, move, and search files ✅ *Implemented*
- **Branch Operations**: Create, delete, checkout, list, and merge branches ✅ *Generated*
- **Tag Operations**: Create, delete, push, and list git tags ✅ *Generated*
- **Commit Operations**: Create, amend, list, cherry-pick and revert git commits ✅ *Generated*

### Shell Runner Compatibility

All components are designed to work with GitLab shell runners:

- **Dependency Management**: Graceful handling of missing pip/pip3
- **Environment Validation**: Checks for required tools before execution
- **Fallback Logic**: Continues operation when optional dependencies are missing

## Setup Instructions

### Using Generated Templates

1. Include the main GitLab CI configuration in your `.gitlab-ci.yml`:
   ```yaml
   include:
     - project: 'your-group/gitlab.toolkit'
       file: '.gitlab-ci/includes.yml'
   ```

2. Reference specific job templates in your pipeline stages

3. Set required environment variables for your operations

### Working with FCM Architecture

1. **View capabilities**: Browse `axioms/` directories for available FCM definitions
2. **Modify templates**: Edit FCM files in `axioms/`, then regenerate using `.gitlab-bridge/generator.py`
3. **Add new capabilities**: Create new FCM files and regenerate templates
4. **Never edit directly**: Templates in `.gitlab-ci/` are generated - changes will be overwritten

### Bridge Commands

```bash
# Generate all templates from FCMs
python3 .gitlab-bridge/generator.py

# View generated structure
find .gitlab-ci -name "*.yml" | head -10
```

## Requirements

### GitLab Environment
- GitLab repository with CI/CD enabled
- Shell runner with `python3` and `git` installed
- Permissions to run pipelines and access repository

### Shell Runner Prerequisites
- `python3` (required)
- `git` (required for git operations)
- `pip3` or `pip` (optional - graceful fallback if missing)

## FCM Integration

This repository demonstrates the **same FCM → different platform** approach:

- **github.toolkit**: FCMs → GitHub Actions (Docker-based)
- **gitlab.toolkit**: FCMs → GitLab CI/CD (Shell runner compatible)

### Shared FCM Sources

```bash
# FCMs are shared via git submodule
github.toolkit/axioms/git/branch-operations.fcm  # Source FCM
  ↓ GitHub Bridge
github.toolkit/actions/core/branch-operations/   # GitHub Action
  ↓ GitLab Bridge  
.gitlab-ci/jobs/branch-operations.yml           # GitLab Jobs
```

## Example Usage

### File Operations

```yaml
stages:
  - build

create-config:
  extends: .system_operation
  variables:
    OPERATION: create
    FILE_PATH: "config/app.conf"
    CONTENT: "environment=production"
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### Git Operations

```yaml
create-feature-branch:
  extends: .git_operation
  variables:
    OPERATION: create
    BRANCH_NAME: "feature/new-functionality"
    BASE_BRANCH: "develop"
  rules:
    - when: manual
```

## Testing

The repository includes comprehensive test suites for implemented components:

```bash
# Run file operations tests
cd actions/core/file_operations
python3 -m pytest tests/ -v
```

## Contributing

1. Create a feature branch off main
2. Add or modify FCM definitions in `axioms/`
3. Regenerate templates using the bridge system
4. Test the generated templates
5. Create a merge request

## License

MIT License - See [LICENSE](LICENSE) file for details