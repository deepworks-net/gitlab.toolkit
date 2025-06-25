#!/usr/bin/env python3
"""
GitLab Bridge Generator - Transforms FCM definitions into GitLab CI/CD templates

This generator reads Formal Conceptual Model (FCM) files from github.toolkit/axioms/
and generates GitLab-compatible CI/CD job templates and pipeline definitions.

The same FCM source produces different outputs for different platforms:
- GitHub: action.yml + Dockerfile
- GitLab: job templates + pipeline includes
"""

import os
import re
import json
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class FCMParser:
    """Parse FCM (Formal Conceptual Model) files"""
    
    def __init__(self, fcm_path: str):
        self.fcm_path = fcm_path
        self.content = self._read_file()
        self.data = self._parse()
    
    def _read_file(self) -> str:
        """Read FCM file content"""
        with open(self.fcm_path, 'r') as f:
            return f.read()
    
    def _parse(self) -> Dict[str, Any]:
        """Parse FCM format into structured data"""
        data = {
            'model': None,
            'version': None,
            'layer': None,
            'domain': None,
            'capability': None,
            'parameters': [],
            'outputs': [],
            'interface': {},
            'dependencies': [],
            'patterns': []
        }
        
        current_section = None
        lines = self.content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Parse header fields
            if line.startswith('Model:'):
                data['model'] = line.split(':', 1)[1].strip()
            elif line.startswith('Version:'):
                data['version'] = line.split(':', 1)[1].strip()
            elif line.startswith('Layer:'):
                data['layer'] = line.split(':', 1)[1].strip()
            elif line.startswith('Domain:'):
                data['domain'] = line.split(':', 1)[1].strip()
            elif line.startswith('Capability:'):
                data['capability'] = line.split(':', 1)[1].strip()
            
            # Parse sections
            elif line.endswith(':') and not line.startswith('-'):
                current_section = line[:-1].lower()
            
            # Parse section content
            elif current_section and line.startswith('-'):
                content = line[1:].strip()
                
                if current_section == 'parameters':
                    # Parse parameter: name: type (optional)
                    match = re.match(r'(\w+):\s*(.+?)(\s*\(optional\))?$', content)
                    if match:
                        param = {
                            'name': match.group(1),
                            'type': match.group(2).strip(),
                            'required': match.group(3) is None
                        }
                        # Handle choice parameters (e.g., create|delete|list)
                        if '|' in param['type']:
                            param['choices'] = param['type'].split('|')
                            param['type'] = 'choice'
                        data['parameters'].append(param)
                
                elif current_section == 'outputs':
                    data['outputs'].append(content)
                
                elif current_section == 'dependencies':
                    # Parse dependency with optional flag
                    if '(optional)' in content:
                        data['dependencies'].append({
                            'name': content.replace('(optional)', '').strip(),
                            'optional': True
                        })
                    else:
                        data['dependencies'].append({
                            'name': content,
                            'optional': False
                        })
                
                elif current_section == 'patterns':
                    data['patterns'].append(content)
            
            # Parse interface section
            elif current_section == 'interface' and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Parse requirements list
                if key == 'requirements' and value.startswith('['):
                    # Parse list safely without eval
                    requirements = value.strip('[]').split(',')
                    data['interface'][key] = [req.strip() for req in requirements]
                else:
                    data['interface'][key] = value
        
        return data
    
    def get_checksum(self) -> str:
        """Calculate SHA256 checksum of FCM content"""
        return hashlib.sha256(self.content.encode()).hexdigest()


