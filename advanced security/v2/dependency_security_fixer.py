#!/usr/bin/env python3
"""
Advanced Security Dependency Auto-Fix Script
Focuses exclusively on fixing vulnerable dependencies in requirements.txt files
"""

import os
import sys
import json
import re
import requests
import subprocess
from datetime import datetime
from base64 import b64encode
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class DependencySecurityFixer:
    """Handles dependency vulnerability fixes for Python requirements.txt"""
    
    def __init__(self):
        # Validate required environment variables
        required_vars = {
            'SYSTEM_COLLECTIONURI': os.environ.get('SYSTEM_COLLECTIONURI'),
            'SYSTEM_TEAMPROJECT': os.environ.get('SYSTEM_TEAMPROJECT'),
            'BUILD_REPOSITORY_ID': os.environ.get('BUILD_REPOSITORY_ID'),
            'BUILD_REPOSITORY_NAME': os.environ.get('BUILD_REPOSITORY_NAME'),
            'SYSTEM_ACCESSTOKEN': os.environ.get('SYSTEM_ACCESSTOKEN')
        }
        
        missing_vars = [name for name, value in required_vars.items() if not value]
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"This script must be run within an Azure DevOps pipeline context."
            )
        
        self.organization = required_vars['SYSTEM_COLLECTIONURI'].rstrip('/').split('/')[-1]
        self.project = required_vars['SYSTEM_TEAMPROJECT']
        self.repository_id = required_vars['BUILD_REPOSITORY_ID']
        self.repo_name = required_vars['BUILD_REPOSITORY_NAME']
        self.pat = required_vars['SYSTEM_ACCESSTOKEN']
        
        self.base_url = f"https://advsec.dev.azure.com/{self.organization}/{self.project}/_apis"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {b64encode(f":{self.pat}".encode()).decode()}'
        }
        
        self.prs_created = 0
        self.alerts_processed = []
        self.dry_run = False
        
        # Configuration
        self.max_prs_per_run = 10
        self.branch_prefix = "security/dependency-update"
    
    def fetch_dependency_alerts(self, severity_filter: str = 'high') -> List[Dict]:
        """Fetch only dependency/vulnerable package alerts"""
        print(f"Fetching dependency alerts for repository: {self.repo_name}")
        
        alerts_url = f"{self.base_url}/alert/repositories/{self.repository_id}/alerts"
        params = {
            'criteria.states': 'active',
            'api-version': '7.2-preview.1'
        }
        
        response = requests.get(alerts_url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching alerts: {response.status_code}")
            print(response.text)
            return []
        
        alerts_data = response.json()
        all_alerts = alerts_data.get('value', [])
        
        print(f"Found {len(all_alerts)} total active alerts")
        
        # Filter for dependency-related alerts only
        dependency_keywords = [
            'dependency', 'package', 'pip', 'npm', 'vulnerable',
            'outdated', 'cve', 'security-advisory'
        ]
        
        dependency_alerts = []
        for alert in all_alerts:
            alert_type = alert.get('alertType', '').lower()
            title = alert.get('title', '').lower()
            
            # Check if this is a dependency alert
            is_dependency = any(keyword in alert_type or keyword in title 
                              for keyword in dependency_keywords)
            
            if is_dependency:
                dependency_alerts.append(alert)
        
        print(f"Found {len(dependency_alerts)} dependency alerts")
        
        # Filter by severity
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        min_severity = severity_order.get(severity_filter.lower(), 3)
        
        filtered_alerts = [
            alert for alert in dependency_alerts 
            if severity_order.get(alert.get('severity', '').lower(), 0) >= min_severity
        ]
        
        # Sort by severity (highest first)
        filtered_alerts.sort(
            key=lambda x: severity_order.get(x.get('severity', '').lower(), 0),
            reverse=True
        )
        
        print(f"Found {len(filtered_alerts)} dependency alerts matching severity: {severity_filter}")
        return filtered_alerts
    
    def get_alert_details(self, alert_id: str) -> Optional[Dict]:
        """Fetch detailed information for a specific alert"""
        detail_url = f"{self.base_url}/alert/repositories/{self.repository_id}/alerts/{alert_id}"
        response = requests.get(
            detail_url, 
            headers=self.headers, 
            params={'api-version': '7.2-preview.1'}
        )
        
        if response.status_code != 200:
            print(f"Failed to get details for alert {alert_id}")
            return None
        
        return response.json()
    
    def extract_package_info(self, alert: Dict) -> Optional[Dict]:
        """Extract package name and vulnerable/fixed versions from alert"""
        title = alert.get('title', '')
        description = alert.get('description', '')
        
        # Common patterns for package alerts
        # e.g., "Vulnerable package: requests (CVE-2023-XXXX)"
        # e.g., "Update requests from 2.25.0 to 2.31.0"
        
        package_info = {
            'package_name': None,
            'current_version': None,
            'fixed_version': None,
            'cve': None
        }
        
        # Extract package name
        # Pattern: "package_name" or package_name or 'package_name'
        package_patterns = [
            r'package[:\s]+([a-zA-Z0-9_-]+)',
            r'`([a-zA-Z0-9_-]+)`',
            r'"([a-zA-Z0-9_-]+)"',
            r'\'([a-zA-Z0-9_-]+)\'',
        ]
        
        for pattern in package_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                package_info['package_name'] = match.group(1)
                break
        
        # If not in title, try description
        if not package_info['package_name']:
            for pattern in package_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    package_info['package_name'] = match.group(1)
                    break
        
        # Extract CVE
        cve_match = re.search(r'(CVE-\d{4}-\d+)', title + ' ' + description, re.IGNORECASE)
        if cve_match:
            package_info['cve'] = cve_match.group(1)
        
        # Extract versions
        # Pattern: "from X.Y.Z to A.B.C" or "upgrade to A.B.C"
        version_pattern = r'(\d+\.\d+\.?\d*)'
        versions = re.findall(version_pattern, title + ' ' + description)
        
        if len(versions) >= 2:
            package_info['current_version'] = versions[0]
            package_info['fixed_version'] = versions[-1]
        elif len(versions) == 1:
            package_info['fixed_version'] = versions[0]
        
        # Try to get recommendation from alert
        recommendations = alert.get('recommendations', [])
        for rec in recommendations:
            rec_text = rec.get('text', '')
            if 'upgrade' in rec_text.lower() or 'update' in rec_text.lower():
                version_matches = re.findall(version_pattern, rec_text)
                if version_matches:
                    package_info['fixed_version'] = version_matches[-1]
        
        return package_info if package_info['package_name'] else None
    
    def find_requirements_files(self) -> List[str]:
        """Find all requirements.txt files in the repository"""
        requirements_files = []
        
        # Common locations
        common_files = [
            'requirements.txt',
            'requirements/base.txt',
            'requirements/production.txt',
            'requirements/dev.txt',
            'requirements/requirements.txt',
        ]
        
        for file_path in common_files:
            if os.path.exists(file_path):
                requirements_files.append(file_path)
        
        # Search for any requirements*.txt files
        for root, dirs, files in os.walk('.'):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'venv', '.venv', '__pycache__']]
            
            for file in files:
                if file.startswith('requirements') and file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    # Remove leading ./
                    file_path = file_path[2:] if file_path.startswith('./') else file_path
                    if file_path not in requirements_files:
                        requirements_files.append(file_path)
        
        return requirements_files
    
    def update_requirement(self, file_path: str, package_name: str, 
                          current_version: Optional[str], 
                          fixed_version: str) -> bool:
        """Update a package version in requirements.txt file"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            updated = False
            new_lines = []
            
            for line in lines:
                original_line = line
                stripped = line.strip()
                
                # Skip comments and empty lines
                if not stripped or stripped.startswith('#'):
                    new_lines.append(line)
                    continue
                
                # Parse the requirement line
                # Patterns: package==version, package>=version, package~=version, etc.
                match = re.match(r'^([a-zA-Z0-9_-]+)(.*)', stripped)
                
                if match:
                    pkg_name = match.group(1)
                    rest = match.group(2)
                    
                    # Case-insensitive package name match
                    if pkg_name.lower() == package_name.lower():
                        # Update the version
                        new_line = f"{pkg_name}=={fixed_version}\n"
                        new_lines.append(new_line)
                        updated = True
                        print(f"    Updated: {stripped} -> {pkg_name}=={fixed_version}")
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            if updated:
                with open(file_path, 'w') as f:
                    f.writelines(new_lines)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False
    
    def process_dependency_alert(self, alert: Dict) -> bool:
        """Process a single dependency alert and create PR"""
        alert_id = alert.get('alertId')
        alert_type = alert.get('alertType', '')
        severity = alert.get('severity')
        title = alert.get('title')
        
        print(f"\n{'='*60}")
        print(f"Processing Alert #{alert_id}")
        print(f"  Type: {alert_type}")
        print(f"  Severity: {severity}")
        print(f"  Title: {title}")
        
        # Get detailed information
        alert_details = self.get_alert_details(alert_id)
        if not alert_details:
            return False
        
        # Extract package information
        package_info = self.extract_package_info(alert_details)
        if not package_info:
            print(f"  Could not extract package information")
            return False
        
        package_name = package_info['package_name']
        current_version = package_info['current_version']
        fixed_version = package_info['fixed_version']
        cve = package_info['cve']
        
        print(f"  Package: {package_name}")
        if current_version:
            print(f"  Current Version: {current_version}")
        if fixed_version:
            print(f"  Fixed Version: {fixed_version}")
        if cve:
            print(f"  CVE: {cve}")
        
        if not fixed_version:
            print(f"  No fixed version available, skipping")
            return False
        
        # Find requirements files
        requirements_files = self.find_requirements_files()
        if not requirements_files:
            print(f"  No requirements.txt files found")
            return False
        
        print(f"  Found {len(requirements_files)} requirements file(s): {', '.join(requirements_files)}")
        
        # Create branch
        branch_name = f"{self.branch_prefix}/{package_name}-{fixed_version}"
        
        if self._branch_exists(branch_name):
            print(f"  Branch {branch_name} already exists, skipping...")
            return False
        
        if self.dry_run:
            print(f"  [DRY RUN] Would create branch: {branch_name}")
            print(f"  [DRY RUN] Would update {package_name} to {fixed_version}")
            self.alerts_processed.append({
                'alert_id': alert_id,
                'package': package_name,
                'fixed_version': fixed_version,
                'severity': severity,
                'status': 'dry_run_would_fix'
            })
            return True
        
        # Create and checkout branch
        self._git_run(['checkout', '-b', branch_name])
        
        try:
            # Update package in all requirements files
            files_updated = []
            for req_file in requirements_files:
                if self.update_requirement(req_file, package_name, current_version, fixed_version):
                    files_updated.append(req_file)
            
            if not files_updated:
                print(f"  Package {package_name} not found in any requirements file")
                self._cleanup_branch(branch_name)
                return False
            
            print(f"  Updated {len(files_updated)} file(s): {', '.join(files_updated)}")
            
            # Commit changes
            self._git_run(['add'] + files_updated)
            
            commit_message = self._generate_commit_message(
                alert_details, package_name, fixed_version, cve, files_updated
            )
            self._git_run(['commit', '-m', commit_message])
            self._git_run(['push', 'origin', branch_name])
            
            # Create PR
            pr_created = self._create_pull_request(
                alert_details, branch_name, package_info, files_updated
            )
            
            if pr_created:
                self.prs_created += 1
                self.alerts_processed.append({
                    'alert_id': alert_id,
                    'package': package_name,
                    'fixed_version': fixed_version,
                    'severity': severity,
                    'files_updated': files_updated,
                    'status': 'pr_created'
                })
                return True
            else:
                self._cleanup_branch(branch_name)
                return False
                
        except Exception as e:
            print(f"  Error processing alert: {e}")
            self._cleanup_branch(branch_name)
            return False
        finally:
            self._git_run(['checkout', 'main'])
    
    def _generate_commit_message(self, alert: Dict, package_name: str, 
                                 fixed_version: str, cve: Optional[str],
                                 files_updated: List[str]) -> str:
        """Generate commit message for the dependency update"""
        alert_id = alert.get('alertId')
        severity = alert.get('severity')
        
        message = f"fix(deps): update {package_name} to {fixed_version}\n\n"
        message += f"Resolves security vulnerability (Alert #{alert_id})\n"
        message += f"Severity: {severity}\n"
        
        if cve:
            message += f"CVE: {cve}\n"
        
        message += f"\nUpdated files:\n"
        for file in files_updated:
            message += f"- {file}\n"
        
        return message
    
    def _create_pull_request(self, alert: Dict, branch_name: str, 
                            package_info: Dict, files_updated: List[str]) -> bool:
        """Create a pull request for the dependency update"""
        alert_id = alert.get('alertId')
        severity = alert.get('severity')
        title = alert.get('title')
        description = alert.get('description', '')
        
        package_name = package_info['package_name']
        fixed_version = package_info['fixed_version']
        current_version = package_info.get('current_version', 'unknown')
        cve = package_info.get('cve', '')
        
        if self.dry_run:
            print(f"  [DRY RUN] Would create PR: Update {package_name} to {fixed_version}")
            return True
        
        # Build PR description
        pr_description = f"""## 🔒 Security: Update {package_name}

