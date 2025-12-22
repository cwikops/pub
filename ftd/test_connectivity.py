#!/usr/bin/env python3
"""
Test script for FTD connectivity validation
Tests connection to FTD without performing restart
"""

import requests
import urllib3
import sys
import os
from typing import Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_ftd_connectivity(host: str, username: str, password: str) -> bool:
    """
    Test connectivity and authentication to FTD
    
    Returns:
        True if connection successful
    """
    base_url = f"https://{host}/api/fdm/latest"
    
    print(f"Testing connectivity to FTD at {host}...")
    print("-" * 60)
    
    # Test 1: Basic HTTPS connectivity
    print("\n[Test 1] Testing HTTPS connectivity...")
    try:
        response = requests.get(
            f"{base_url}/fdm/token",
            verify=False,
            timeout=10
        )
        print(f"✓ FTD is reachable (HTTP {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot reach FTD: {str(e)}")
        return False
    
    # Test 2: Authentication
    print("\n[Test 2] Testing authentication...")
    try:
        auth_url = f"{base_url}/fdm/token"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "grant_type": "password",
            "username": username,
            "password": password
        }
        
        response = requests.post(
            auth_url,
            json=payload,
            headers=headers,
            verify=False,
            timeout=30
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"✓ Authentication successful")
            print(f"  Token expires in: {token_data.get('expires_in', 'N/A')} seconds")
            
            # Test 3: API call with token
            print("\n[Test 3] Testing authenticated API call...")
            info_url = f"{base_url}/devicesettings/default/devicehostnames"
            info_headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            response = requests.get(
                info_url,
                headers=info_headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                device_info = response.json()
                print(f"✓ API call successful")
                print(f"  Device hostname: {device_info.get('hostname', 'N/A')}")
                return True
            else:
                print(f"✗ API call failed: HTTP {response.status_code}")
                return False
        else:
            print(f"✗ Authentication failed: HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request error: {str(e)}")
        return False


def main():
    """Main test execution"""
    print("=" * 60)
    print("FTD Connectivity Test Script")
    print("=" * 60)
    
    # Get credentials from environment or prompt
    ftd_host = os.environ.get("FTD_HOST")
    ftd_username = os.environ.get("FTD_USERNAME")
    ftd_password = os.environ.get("FTD_PASSWORD")
    
    if not ftd_host:
        ftd_host = input("FTD Host (IP or FQDN): ")
    if not ftd_username:
        ftd_username = input("FTD Username: ")
    if not ftd_password:
        import getpass
        ftd_password = getpass.getpass("FTD Password: ")
    
    if not all([ftd_host, ftd_username, ftd_password]):
        print("Error: Missing required credentials")
        sys.exit(1)
    
    # Run tests
    success = test_ftd_connectivity(ftd_host, ftd_username, ftd_password)
    
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed - FTD is ready for automation")
        print("=" * 60)
        sys.exit(0)
    else:
        print("✗ Tests failed - Please review errors above")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
