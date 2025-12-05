"""
Azure App Configuration Web Reader

A simple Flask web application that connects to Azure App Configuration
and displays configuration settings filtered by app name and environment.
"""

import os
from flask import Flask, render_template_string
from azure.identity import DefaultAzureCredential
from azure.appconfiguration import AzureAppConfigurationClient

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azure App Config Reader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0f1a;
            color: #f8fafc;
            padding: 2rem;
            min-height: 100vh;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 {
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
            color: #50e6ff;
        }
        .subtitle {
            color: #94a3b8;
            margin-bottom: 2rem;
        }
        .info-bar {
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: #1a2332;
            border-radius: 8px;
            border: 1px solid rgba(80, 230, 255, 0.15);
        }
        .info-item label {
            font-size: 0.75rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .info-item span {
            display: block;
            font-family: 'Courier New', monospace;
            color: #50e6ff;
        }
        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .count {
            color: #94a3b8;
            margin-bottom: 1rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #1a2332;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid rgba(80, 230, 255, 0.15);
        }
        th {
            text-align: left;
            padding: 1rem;
            background: #111827;
            color: #94a3b8;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        td {
            padding: 1rem;
            border-top: 1px solid rgba(80, 230, 255, 0.1);
            vertical-align: top;
        }
        .key {
            font-family: 'Courier New', monospace;
            color: #50e6ff;
            word-break: break-all;
        }
        .value {
            font-family: 'Courier New', monospace;
            color: #4ade80;
            word-break: break-all;
        }
        .label {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            background: rgba(80, 230, 255, 0.1);
            border-radius: 4px;
            font-size: 0.85rem;
            color: #94a3b8;
        }
        .empty {
            text-align: center;
            padding: 3rem;
            color: #64748b;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Azure App Config Reader</h1>
        <p class="subtitle">Configuration settings from Azure App Configuration</p>
        
        <div class="info-bar">
            <div class="info-item">
                <label>Endpoint</label>
                <span>{{ endpoint or 'Not set' }}</span>
            </div>
            <div class="info-item">
                <label>App Name</label>
                <span>{{ app_name or 'Not set' }}</span>
            </div>
            <div class="info-item">
                <label>Environment</label>
                <span>{{ environment or 'All' }}</span>
            </div>
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if settings %}
        <p class="count">Found {{ settings|length }} setting(s)</p>
        <table>
            <thead>
                <tr>
                    <th>Key</th>
                    <th>Value</th>
                    <th>Label</th>
                </tr>
            </thead>
            <tbody>
                {% for setting in settings %}
                <tr>
                    <td class="key">{{ setting.key }}</td>
                    <td class="value">{{ setting.value }}</td>
                    <td><span class="label">{{ setting.label or '(none)' }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% elif not error %}
        <div class="empty">No configuration settings found.</div>
        {% endif %}
    </div>
</body>
</html>
"""


def get_app_config_client(endpoint: str) -> AzureAppConfigurationClient:
    """Create an Azure App Configuration client using DefaultAzureCredential."""
    credential = DefaultAzureCredential()
    return AzureAppConfigurationClient(base_url=endpoint, credential=credential)


def get_config_settings(endpoint: str, app_name: str, environment: str | None = None) -> list[dict]:
    """Retrieve configuration settings for keys starting with app_name."""
    client = get_app_config_client(endpoint)
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
        })
    
    return settings


@app.route("/")
def index():
    endpoint = os.getenv("AZURE_APP_CONFIG_ENDPOINT")
    app_name = os.getenv("APP_NAME")
    environment = os.getenv("ENVIRONMENT")
    
    error = None
    settings = []
    
    if not endpoint:
        error = "AZURE_APP_CONFIG_ENDPOINT environment variable is not set."
    elif not app_name:
        error = "APP_NAME environment variable is not set."
    else:
        try:
            settings = get_config_settings(endpoint, app_name, environment)
        except Exception as e:
            error = f"Error connecting to Azure App Configuration: {e}"
    
    return render_template_string(
        HTML_TEMPLATE,
        endpoint=endpoint,
        app_name=app_name,
        environment=environment,
        settings=settings,
        error=error,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
