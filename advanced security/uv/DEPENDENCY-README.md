# Dependency Security Auto-Fix Pipeline (with uv)

Automatically updates vulnerable Python dependencies in `requirements.txt` and `pyproject.toml` files using **uv** - the fast, modern Python package manager.

## What It Does

1. **Scans** for dependency vulnerability alerts from Advanced Security
2. **Identifies** the vulnerable package and recommended fix version
3. **Updates** all `requirements.txt` and `pyproject.toml` files in your repository
4. **Validates** changes with `uv pip compile`
5. **Generates lockfiles** (`requirements.lock` or `uv.lock`)
6. **Creates** a pull request for each vulnerable dependency
7. **Documents** CVEs, severity levels, and changes

## Features

✅ **Uses uv** - Fast, reliable Python package management  
✅ **Lockfile Generation** - Automatically creates `.lock` files  
✅ **Dependency Validation** - Validates updates with `uv pip compile`  
✅ **Focused on Dependencies** - Only processes package/dependency alerts  
✅ **Smart Package Detection** - Finds all requirements*.txt and pyproject.toml files  
✅ **Version Extraction** - Parses alerts to get current and fixed versions  
✅ **Multiple Files** - Updates all requirements files (base, dev, prod, etc.)  
✅ **CVE Tracking** - Extracts and documents CVE identifiers  
✅ **Dry Run Mode** - Test without creating PRs  
✅ **Batch Processing** - Handle multiple vulnerabilities at once  

## Why uv?

