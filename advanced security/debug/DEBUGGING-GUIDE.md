# Debugging "Could not extract package information"

If you're seeing "Could not extract package information" and 0 PRs created, follow this guide.

## Quick Diagnosis

The script now includes extensive debugging output. When it runs, you'll see:

```
Processing Alert #12345
  Type: dependency
  Severity: high
  Title: <alert title>
    DEBUG - Full alert structure:
      Title: ...
      Type: ...
      Description: ...
      File: ...
      Code snippet: ...
    ═══ Final extraction result ═══
      Package: NOT FOUND  ← Problem here!
      Current: N/A
      Fixed: NOT FOUND
      CVE: N/A
```

## Common Causes & Solutions

### 1. **Alert is NOT a dependency vulnerability**

**Symptom:**
```
Found 25 total active alerts
Found 0 dependency alerts  ← No dependency alerts found!
```

**Solution:** The alert might be for code issues (XSS, SQL injection, etc.), not packages.

**Check:**
- Go to Advanced Security UI in Azure DevOps
- Look at alert type - should mention "dependency", "package", or "vulnerable package"
- If all alerts are code-related, this is expected behavior

---

### 2. **Alert format not recognized**

**Symptom:**
```
DEBUG - Full alert structure:
  Title: Security vulnerability found
  Description: Some description
  ═══ Final extraction result ═══
  Package: NOT FOUND  ← Can't find package name
```

**Solution:** Alert title/description doesn't match expected patterns.

**Check the alert title format:**
```python
# Supported formats:
"Update requests to fix CVE-2023-XXXX"        ✓
"Vulnerable package: requests"                 ✓  
"requests vulnerability"                       ✓
"`requests` has a security issue"              ✓
"Security issue in requests"                   ✓

# NOT supported:
"Security vulnerability detected"              ✗ (no package name)
"Dependency issue"                             ✗ (too vague)
```

**Fix:** Add custom pattern matching. Edit `dependency_security_fixer.py`:

```python
# Around line 220, add your pattern:
package_patterns = [
    # ... existing patterns ...
    r'your_custom_pattern_here',  # Add this
]
```

---

### 3. **Package name is there but not extracted**

**Symptom:**
```
Title: Vulnerability in flask-cors detected
Package: NOT FOUND  ← Missed it!
```

**Cause:** Package name has hyphens/special characters

**Solution:** The script already handles this, but check line 220:

```python
# This pattern should catch it:
r'\b(requests|django|flask|flask-cors|...)\b'  # Add your package
```

**Workaround:** Add your specific package to the list around line 222.

---

### 4. **No version information in alert**

**Symptom:**
```
Package: requests  ✓
Current: N/A
Fixed: NOT FOUND  ← No version!
```

**Cause:** Alert doesn't specify fix version

**Solutions:**

**A. Check recommendations:**
The script checks alert recommendations automatically. Ensure your alert has them.

**B. Manually specify version:**
If you know the fixed version, you can create a mapping file:

```python
# Create version_overrides.json
{
  "requests": "2.31.0",
  "urllib3": "2.0.4"
}
```

Then modify the script to load this file.

**C. Let script search requirements.txt:**
The script already does this! It will:
1. Find package in your requirements files
2. Use current version from there
3. You just need to know the fixed version

---

## Enable Full Debug Mode

To see the complete alert JSON structure:

### Method 1: Edit Script

```python
# Line 54 in dependency_security_fixer.py
self.debug_mode = True  # Change from False
```

### Method 2: Environment Variable (if added)

```yaml
# In pipeline
env:
  DEBUG_ALERTS: "true"
```

### Method 3: Print Alerts Manually

Add to pipeline before running script:

```yaml
- script: |
    # Get and print alerts for manual inspection
    ALERT_URL="https://advsec.dev.azure.com/$(System.CollectionId)/$(System.TeamProjectId)/_apis/alert/repositories/$(Build.Repository.ID)/alerts?criteria.states=active&api-version=7.2-preview.1"
    
    curl -u ":$(System.AccessToken)" "$ALERT_URL" | python -m json.tool > alerts.json
    
    echo "First alert:"
    cat alerts.json | python -c "import sys, json; print(json.dumps(json.load(sys.stdin)['value'][0], indent=2))"
  displayName: 'Debug: Print First Alert'
```

---

## Understanding Alert Structure

Advanced Security alerts typically look like:

```json
{
  "alertId": 123,
  "alertType": "dependency",
  "title": "Update package-name to fix CVE-XXXX",
  "description": "Package package-name version X.Y.Z has a vulnerability...",
  "severity": "high",
  "physicalLocations": [{
    "filePath": "requirements.txt",
    "region": {
      "startLine": 10,
      "snippet": {
        "text": "package-name==1.2.3"
      }
    }
  }],
  "recommendations": [{
    "text": "Upgrade to version 2.0.0 or later"
  }]
}
```

The script extracts:
- **Package name** from: title, description, snippet
- **Current version** from: snippet, description, requirements files
- **Fixed version** from: recommendations, description
- **CVE** from: anywhere in text

---

## Manual Workaround

If automatic extraction fails, create PRs manually:

```bash
# 1. Identify the package and version from Azure DevOps UI
# 2. Update locally
sed -i 's/requests==2.25.0/requests==2.31.0/' requirements.txt

# 3. Commit and push
git checkout -b security/requests-2.31.0
git add requirements.txt
git commit -m "fix(deps): update requests to 2.31.0"
git push origin security/requests-2.31.0

# 4. Create PR via Azure DevOps UI
```

---

## Test Extraction Locally

Create a test script:

```python
#!/usr/bin/env python3
import json

# Paste your alert JSON here
alert = {
    "title": "Your alert title",
    "description": "Your alert description",
    # ... etc
}

from dependency_security_fixer import DependencySecurityFixer

fixer = DependencySecurityFixer()
fixer.debug_mode = True

result = fixer.extract_package_info(alert)
print(f"\nResult: {result}")
```

Run: `python test_extraction.py`

---

## Report Patterns

If you find a pattern that doesn't work, please note:
1. The alert title format
2. The alert description format  
3. Whether it's from a specific security tool
4. The actual package name

This helps improve the script!

---

## Quick Fixes

### Pattern 1: Title has package name

```
Title: "mycool-package has vulnerability"
```

Add to line 222:
```python
r'\b(mycool-package)\b',
```

### Pattern 2: Description has version

```
Description: "Affects versions before 3.0.0"
```

Already handled! The script looks for "< X.Y.Z" patterns.

### Pattern 3: Recommendation has fix

```
Recommendation: "Update to at least version 3.0.0"
```

Already handled! The script checks recommendations.

---

## Still Not Working?

1. **Check alert type** - Must be dependency-related
2. **Check alert state** - Must be "active"
3. **Check severity filter** - alert severity >= your filter
4. **Enable debug mode** - See full alert JSON
5. **Check requirements files** - Are they in standard locations?
6. **Check file format** - Must be `package==version` or similar

## Need More Help?

Run with maximum verbosity and share the output:

```bash
# Enable all debug output
export DEBUG_ALERTS=true
python dependency_security_fixer.py --severity low --dry-run
```

Look for the "DEBUG - Full alert structure" section and check what's being extracted.
