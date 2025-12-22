#!/usr/bin/env python3
"""
FTD Pre-Restart Validation Script
Tests connectivity and credentials before executing restart
"""

import requests
import urllib3
import sys
import os
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FTD_HOST = os.getenv('FTD_HOST')
FTD_USERNAME = os.getenv('FTD_USERNAME')
FTD_PASSWORD = os.getenv('FTD_PASSWORD')

class FTDValidator:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.base_url = f"https://{self.host}/api/fdm/latest"
        self.token = None
        self.validation_results = {
            'connectivity': False,
            'authentication': False,
            'api_access': False,
            'device_info': None
        }
    
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }
        print(f"[{timestamp}] {symbols.get(status, '')} {message}")
    
    def test_connectivity(self):
        """Test basic HTTPS connectivity to FTD"""
        try:
            self.log("Testing connectivity to FTD...")
            response = requests.get(
                f"https://{self.host}",
                verify=False,
                timeout=10
            )
            self.validation_results['connectivity'] = True
            self.log(f"FTD is reachable at {self.host}", "SUCCESS")
            return True
        except requests.exceptions.Timeout:
            self.log(f"Connection timeout to {self.host}", "ERROR")
            return False
        except requests.exceptions.ConnectionError as e:
            self.log(f"Connection error: {str(e)}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Connectivity test failed: {str(e)}", "ERROR")
            return False
    
    def test_authentication(self):
        """Test FTD API authentication"""
        try:
            self.log("Testing authentication...")
            url = f"{self.base_url}/fdm/token"
            
            payload = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password
            }
            
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.validation_results['authentication'] = True
                self.log("Authentication successful", "SUCCESS")
                return True
            else:
                self.log(f"Authentication failed: HTTP {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Authentication test failed: {str(e)}", "ERROR")
            return False
    
    def test_api_access(self):
        """Test API access and retrieve device info"""
        if not self.token:
            self.log("No authentication token available", "ERROR")
            return False
        
        try:
            self.log("Testing API access...")
            
            # Get device hostname
            url = f"{self.base_url}/devicesettings/default/devicehostnames"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.get(
                url,
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                device_info = response.json()
                hostname = device_info.get('items', [{}])[0].get('hostname', 'Unknown')
                
                self.validation_results['api_access'] = True
                self.validation_results['device_info'] = {
                    'hostname': hostname,
                    'management_ip': self.host
                }
                
                self.log("API access verified", "SUCCESS")
                self.log(f"Device hostname: {hostname}", "INFO")
                return True
            else:
                self.log(f"API access failed: HTTP {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"API access test failed: {str(e)}", "ERROR")
            return False
    
    def get_system_info(self):
        """Retrieve additional system information"""
        if not self.token:
            return None
        
        try:
            self.log("Retrieving system information...")
            
            # Get system version
            url = f"{self.base_url}/devicesettings/default/systemversions"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.get(
                url,
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                version_info = response.json()
                version = version_info.get('items', [{}])[0].get('version', 'Unknown')
                self.log(f"FTD Version: {version}", "INFO")
                return version_info
            
        except Exception as e:
            self.log(f"Could not retrieve system info: {str(e)}", "WARNING")
        
        return None
    
    def check_pending_changes(self):
        """Check if there are pending deployments"""
        if not self.token:
            return None
        
        try:
            self.log("Checking for pending changes...")
            
            url = f"{self.base_url}/operational/deploy"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.get(
                url,
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                deploy_status = response.json()
                pending = deploy_status.get('pendingChanges', False)
                
                if pending:
                    self.log("WARNING: Pending configuration changes detected", "WARNING")
                    self.log("Changes may be lost if restart is FORCED", "WARNING")
                else:
                    self.log("No pending configuration changes", "INFO")
                
                return pending
            
        except Exception as e:
            self.log(f"Could not check pending changes: {str(e)}", "WARNING")
        
        return None
    
    def run_validation(self):
        """Run complete validation suite"""
        self.log("=" * 70)
        self.log("FTD Pre-Restart Validation")
        self.log("=" * 70)
        self.log(f"Target: {self.host}")
        self.log("")
        
        # Test 1: Connectivity
        if not self.test_connectivity():
            self.print_summary()
            return False
        
        # Test 2: Authentication
        if not self.test_authentication():
            self.print_summary()
            return False
        
        # Test 3: API Access
        if not self.test_api_access():
            self.print_summary()
            return False
        
        # Additional checks
        self.get_system_info()
        self.check_pending_changes()
        
        self.print_summary()
        return True
    
    def print_summary(self):
        """Print validation summary"""
        self.log("")
        self.log("=" * 70)
        self.log("Validation Summary")
        self.log("=" * 70)
        
        results = self.validation_results
        
        print(f"Connectivity:     {'✅ PASS' if results['connectivity'] else '❌ FAIL'}")
        print(f"Authentication:   {'✅ PASS' if results['authentication'] else '❌ FAIL'}")
        print(f"API Access:       {'✅ PASS' if results['api_access'] else '❌ FAIL'}")
        
        if results['device_info']:
            print(f"\nDevice Information:")
            print(f"  Hostname: {results['device_info']['hostname']}")
            print(f"  Management IP: {results['device_info']['management_ip']}")
        
        all_passed = all([
            results['connectivity'],
            results['authentication'],
            results['api_access']
        ])
        
        self.log("")
        if all_passed:
            self.log("✅ All validation checks PASSED", "SUCCESS")
            self.log("FTD is ready for restart", "SUCCESS")
        else:
            self.log("❌ Validation checks FAILED", "ERROR")
            self.log("Do NOT proceed with restart", "ERROR")
        
        self.log("=" * 70)

def main():
    # Validate environment variables
    if not all([FTD_HOST, FTD_USERNAME, FTD_PASSWORD]):
        print("ERROR: Missing required environment variables", file=sys.stderr)
        print("Required: FTD_HOST, FTD_USERNAME, FTD_PASSWORD", file=sys.stderr)
        sys.exit(1)
    
    # Run validation
    validator = FTDValidator(FTD_HOST, FTD_USERNAME, FTD_PASSWORD)
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
