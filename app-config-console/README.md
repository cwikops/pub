# Azure App Configuration Reader

A Python application that connects to Azure App Configuration using Azure Identity and retrieves configuration settings filtered by app name prefix and optional environment label.

## Requirements

- Python 3.11+
- Azure App Configuration instance
- Azure credentials (via DefaultAzureCredential)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_APP_CONFIG_ENDPOINT` | Yes | Azure App Config endpoint (e.g., `https://your-store.azconfig.io`) |
| `APP_NAME` | Yes | Prefix to filter keys (retrieves keys matching `{APP_NAME}/*`) |
| `ENVIRONMENT` | No | Label filter (e.g., `dev`, `staging`, `prod`). If not set, retrieves all labels. |

## Local Development

### Using uv

```bash
# Install dependencies
uv sync

# Run the application
AZURE_APP_CONFIG_ENDPOINT=https://your-store.azconfig.io \
APP_NAME=myapp \
ENVIRONMENT=dev \
uv run python azure_app_config.py
```

### Using pip

```bash
pip install azure-identity azure-appconfiguration

AZURE_APP_CONFIG_ENDPOINT=https://your-store.azconfig.io \
APP_NAME=myapp \
ENVIRONMENT=dev \
python azure_app_config.py
```

## Docker

### Build

```bash
docker build -t azure-app-config-reader .
```

### Run

```bash
docker run --rm \
  -e AZURE_APP_CONFIG_ENDPOINT=https://your-store.azconfig.io \
  -e APP_NAME=myapp \
  -e ENVIRONMENT=dev \
  -e AZURE_CLIENT_ID=<your-client-id> \
  -e AZURE_CLIENT_SECRET=<your-client-secret> \
  -e AZURE_TENANT_ID=<your-tenant-id> \
  azure-app-config-reader
```

### Authentication Options

The app uses `DefaultAzureCredential`, which tries multiple authentication methods in order:

1. **Environment variables** - Set `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
2. **Managed Identity** - Works automatically in Azure (App Service, AKS, VMs)
3. **Azure CLI** - Uses `az login` credentials (for local development)
4. **Visual Studio Code** - Uses VS Code Azure extension credentials

## Example Output

```
============================================================
Azure App Configuration Settings
App Name Prefix: myapp
Environment/Label: dev
============================================================

Found 3 setting(s):

Key: myapp/database/connection-string
  Value: Server=localhost;Database=mydb
  Label: dev
  Content-Type: (none)
  Last Modified: 2024-01-15 10:30:00
----------------------------------------
Key: myapp/feature/enable-cache
  Value: true
  Label: dev
  Content-Type: (none)
  Last Modified: 2024-01-15 10:30:00
----------------------------------------
```
