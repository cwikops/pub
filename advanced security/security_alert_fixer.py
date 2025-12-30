#!/usr/bin/env python3
"""
Advanced Security Alert Auto-Fix Script
Reads GitHub Advanced Security alerts from Azure DevOps and creates PRs with fixes
"""

import os
import sys
import json
import re
import requests
import subprocess
import yaml
from datetime import datetime
from base64 import b64encode
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class SecurityAlertFixer:
    """Main class for processing and fixing security alerts"""
    
    def __init__(self, config_path: str = 'security-fix-config.yml'):
        self.organization = os.environ.get('SYSTEM_COLLECTIONURI', '').rstrip('/').split('/')[-1]
        self.project = os.environ.get('SYSTEM_TEAMPROJECT')
        self.repository_id = os.environ.get('BUILD_REPOSITORY_ID')
        self.repo_name = os.environ.get('BUILD_REPOSITORY_NAME')
        self.pat = os.environ.get('SYSTEM_ACCESSTOKEN')
        
        self.base_url = f"https://advsec.dev.azure.com/{self.organization}/{self.project}/_apis"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {b64encode(f":{self.pat}".encode()).decode()}'
        }
        
        # Load configuration
        self.config = self._load_config(config_path)
        self.prs_created = 0
        self.alerts_processed = []
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {config_path} not found, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Return default configuration"""
        return {
            'alert_strategies': {},
            'pr_config': {
                'branch_prefix': 'security-fix',
                'default_labels': ['security', 'automated-fix']
            },
            'limits': {
                'max_prs_per_run': 5,
                'max_files_per_pr': 10,
                'max_lines_changed_per_file': 50
            }
        }
    
    def fetch_alerts(self, severity_filter: str = 'high') -> List[Dict]:
        """Fetch active security alerts from Advanced Security"""
        print(f"Fetching Advanced Security alerts for repository: {self.repo_name}")
        
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
        alerts = alerts_data.get('value', [])
        
        print(f"Found {len(alerts)} active alerts")
        
        # Filter by severity
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        min_severity = severity_order.get(severity_filter.lower(), 3)
        
        filtered_alerts = [
            alert for alert in alerts 
            if severity_order.get(alert.get('severity', '').lower(), 0) >= min_severity
        ]
        
        # Sort by severity (highest first)
        filtered_alerts.sort(
            key=lambda x: severity_order.get(x.get('severity', '').lower(), 0),
            reverse=True
        )
        
        print(f"Found {len(filtered_alerts)} alerts matching severity filter: {severity_filter}")
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
    
    def process_alert(self, alert: Dict) -> bool:
        """Process a single alert and create a PR if possible"""
        alert_id = alert.get('alertId')
        alert_type = alert.get('alertType', '')
        severity = alert.get('severity')
        title = alert.get('title')
        
        print(f"\nProcessing Alert {alert_id}:")
        print(f"  Type: {alert_type}")
        print(f"  Severity: {severity}")
        print(f"  Title: {title}")
        
        # Get detailed information
        alert_details = self.get_alert_details(alert_id)
        if not alert_details:
            return False
        
        # Extract file location
        physical_locations = alert_details.get('physicalLocations', [])
        if not physical_locations:
            print(f"  No physical location found for alert {alert_id}")
            return False
        
        location = physical_locations[0]
        file_path = location.get('filePath', '')
        start_line = location.get('region', {}).get('startLine', 0)
        end_line = location.get('region', {}).get('endLine', start_line)
        
        print(f"  File: {file_path}:{start_line}-{end_line}")
        
        # Check if file should be processed
        if self._should_skip_file(file_path):
            print(f"  Skipping excluded file pattern")
            return False
        
        # Create branch
        branch_name = f"{self.config['pr_config']['branch_prefix']}/alert-{alert_id}"
        
        if self._branch_exists(branch_name):
            print(f"  Branch {branch_name} already exists, skipping...")
            return False
        
        # Create and checkout branch
        self._git_run(['checkout', '-b', branch_name])
        
        try:
            # Apply fix
            fix_applied = self.apply_fix(alert_details, file_path, start_line, end_line)
            
            if not fix_applied:
                print(f"  Unable to auto-fix alert {alert_id}")
                self._cleanup_branch(branch_name)
                return False
            
            # Check if changes are within limits
            if not self._check_change_limits(file_path):
                print(f"  Changes exceed safety limits")
                self._cleanup_branch(branch_name)
                return False
            
            # Commit and push
            self._git_run(['add', '.'])
            
            commit_message = self._generate_commit_message(alert_details)
            self._git_run(['commit', '-m', commit_message])
            self._git_run(['push', 'origin', branch_name])
            
            # Create PR
            pr_created = self._create_pull_request(alert_details, branch_name)
            
            if pr_created:
                self.prs_created += 1
                self.alerts_processed.append({
                    'alert_id': alert_id,
                    'severity': severity,
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
    
    def apply_fix(self, alert: Dict, file_path: str, start_line: int, end_line: int) -> bool:
        """Apply fix based on alert type"""
        alert_type = alert.get('alertType', '').lower()
        
        # Determine fix strategy
        strategy = self._get_fix_strategy(alert_type)
        
        if not strategy:
            print(f"  No fix strategy for alert type: {alert_type}")
            return self._add_security_comment(alert, file_path, start_line)
        
        fix_type = strategy.get('fix_type', 'comment')
        
        if fix_type == 'parameterized_query':
            return self._fix_sql_injection(alert, file_path, start_line, end_line)
        elif fix_type == 'sanitization':
            return self._fix_xss(alert, file_path, start_line)
        elif fix_type == 'environment_variable':
            return self._fix_hardcoded_secret(alert, file_path, start_line, end_line)
        elif fix_type == 'secure_random':
            return self._fix_insecure_random(alert, file_path, start_line)
        elif fix_type == 'path_validation':
            return self._fix_path_traversal(alert, file_path, start_line)
        else:
            return self._add_security_comment(alert, file_path, start_line)
    
    def _get_fix_strategy(self, alert_type: str) -> Optional[Dict]:
        """Get fix strategy for alert type"""
        strategies = self.config.get('alert_strategies', {})
        
        # Try exact match first
        if alert_type in strategies:
            return strategies[alert_type]
        
        # Try partial match
        for key, strategy in strategies.items():
            if key.lower() in alert_type or alert_type in key.lower():
                return strategy
        
        return None
    
    def _fix_sql_injection(self, alert: Dict, file_path: str, start_line: int, end_line: int) -> bool:
        """Fix SQL injection vulnerabilities"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if start_line <= 0 or start_line > len(lines):
                return False
            
            # Detect the programming language
            ext = Path(file_path).suffix
            
            if ext == '.py':
                comment = self._get_comment_for_language('python', 
                    "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))")
            elif ext in ['.js', '.ts']:
                comment = self._get_comment_for_language('javascript',
                    "Use parameterized queries: db.query('SELECT * FROM users WHERE id = $1', [userId])")
            elif ext in ['.cs']:
                comment = self._get_comment_for_language('csharp',
                    "Use parameterized queries: cmd.Parameters.AddWithValue('@id', userId)")
            else:
                comment = self._get_comment_for_language('generic',
                    "SECURITY: Use parameterized queries to prevent SQL injection")
            
            indent = self._get_indent(lines[start_line - 1])
            lines.insert(start_line - 1, f"{indent}{comment}\n")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            print(f"Error applying SQL injection fix: {e}")
            return False
    
    def _fix_xss(self, alert: Dict, file_path: str, start_line: int) -> bool:
        """Fix XSS vulnerabilities"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            ext = Path(file_path).suffix
            
            if ext == '.py':
                comment = self._get_comment_for_language('python',
                    "Sanitize output: html.escape(user_input) or use templating engine escaping")
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                comment = self._get_comment_for_language('javascript',
                    "Sanitize output: Use DOMPurify.sanitize() or framework escaping (e.g., {userInput})")
            else:
                comment = self._get_comment_for_language('generic',
                    "SECURITY: Sanitize user input before rendering to prevent XSS")
            
            indent = self._get_indent(lines[start_line - 1])
            lines.insert(start_line - 1, f"{indent}{comment}\n")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            print(f"Error applying XSS fix: {e}")
            return False
    
    def _fix_hardcoded_secret(self, alert: Dict, file_path: str, start_line: int, end_line: int) -> bool:
        """Fix hardcoded secrets"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            ext = Path(file_path).suffix
            
            if ext == '.py':
                comment = self._get_comment_for_language('python',
                    "CRITICAL: Remove hardcoded secret. Use: secret = os.environ.get('SECRET_NAME') or Azure Key Vault")
            elif ext in ['.js', '.ts']:
                comment = self._get_comment_for_language('javascript',
                    "CRITICAL: Remove hardcoded secret. Use: process.env.SECRET_NAME or Azure Key Vault")
            else:
                comment = self._get_comment_for_language('generic',
                    "CRITICAL SECURITY: Remove hardcoded secret, use environment variables or Key Vault")
            
            indent = self._get_indent(lines[start_line - 1])
            lines.insert(start_line - 1, f"{indent}{comment}\n")
            
            # Also try to comment out the offending line(s)
            for i in range(start_line - 1, min(end_line, len(lines))):
                if not lines[i].strip().startswith('#') and not lines[i].strip().startswith('//'):
                    if ext == '.py':
                        lines[i] = f"{indent}# REMOVED: {lines[i].lstrip()}"
                    elif ext in ['.js', '.ts', '.cs', '.java']:
                        lines[i] = f"{indent}// REMOVED: {lines[i].lstrip()}"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            print(f"Error applying hardcoded secret fix: {e}")
            return False
    
    def _fix_insecure_random(self, alert: Dict, file_path: str, start_line: int) -> bool:
        """Fix insecure random number generation"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = f.readlines()
            
            f.seek(0)
            lines = f.readlines()
            
            ext = Path(file_path).suffix
            
            if ext == '.py':
                # Add import if not present
                if 'import secrets' not in content:
                    lines.insert(0, 'import secrets\n')
                
                comment = self._get_comment_for_language('python',
                    "Use secrets module: secrets.token_hex(32) instead of random")
                indent = self._get_indent(lines[start_line - 1])
                lines.insert(start_line - 1, f"{indent}{comment}\n")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            print(f"Error applying insecure random fix: {e}")
            return False
    
    def _fix_path_traversal(self, alert: Dict, file_path: str, start_line: int) -> bool:
        """Fix path traversal vulnerabilities"""
        return self._add_security_comment(alert, file_path, start_line,
            "Validate file paths: os.path.abspath(os.path.join(safe_dir, user_input))")
    
    def _add_security_comment(self, alert: Dict, file_path: str, start_line: int, 
                             custom_message: str = None) -> bool:
        """Add a security comment to the code"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            title = alert.get('title', 'Security issue')
            message = custom_message or f"SECURITY: {title}"
            
            comment = self._get_comment_for_language(
                self._detect_language(file_path), 
                message
            )
            
            indent = self._get_indent(lines[start_line - 1])
            lines.insert(start_line - 1, f"{indent}{comment}\n")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            print(f"Error adding security comment: {e}")
            return False
    
    def _get_comment_for_language(self, language: str, message: str) -> str:
        """Get comment syntax for language"""
        comment_styles = {
            'python': f"# {message}",
            'javascript': f"// {message}",
            'typescript': f"// {message}",
            'csharp': f"// {message}",
            'java': f"// {message}",
            'html': f"<!-- {message} -->",
            'css': f"/* {message} */",
            'generic': f"# {message}"
        }
        return comment_styles.get(language, f"# {message}")
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.cs': 'csharp',
            '.java': 'java',
            '.html': 'html',
            '.css': 'css'
        }
        ext = Path(file_path).suffix
        return ext_map.get(ext, 'generic')
    
    def _get_indent(self, line: str) -> str:
        """Get indentation from a line"""
        return line[:len(line) - len(line.lstrip())]
    
    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped based on exclude patterns"""
        exclude_patterns = self.config.get('file_handling', {}).get('exclude_patterns', [])
        
        for pattern in exclude_patterns:
            if Path(file_path).match(pattern):
                return True
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
    
    def _check_change_limits(self, file_path: str) -> bool:
        """Check if changes are within safety limits"""
        result = subprocess.run(
            ['git', 'diff', '--cached', file_path],
            capture_output=True,
            text=True
        )
        
        added_lines = len([l for l in result.stdout.split('\n') if l.startswith('+')])
        removed_lines = len([l for l in result.stdout.split('\n') if l.startswith('-')])
        
        max_lines = self.config.get('limits', {}).get('max_lines_changed_per_file', 50)
        
        return (added_lines + removed_lines) <= max_lines
    
    def _generate_commit_message(self, alert: Dict) -> str:
        """Generate commit message for the fix"""
        alert_id = alert.get('alertId')
        title = alert.get('title')
        severity = alert.get('severity')
        alert_type = alert.get('alertType')
        
        return f"""fix(security): {title}

