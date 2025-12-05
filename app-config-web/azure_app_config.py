"""
Azure App Configuration Reader

Connects to Azure App Configuration using Azure Identity (DefaultAzureCredential)
and retrieves all configuration keys starting with a specified app name prefix.
Supports filtering by environment labels.
"""

import os
import sys
from azure.identity import DefaultAzureCredential
from azure.appconfiguration import AzureAppConfigurationClient


def get_app_config_client(endpoint: str) -> AzureAppConfigurationClient:
    """Create an Azure App Configuration client using DefaultAzureCredential."""
    credential = DefaultAzureCredential()
    return AzureAppConfigurationClient(base_url=endpoint, credential=credential)


def get_config_settings(
    client: AzureAppConfigurationClient,
    app_name: str,
    environment: str | None = None,
) -> list[dict]:
    """
    Retrieve configuration settings for keys starting with app_name.
    
    Args:
        client: Azure App Configuration client
        app_name: Prefix to filter keys (e.g., 'myapp')
        environment: Optional label filter (e.g., 'dev', 'staging', 'prod')
    
    Returns:
        List of configuration settings as dictionaries
    """
    key_filter = f"{app_name}/*"
    label_filter = environment if environment else "*"
    
    settings = []
    for setting in client.list_configuration_settings(
        key_filter=key_filter,
        label_filter=label_filter,
    ):
        settings.append({
            "key": setting.key,
            "value": setting.value,
            "label": setting.label,
            "content_type": setting.content_type,
            "last_modified": str(setting.last_modified) if setting.last_modified else None,
            "etag": setting.etag,
        })
    
    return settings


def print_settings(settings: list[dict], app_name: str, environment: str | None) -> None:
    """Print configuration settings in a formatted way."""
    env_display = environment if environment else "all"
    print(f"\n{'='*60}")
    print(f"Azure App Configuration Settings")
    print(f"App Name Prefix: {app_name}")
    print(f"Environment/Label: {env_display}")
    print(f"{'='*60}\n")
    
    if not settings:
        print("No configuration settings found.")
        return
    
    print(f"Found {len(settings)} setting(s):\n")
    
    for setting in settings:
        print(f"Key: {setting['key']}")
        print(f"  Value: {setting['value']}")
        print(f"  Label: {setting['label'] or '(none)'}")
        print(f"  Content-Type: {setting['content_type'] or '(none)'}")
        print(f"  Last Modified: {setting['last_modified'] or 'N/A'}")
        print("-" * 40)


def main() -> None:
    """Main entry point."""
    endpoint = os.getenv("AZURE_APP_CONFIG_ENDPOINT")
    app_name = os.getenv("APP_NAME")
    environment = os.getenv("ENVIRONMENT")
    
    if not endpoint:
        print("Error: AZURE_APP_CONFIG_ENDPOINT environment variable is required.")
        print("Example: https://your-config-store.azconfig.io")
        sys.exit(1)
    
    if not app_name:
        print("Error: APP_NAME environment variable is required.")
        print("This is used to filter keys starting with: {app_name}/*")
        sys.exit(1)
    
    try:
        client = get_app_config_client(endpoint)
        settings = get_config_settings(client, app_name, environment)
        print_settings(settings, app_name, environment)
    except Exception as e:
        print(f"Error connecting to Azure App Configuration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
