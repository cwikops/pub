# Azure App Configuration Web Reader

A simple Flask web application that connects to Azure App Configuration and displays configuration settings filtered by app name prefix and optional environment label.

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

# Run the web app
AZURE_APP_CONFIG_ENDPOINT=https://your-store.azconfig.io \
APP_NAME=myapp \
ENVIRONMENT=dev \
uv run python app.py
```

Then open http://localhost:8080 in your browser.

## Docker

### Build

```bash
docker build -t azure-app-config-reader .
```

### Run

```bash
docker run --rm -p 8080:8080 \
  -e AZURE_APP_CONFIG_ENDPOINT=https://your-store.azconfig.io \
  -e APP_NAME=myapp \
  -e ENVIRONMENT=dev \
  -e AZURE_CLIENT_ID=<your-client-id> \
  -e AZURE_CLIENT_SECRET=<your-client-secret> \
  -e AZURE_TENANT_ID=<your-tenant-id> \
  azure-app-config-reader
```

Then open http://localhost:8080 in your browser.

### Authentication Options

The app uses `DefaultAzureCredential`, which tries multiple authentication methods in order:

1. **Environment variables** - Set `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
2. **Managed Identity** - Works automatically in Azure (App Service, AKS, VMs)
3. **Azure CLI** - Uses `az login` credentials (for local development)