[uv](https://github.com/astral-sh/uv) is 10-100x faster than pip and provides:
- **Fast dependency resolution** - Written in Rust
- **Reliable lockfiles** - Consistent across environments  
- **Better error messages** - Clear feedback on conflicts
- **Dependency validation** - Catch issues before deployment  

## Quick Start

### 1. Add Files to Repository

```
your-repo/
├── dependency_security_fixer.py
├── dependency-security-pipeline.yml
├── requirements.txt  # Your existing file(s)
└── pyproject.toml    # Optional, for uv projects
```

### 2. Install uv (Optional for Local Testing)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

Pipeline automatically installs uv - no manual setup needed!

### 3. Enable Advanced Security

```
Repository Settings → Security → Advanced Security
→ Enable "GitHub Advanced Security"
→ Wait for initial scan (5-10 minutes)
```

### 3. Grant Permissions

```
Project Settings → Repositories → [Your Repo] → Security
→ Add "[Project Name] Build Service"
→ Allow: Contribute, Create branch, Contribute to pull requests
```

### 4. Create Pipeline

1. **Pipelines** → **New Pipeline**
2. **Azure Repos Git** → Select your repository
3. **Existing YAML file** → `dependency-security-pipeline.yml`
4. **Save** or **Run**

## Usage

### Run Manually

```
Pipelines → [Your Pipeline] → Run Pipeline

Parameters:
- Severity Filter: critical | high | medium | low
- Max PRs: Number of PRs to create (default: 10)
- Dry Run: Test without creating PRs
```

### Scheduled Run

Pipeline runs daily at 2 AM by default. Customize in YAML:

```yaml
schedules:
- cron: "0 14 * * *"  # 2 PM UTC
  displayName: Afternoon dependency check
  branches:
    include:
    - main
```

### Command Line (Manual Testing)

```bash
# Set environment variables (from Azure DevOps pipeline context)
export SYSTEM_COLLECTIONURI="https://dev.azure.com/yourorg/"
export SYSTEM_TEAMPROJECT="YourProject"
export BUILD_REPOSITORY_ID="repo-guid"
export BUILD_REPOSITORY_NAME="your-repo"
export SYSTEM_ACCESSTOKEN="your-pat"

# Run
python dependency_security_fixer.py --severity high --dry-run

# Options:
#   --severity {critical,high,medium,low}  (default: high)
#   --max-prs N                            (default: 10)
#   --dry-run                              (test mode)
```

## How It Works

### 1. Alert Detection

The script filters for dependency-related alerts by checking for keywords:
- `dependency`
- `package`
- `pip`
- `vulnerable`
- `cve`

### 2. Package Information Extraction

From alert title and description, extracts:
```python
{
  'package_name': 'requests',
  'current_version': '2.25.0',
  'fixed_version': '2.31.0',
  'cve': 'CVE-2023-32681'
}
```

### 3. Requirements File Discovery

Searches for:
- `requirements.txt` (root)
- `requirements/*.txt`
- `pyproject.toml` (for uv projects)
- Any `requirements*.txt` files

Ignores:
- `.git/`, `node_modules/`, `venv/`, `.venv/`, `.uv/`

### 4. Version Update with uv

```python
# Before (requirements.txt)
requests==2.25.0

# After
requests==2.31.0

# uv validates the change
uv pip compile requirements.txt --quiet

# uv generates lockfile
uv pip compile requirements.txt -o requirements.lock
```

For `pyproject.toml`:
```toml
# Before
dependencies = ["requests>=2.25.0"]

# After  
dependencies = ["requests==2.31.0"]

# uv generates uv.lock
uv lock
```

### 5. Lockfile Generation

Automatically creates lockfiles for reproducible builds:
- `requirements.lock` for requirements.txt
- `uv.lock` for pyproject.toml

### 6. Pull Request Creation

Creates a PR with:
- **Title**: `[Security] Update {package} to {version}`
- **Description**: CVE details, files changed, testing recommendations
- **Labels**: `security`, `dependencies`, `severity-{level}`

## Example Output

### Pipeline Run

```
════════════════════════════════════════════════════════════
Dependency Security Auto-Fix Pipeline
════════════════════════════════════════════════════════════
Fetching dependency alerts for repository: my-app
Found 25 total active alerts
Found 8 dependency alerts
Found 5 dependency alerts matching severity: high

════════════════════════════════════════════════════════════
Processing Alert #12345
  Type: dependency
  Severity: high
  Title: Update requests to fix CVE-2023-32681
  Package: requests
  Current Version: 2.25.0
  Fixed Version: 2.31.0
  CVE: CVE-2023-32681
  Found 2 requirements file(s): requirements.txt, requirements/dev.txt
    Updated: requests==2.25.0 -> requests==2.31.0
    Validating with uv...
    ✓ Requirements validated with uv
  Updated 2 file(s): requirements.txt, requirements/dev.txt
    Generating lockfile with uv...
    ✓ Generated requirements.lock
  ✓ Created PR #456

════════════════════════════════════════════════════════════
Summary: Created 5 pull request(s)
════════════════════════════════════════════════════════════
```

### Pull Request

```markdown
## 🔒 Security: Update requests

**Alert ID:** #12345
**Severity:** HIGH
**CVE:** CVE-2023-32681

### Vulnerability Details
The requests library versions < 2.31.0 are vulnerable to CRLF injection...

### Changes
- **Package:** `requests`
- **Current Version:** `2.25.0`
- **Fixed Version:** `2.31.0`

### Files Updated
- `requirements.txt`
- `requirements/dev.txt`
- `requirements.lock` (generated by uv)

### Testing Recommendations
1. Run your test suite to ensure compatibility
2. Check for breaking changes in package changelog
3. Verify application functionality
4. Review lockfile changes
```

## Supported Alert Formats

The script can parse these alert patterns:

```
# Pattern 1: Direct package mention
"Vulnerable package: requests (CVE-2023-XXXX)"

# Pattern 2: Version upgrade
"Update requests from 2.25.0 to 2.31.0"

# Pattern 3: In description
Description: "The package `flask` version 1.0.0 is vulnerable..."

# Pattern 4: From recommendations
Recommendation: "Upgrade to version 2.31.0 or later"
```

## Configuration

### Adjust Limits

Edit in script or pass as arguments:

```python
# In dependency_security_fixer.py
self.max_prs_per_run = 10  # Max PRs per run
self.branch_prefix = "security/dependency-update"  # Branch naming
```

Or via command line:
```bash
python dependency_security_fixer.py --max-prs 20
```

### Target Different Branches

```yaml
# In pipeline YAML
pr_payload = {
  "targetRefName": "refs/heads/develop"  # Instead of main
}
```

### Custom Requirements Paths

The script auto-discovers files, but you can customize:

```python
def find_requirements_files(self) -> List[str]:
    # Add your custom paths
    custom_files = [
        'path/to/custom-requirements.txt',
        'docker/requirements.txt'
    ]
    # ... rest of discovery logic
```

## Troubleshooting

### No Dependency Alerts Found

1. **Check Advanced Security is enabled**
   ```
   Repository → Settings → Advanced Security
   ```

2. **Verify alerts exist**
   ```
   Repos → [Your Repo] → Advanced Security → Alerts
   ```

3. **Check alert types**
   - Script only processes dependency-related alerts
   - Other alert types (XSS, SQL injection, etc.) are ignored

### Package Not Found in Requirements

```
Package requests not found in any requirements file
```

**Causes:**
- Package name mismatch (case-sensitive)
- Package in different file (e.g., `setup.py`, `pyproject.toml`)
- Package pinned in different format

**Solutions:**
1. Check actual package name in requirements
2. Script only updates `.txt` files
3. Manually add package if missing

### Could Not Extract Package Information

```
Could not extract package information
```

**Causes:**
- Alert format not recognized
- Missing version information
- Complex alert description

**Solutions:**
1. Check alert in UI for format
2. Add custom parsing pattern
3. Update manually

### Version Extraction Failed

```
No fixed version available, skipping
```

**Cause:** Script couldn't parse recommended version from alert

**Solution:** Check alert recommendations in UI and update manually

## Advanced Features

### uv Integration Benefits

**Speed:**
- 10-100x faster than traditional pip
- Parallel dependency resolution
- Cached package installations

**Reliability:**
- Lockfiles ensure reproducible builds
- Better conflict detection
- Clear error messages

**Validation:**
```bash
# Automatically validates updates
uv pip compile requirements.txt --quiet

# Generates lockfile for reproducibility  
uv pip compile requirements.txt -o requirements.lock
```

### Multiple Requirements Files

Automatically updates all matching files:

```
requirements.txt              → Updated
requirements/base.txt        → Updated
requirements/production.txt  → Updated
requirements/dev.txt         → Updated
requirements/test.txt        → Updated
```

### CVE Documentation

Automatically extracts and documents CVEs:

```python
# From alert text
"... CVE-2023-32681 ..."

# Becomes PR link
[CVE Details](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-32681)
```

### Batch Processing

Processes multiple alerts in one run:

```bash
# Process up to 20 vulnerabilities
python dependency_security_fixer.py --max-prs 20
```

### Dry Run Testing

Test without making changes:

```bash
python dependency_security_fixer.py --dry-run

# Output:
[DRY RUN] Would create branch: security/dependency-update/requests-2.31.0
[DRY RUN] Would update requests to 2.31.0
[DRY RUN] Would create PR: Update requests to 2.31.0
```

## Best Practices

1. **Start with Dry Run** - Test first with `--dry-run`
2. **Review PRs Carefully** - Version updates can break compatibility
3. **Test Updated Dependencies** - Run test suite after updates
4. **Check Changelogs** - Review breaking changes in new versions
5. **Merge Promptly** - Security fixes should be prioritized
6. **Monitor Pipeline** - Check daily run results
7. **Update Regularly** - Don't let vulnerabilities accumulate

## Limitations

- **Python Focused** - Currently supports Python packages only (pip/uv)
- **Simple Formats** - Best with standard `package==version` format
- **Alert Parsing** - May not parse all alert formats correctly
- **No Testing** - Doesn't automatically test updated dependencies
- **Main Branch Only** - Creates PRs targeting `main` branch
- **uv Optional** - Works with or without uv (but uv is recommended)

## Future Enhancements

Potential improvements:

- [ ] Support for `setup.py`, `pyproject.toml`, `Pipfile`
- [ ] Support for npm `package.json`, `package-lock.json`
- [ ] Automatic test execution after update
- [ ] Rollback on test failures
- [ ] Group related updates in single PR
- [ ] Check package compatibility matrix
- [ ] Auto-merge for patch versions

## FAQ

**Q: Does this work with other package managers?**  
A: Currently Python/pip only. npm, Maven, NuGet support could be added.

**Q: Will it break my application?**  
A: Possibly. Always review PRs and test thoroughly before merging.

**Q: Can I exclude certain packages?**  
A: Not currently, but you can add exclusion logic in `process_dependency_alert()`.

**Q: What if the fixed version has breaking changes?**  
A: The PR will be created. You must review and decide whether to merge.

**Q: Does it handle transitive dependencies?**  
A: Only if they're explicitly listed in requirements.txt.

**Q: Can I run this locally?**  
A: Yes, but you need Azure DevOps PAT and environment variables set.

## Support

For issues:
1. Check pipeline logs for detailed error messages
2. Verify Advanced Security is enabled and scanning
3. Check permissions for build service
4. Review TROUBLESHOOTING.md

## License

Provided as-is for use in your Azure DevOps environment.