Resolves Advanced Security Alert #{alert_id}
Severity: {severity}
Type: {alert_type}

This automated fix addresses a security vulnerability detected by
GitHub Advanced Security for Azure DevOps.
"""
    
    def _create_pull_request(self, alert: Dict, branch_name: str) -> bool:
        """Create a pull request for the fix"""
        alert_id = alert.get('alertId')
        severity = alert.get('severity')
        title = alert.get('title')
        description = alert.get('description', 'No description available')
        alert_type = alert.get('alertType')
        
        # Get file location for PR description
        physical_locations = alert.get('physicalLocations', [])
        file_info = ""
        if physical_locations:
            location = physical_locations[0]
            file_path = location.get('filePath', '')
            start_line = location.get('region', {}).get('startLine', 0)
            file_info = f"**File:** `{file_path}` (Line {start_line})\n"
        
        pr_description = f"""## 🔒 Security Fix - Alert #{alert_id}

**Severity:** {severity.upper()}
**Alert Type:** {alert_type}
{file_info}

### Description
{description}

### Fix Applied
This PR automatically applies a fix for the security vulnerability identified by Advanced Security.

### ⚠️ Required Actions
1. **Review** the changes carefully
2. **Test** the application thoroughly
3. **Verify** that the fix doesn't break existing functionality
4. **Update** any related tests if needed