class GitLabBridgeGenerator:
    """Generate GitLab CI/CD templates from FCM definitions"""
    
    def __init__(self, fcm_base_paths: list = None, 
                 output_base_path: str = ".gitlab-ci"):
        if fcm_base_paths is None:
            fcm_base_paths = ["github.toolkit/axioms", "axioms"]
        self.fcm_base_paths = [Path(p) for p in fcm_base_paths]
        self.output_base_path = Path(output_base_path)
        self.generated_files = []
        
    def generate_all(self):
        """Generate GitLab templates for all FCM files"""
        # Ensure output directories exist
        (self.output_base_path / "jobs").mkdir(parents=True, exist_ok=True)
        (self.output_base_path / "templates").mkdir(parents=True, exist_ok=True)
        
        # Find all FCM files from all base paths
        fcm_files = []
        for base_path in self.fcm_base_paths:
            if base_path.exists():
                fcm_files.extend(list(base_path.rglob("*.fcm")))
        
        print(f"Found {len(fcm_files)} FCM files to process")
        
        for fcm_file in fcm_files:
            print(f"\nProcessing: {fcm_file}")
            try:
                self.generate_from_fcm(fcm_file)
            except Exception as e:
                print(f"  ERROR: {e}")
                continue
        
        # Generate master include file
        self._generate_master_include()
        
        print(f"\nGeneration complete. Created {len(self.generated_files)} files.")
    
    def generate_from_fcm(self, fcm_path: Path):
        """Generate GitLab CI templates from a single FCM file"""
        parser = FCMParser(str(fcm_path))
        fcm_data = parser.data
        
        # Determine output paths based on FCM model
        model_parts = fcm_data['model'].split('.')
        domain = model_parts[0]
        capability = model_parts[1] if len(model_parts) > 1 else 'unknown'
        
        # Generate job definition
        job_path = self.output_base_path / "jobs" / f"{capability}.yml"
        self._generate_job_definition(fcm_data, parser, fcm_path, job_path)
        
        # Generate template if it has parameters
        if fcm_data['parameters']:
            template_path = self.output_base_path / "templates" / f"{domain}-operations.yml"
            self._generate_template(fcm_data, parser, fcm_path, template_path, domain)
    
    def _generate_job_definition(self, fcm_data: Dict, parser: FCMParser, 
                                fcm_path: Path, output_path: Path):
        """Generate GitLab job definition from FCM"""
        
        # Build job definition
        job_name = fcm_data['model'].replace('.', '-')
        
        job_def = {
            '# GENERATED FILE - DO NOT EDIT': None,
            f'# Source: {fcm_path.relative_to(".")}': None,
            f'# Model: {fcm_data["model"]} v{fcm_data["version"]}': None,
            f'# Generated: {datetime.utcnow().isoformat()}Z': None,
            '': None,
            '# To modify this job:': None,
            '# 1. Edit the source FCM': None,
            '# 2. Run: python .gitlab-bridge/generator.py': None,
            '# 3. Commit both FCM and generated files': None,
            '': None,
            
            # Include the appropriate template
            'include': [
                {'local': f'.gitlab-ci/templates/{fcm_data["domain"]}-operations.yml'}
            ],
            
            # Job definitions for different actions
        }
        
        # For each action/operation parameter value, create a job
        action_param = next((p for p in fcm_data['parameters'] 
                           if p['name'] == 'action' and p['type'] == 'choice'), None)
        
        if action_param:
            for action in action_param['choices']:
                job_key = f"{job_name}-{action}"
                job_def[job_key] = {
                    'extends': f'.{fcm_data["domain"]}_operation',
                    'variables': {
                        'OPERATION': action,
                        'FCM_MODEL': fcm_data['model'],
                        'FCM_VERSION': fcm_data['version']
                    },
                    'rules': [
                        {'if': '$CI_PIPELINE_SOURCE == "merge_request_event"', 'when': 'manual'},
                        {'if': f'$CI_COMMIT_BRANCH == $DEFAULT_BRANCH && $GIT_OPERATION == "{action}"'}
                    ]
                }
        else:
            # Single job for operations without action choices
            job_def[job_name] = {
                'extends': f'.{fcm_data["domain"]}_operation',
                'variables': {
                    'FCM_MODEL': fcm_data['model'],
                    'FCM_VERSION': fcm_data['version']
                }
            }
        
        # Add bridge sync metadata
        bridge_sync = {
            'source_fcm': str(fcm_path.relative_to('.')),
            'model': fcm_data['model'],
            'version': fcm_data['version'],
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'generator_version': 'gitlab-bridge-1.0.0',
            'checksum': parser.get_checksum()
        }
        
        # Write job definition
        self._write_yaml(job_def, output_path)
        
        # Write bridge sync file
        sync_path = output_path.with_suffix('.bridge-sync')
        with open(sync_path, 'w') as f:
            json.dump(bridge_sync, f, indent=2)
        
        self.generated_files.extend([output_path, sync_path])
        print(f"  ✓ Generated job: {output_path}")
    
    def _generate_template(self, fcm_data: Dict, parser: FCMParser, 
                          fcm_path: Path, output_path: Path, domain: str):
        """Generate GitLab template from FCM"""
        
        # Check if template already exists (multiple FCMs might share a domain)
        if output_path.exists():
            print(f"  → Template already exists: {output_path}")
            return
        
        template = {
            '# GENERATED FILE - DO NOT EDIT': None,
            f'# Domain: {domain}': None,
            f'# Generated: {datetime.utcnow().isoformat()}Z': None,
            '': None,
            
            # Base template for operations (shell runner)
            f'.{domain}_operation_base': {
                'stage': 'build',  # Use standard GitLab stage
                'tags': ['shell'],  # Use shell runner
                'variables': {
                    'GIT_STRATEGY': 'clone',
                    'GIT_DEPTH': '0'
                }
            }
        }
        
        # Add before_script for shell runner dependencies
        before_script = []
        
        # Check for Python availability
        before_script.append('which python3 || (echo "Python3 not found"; exit 1)')
        
        # Install system requirements (assumes sudo access or pre-installed)
        requirements = fcm_data['interface'].get('requirements', [])
        if requirements and len(requirements) > 0:
            # Check if requirements are available
            for req in requirements:
                if req.strip():  # Only add non-empty requirements
                    before_script.append(f'which {req} || (echo "{req} not found, please install it"; exit 1)')
        
        # Git configuration
        if domain == 'git':
            before_script.extend([
                'git config --global user.email "$GITLAB_USER_EMAIL" || git config --global user.email "gitlab-ci@example.com"',
                'git config --global user.name "$GITLAB_USER_NAME" || git config --global user.name "GitLab CI"',
                'git config --global init.defaultBranch main'
            ])
            
            # Set up push credentials
            before_script.append(
                'git remote set-url origin "https://gitlab-ci-token:${CI_JOB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"'
            )
        
        # Install Python dependencies (use pip3 for shell runner)
        before_script.extend([
            '[ -f scripts/requirements.txt ] && pip3 install --user -r scripts/requirements.txt || echo "No requirements.txt or pip3 install failed"',
            'export PATH="$HOME/.local/bin:$PATH"'  # Add user pip binaries to PATH
        ])
        
        if before_script:
            template[f'.{domain}_operation_base']['before_script'] = before_script
        
        # Create operation template with parameters
        operation_template = {
            'extends': f'.{domain}_operation_base',
            'variables': {}
        }
        
        # Add all parameters as variables
        for param in fcm_data['parameters']:
            var_name = param['name'].upper()
            if param['type'] == 'boolean':
                operation_template['variables'][var_name] = 'false'
            elif param['type'] == 'choice':
                operation_template['variables'][var_name] = param['choices'][0]
            else:
                operation_template['variables'][var_name] = ''
        
        # Add script (use python3 explicitly for shell runner)
        operation_template['script'] = [
            f'python3 scripts/{domain}_operations.py'
        ]
        
        # Add artifacts for outputs
        if fcm_data['outputs']:
            operation_template['artifacts'] = {
                'reports': {
                    'dotenv': 'operation_outputs.env'
                },
                'expire_in': '1 hour'
            }
        
        template[f'.{domain}_operation'] = operation_template
        
        # Write template
        self._write_yaml(template, output_path)
        self.generated_files.append(output_path)
        print(f"  ✓ Generated template: {output_path}")
    
    def _generate_master_include(self):
        """Generate master include file for all templates"""
        include_path = self.output_base_path / "includes.yml"
        
        includes = {
            '# GENERATED FILE - DO NOT EDIT': None,
            '# Master include file for all GitLab CI templates': None,
            f'# Generated: {datetime.utcnow().isoformat()}Z': None,
            '': None,
            
            'include': []
        }
        
        # Add all template files
        for template_file in sorted((self.output_base_path / "templates").glob("*.yml")):
            includes['include'].append({
                'local': f'.gitlab-ci/templates/{template_file.name}'
            })
        
        # Add all job files
        for job_file in sorted((self.output_base_path / "jobs").glob("*.yml")):
            includes['include'].append({
                'local': f'.gitlab-ci/jobs/{job_file.name}'
            })
        
        self._write_yaml(includes, include_path)
        self.generated_files.append(include_path)
        print(f"\n✓ Generated master include: {include_path}")
    
    def _write_yaml(self, data: Dict, output_path: Path):
        """Write YAML file with proper formatting"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            # Write comments and empty values manually
            for key, value in data.items():
                if key.startswith('#'):
                    f.write(f"{key}\n")
                elif key == '':
                    f.write('\n')
                elif value is None:
                    continue
                else:
                    # Write the rest as YAML
                    yaml.dump({key: value}, f, default_flow_style=False, sort_keys=False)


def main():
    """Main entry point"""
    import sys
    
    # Check if github.toolkit exists
    if not Path("github.toolkit/axioms").exists():
        print("ERROR: github.toolkit/axioms not found!")
        print("Make sure github.toolkit is properly initialized as a submodule.")
        sys.exit(1)
    
    # Create generator
    generator = GitLabBridgeGenerator()
    
    # Run generation
    generator.generate_all()
    
    print("\nNext steps:")
    print("1. Review generated files in .gitlab-ci/")
    print("2. Implement runtime scripts in scripts/")
    print("3. Update .gitlab-ci.yml to include generated templates")
    print("4. Test the generated jobs")


if __name__ == "__main__":
    main()