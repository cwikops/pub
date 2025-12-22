#!/usr/bin/env python3
"""
Cisco FTD Restart Automation Script
Restarts Cisco FTD device using FDM API with credentials from Azure Key Vault
"""

import requests
import urllib3
import time
import sys
import os
import json
from datetime import datetime

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration from environment variables
FTD_HOST = os.getenv('FTD_HOST')
FTD_USERNAME = os.getenv('FTD_USERNAME')
FTD_PASSWORD = os.getenv('FTD_PASSWORD')
RESTART_MODE = os.getenv('RESTART_MODE', 'GRACEFUL')  # GRACEFUL or FORCED

# Validation
REQUIRED_VARS = ['FTD_HOST', 'FTD_USERNAME', 'FTD_PASSWORD']
missing_vars = [var for var in REQUIRED_VARS if not os.getenv(var)]

if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
    sys.exit(1)

class FTDRestarter:
    """Handle FTD restart operations via FDM API"""
    
    def __init__(self, host, username, password, restart_mode='GRACEFUL'):
        self.host = host
        self.username = username
        self.password = password
        self.restart_mode = restart_mode
        self.token = None
        self.base_url = f"https://{self.host}/api/fdm/latest"
        
    def log(self, message, level="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def get_token(self):
        """Authenticate to FTD and obtain access token"""
        url = f"{self.base_url}/fdm/token"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password
        }
        
        try:
            self.log(f"Authenticating to FTD at {self.host}...")
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.log("Authentication successful")
                return True
            else:
                self.log(f"Authentication failed: HTTP {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"Authentication request failed: {str(e)}", "ERROR")
            return False
    
    def get_device_info(self):
        """Get FTD device information"""
        if not self.token:
            self.log("No authentication token available", "ERROR")
            return None
        
        url = f"{self.base_url}/devicesettings/default/devicehostnames"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        
        try:
            self.log("Retrieving device information...")
            response = requests.get(
                url,
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                device_info = response.json()
                hostname = device_info.get('items', [{}])[0].get('hostname', 'Unknown')
                self.log(f"Device hostname: {hostname}")
                return device_info
            else:
                self.log(f"Failed to get device info: HTTP {response.status_code}", "WARNING")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"Failed to retrieve device info: {str(e)}", "WARNING")
            return None
    
    def restart_device(self):
        """Restart FTD device"""
        if not self.token:
            self.log("No authentication token available", "ERROR")
            return False
        
        url = f"{self.base_url}/action/reboot"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "type": "reboot",
            "mode": self.restart_mode
        }
        
        try:
            self.log(f"Initiating {self.restart_mode} restart of FTD device...")
            self.log("WARNING: Network traffic will be interrupted during restart")
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code in [200, 202, 204]:
                self.log("FTD restart initiated successfully", "SUCCESS")
                self.log("Device will reboot and be unavailable for 10-15 minutes")
                return True
            else:
                self.log(f"Failed to restart FTD: HTTP {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"Restart request failed: {str(e)}", "ERROR")
            return False
    
    def verify_connectivity(self):
        """Verify FTD is reachable"""
        url = f"https://{self.host}"
        
        try:
            self.log("Verifying FTD connectivity...")
            response = requests.get(
                url,
                verify=False,
                timeout=10
            )
            self.log("FTD is reachable")
            return True
        except requests.exceptions.RequestException as e:
            self.log(f"FTD is not reachable: {str(e)}", "ERROR")
            return False

def main():
    """Main execution function"""
    print("=" * 70)
    print("Cisco FTD Restart Automation")
    print("=" * 70)
    
    # Initialize restarter
    restarter = FTDRestarter(
        host=FTD_HOST,
        username=FTD_USERNAME,
        password=FTD_PASSWORD,
        restart_mode=RESTART_MODE
    )
    
    # Step 1: Verify connectivity
    if not restarter.verify_connectivity():
        print("\nERROR: Cannot reach FTD device")
        sys.exit(1)
    
    # Step 2: Authenticate
    if not restarter.get_token():
        print("\nERROR: Authentication failed")
        sys.exit(1)
    
    # Step 3: Get device info (optional)
    restarter.get_device_info()
    
    # Step 4: Restart device
    if not restarter.restart_device():
        print("\nERROR: Failed to restart FTD device")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("FTD Restart Process Completed Successfully")
    print("=" * 70)
    print("\nIMPORTANT NOTES:")
    print("- FTD device is rebooting and will be unavailable")
    print("- Expected downtime: 10-15 minutes")
    print("- Network traffic through FTD will be interrupted")
    print("- Monitor FTD availability and verify services after restart")
    
    if RESTART_MODE == "FORCED":
        print("- FORCED restart was used - configuration may not have been saved")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