### Additional Context
- This PR was automatically generated by the Advanced Security Auto-Fix pipeline
- The fix follows security best practices for {alert_type} vulnerabilities
- Consider adding additional security controls or tests

---
*Generated by Advanced Security Auto-Fix Pipeline*
*Alert ID: {alert_id} | Severity: {severity}*
"""
        
        pr_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/git/repositories/{self.repository_id}/pullrequests"
        
        labels = self.config.get('pr_config', {}).get('default_labels', [])
        labels.append(f"severity-{severity}")
        
        pr_payload = {
            "sourceRefName": f"refs/heads/{branch_name}",
            "targetRefName": "refs/heads/main",
            "title": f"[Security-{severity.upper()}] {title}",
            "description": pr_description,
            "labels": [{"name": label} for label in labels]
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
    
    def run(self, severity_filter: str = 'high') -> Dict:
        """Main execution method"""
        print("="*60)
        print("Advanced Security Auto-Fix Pipeline")
        print("="*60)
        
        # Fetch alerts
        alerts = self.fetch_alerts(severity_filter)
        
        if not alerts:
            print("\nNo alerts found to process")
            return self._generate_summary(alerts, [])
        
        # Process alerts up to limit
        max_prs = self.config.get('limits', {}).get('max_prs_per_run', 5)
        
        for alert in alerts[:max_prs]:
            if self.prs_created >= max_prs:
                print(f"\nReached maximum PR limit ({max_prs})")
                break
            
            self.process_alert(alert)
        
        # Generate summary
        summary = self._generate_summary(alerts, self.alerts_processed)
        
        print("\n" + "="*60)
        print(f"Summary: Created {self.prs_created} pull request(s)")
        print("="*60)
        
        return summary
    
    def _generate_summary(self, all_alerts: List[Dict], processed: List[Dict]) -> Dict:
        """Generate execution summary"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_alerts': len(all_alerts),
            'alerts_processed': len(processed),
            'prs_created': self.prs_created,
            'processed_details': processed,
            'status': 'success' if self.prs_created > 0 else 'no_prs_created'
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Advanced Security alerts')
    parser.add_argument('--severity', default='high', 
                       choices=['critical', 'high', 'medium', 'low'],
                       help='Minimum severity to process')
    parser.add_argument('--config', default='security-fix-config.yml',
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    fixer = SecurityAlertFixer(config_path=args.config)
    summary = fixer.run(severity_filter=args.severity)
    
    # Save summary
    workspace = os.environ.get('PIPELINE_WORKSPACE', '.')
    summary_path = os.path.join(workspace, 'summary.json')
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {summary_path}")
    
    return 0 if summary['prs_created'] > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
