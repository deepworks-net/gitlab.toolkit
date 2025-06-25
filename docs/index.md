# GitLab Toolkit Documentation

## Overview

The GitLab Toolkit provides GitLab CI/CD templates and scripts generated from Formal Conceptual Models (FCM).

## Components

- **Scripts** - Python scripts for GitLab CI jobs
- **Templates** - GitLab CI job templates  
- **FCM Bridge** - Generator for FCM to GitLab CI transformation

## Usage

Include the toolkit in your GitLab CI pipeline:

```yaml
include:
  - local: '.gitlab-ci/includes.yml'
```