**Alert ID:** #{alert_id}
**Severity:** {severity.upper()}
{f"**CVE:** {cve}" if cve else ""}

### Vulnerability Details
{description}

### Changes
- **Package:** `{package_name}`
- **Current Version:** `{current_version}`
- **Fixed Version:** `{fixed_version}`

### Files Updated
"""
        
        for file in files_updated:
            pr_description += f"- `{file}`\n"
        
        pr_description += f"""

### Testing Recommendations
1. Run your test suite to ensure compatibility
2. Check for breaking changes in package changelog
3. Verify application functionality
4. Review security advisory details

### Additional Information
- [View Alert Details](https://dev.azure.com/{self.organization}/{self.project}/_git/{self.repo_name}/alerts)
{f"- [CVE Details](https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve})" if cve else ""}

---
*This PR was automatically generated by the Dependency Security Auto-Fix pipeline*
"""
        
        pr_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/git/repositories/{self.repository_id}/pullrequests"
        
        pr_payload = {
            "sourceRefName": f"refs/heads/{branch_name}",
            "targetRefName": "refs/heads/main",
            "title": f"[Security] Update {package_name} to {fixed_version}",
            "description": pr_description,
            "labels": [
                {"name": "security"},
                {"name": "dependencies"},
                {"name": f"severity-{severity}"}
            ]
        }
        
        response = requests.post(
            pr_url,
            headers=self.headers,
            json=pr_payload,
            params={'api-version': '7.0'}
        )
        
        if response.status_code == 201:
            pr_data = response.json()
            pr_id = pr_data.get('pullRequestId')
            print(f"  ✓ Created PR #{pr_id}")
            return True
        else:
            print(f"  ✗ Failed to create PR: {response.status_code}")
            print(response.text)
            return False
    
    def _branch_exists(self, branch_name: str) -> bool:
        """Check if branch exists remotely"""
        result = subprocess.run(
            ['git', 'ls-remote', '--heads', 'origin', branch_name],
            capture_output=True,
            text=True
        )
        return bool(result.stdout)
    
    def _git_run(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run git command"""
        return subprocess.run(['git'] + args, check=True, capture_output=True, text=True)
    
    def _cleanup_branch(self, branch_name: str):
        """Clean up failed branch"""
        try:
            subprocess.run(['git', 'checkout', 'main'], check=False)
            subprocess.run(['git', 'branch', '-D', branch_name], check=False)
        except:
            pass
    
    def run(self, severity_filter: str = 'high') -> Dict:
        """Main execution method"""
        print("="*60)
        print("Dependency Security Auto-Fix Pipeline")
        if self.dry_run:
            print("MODE: DRY RUN (No PRs will be created)")
        print("="*60)
        
        # Fetch dependency alerts
        alerts = self.fetch_dependency_alerts(severity_filter)
        
        if not alerts:
            print("\nNo dependency alerts found to process")
            return self._generate_summary(alerts)
        
        # Process alerts up to limit
        for alert in alerts[:self.max_prs_per_run]:
            if self.prs_created >= self.max_prs_per_run:
                print(f"\nReached maximum PR limit ({self.max_prs_per_run})")
                break
            
            success = self.process_dependency_alert(alert)
            if success:
                self.prs_created += 1
        
        # Generate summary
        summary = self._generate_summary(alerts)
        
        print("\n" + "="*60)
        if self.dry_run:
            print(f"Summary: Would have created {self.prs_created} pull request(s)")
        else:
            print(f"Summary: Created {self.prs_created} pull request(s)")
        print("="*60)
        
        return summary
    
    def _generate_summary(self, all_alerts: List[Dict]) -> Dict:
        """Generate execution summary"""
        return {
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'total_dependency_alerts': len(all_alerts),
            'alerts_processed': len(self.alerts_processed),
            'prs_created': self.prs_created,
            'processed_details': self.alerts_processed,
            'status': 'dry_run' if self.dry_run else ('success' if self.prs_created > 0 else 'no_prs_created')
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix dependency security vulnerabilities')
    parser.add_argument('--severity', default='high', 
                       choices=['critical', 'high', 'medium', 'low'],
                       help='Minimum severity to process')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no PRs created)')
    parser.add_argument('--max-prs', type=int, default=10,
                       help='Maximum PRs to create per run')
    
    args = parser.parse_args()
    
    try:
        fixer = DependencySecurityFixer()
        fixer.dry_run = args.dry_run
        fixer.max_prs_per_run = args.max_prs
        
        if args.dry_run:
            print("\n" + "="*60)
            print("DRY RUN MODE - No PRs will be created")
            print("="*60 + "\n")
        
        summary = fixer.run(severity_filter=args.severity)
        
        # Save summary
        workspace = os.environ.get('PIPELINE_WORKSPACE', '.')
        summary_path = os.path.join(workspace, 'dependency-fix-summary.json')
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nSummary saved to: {summary_path}")
        
        return 0 if summary['prs_created'] > 0 or args.dry_run else 1
        
    except EnvironmentError as e:
        print(f"\n❌ Environment Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 3


if __name__ == '__main__':
    sys.exit(main())
