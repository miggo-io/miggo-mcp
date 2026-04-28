# Miggo MCP Server

> **Ask your AI assistant about your live application security — vulnerabilities, services, endpoints, findings, dependencies, and third-party integrations — all through natural language.**

Miggo's MCP server connects Claude, Cursor, VS Code Copilot, and other AI assistants directly to your [Miggo](https://miggo.io) environment. Instead of clicking through dashboards, just ask questions and get answers grounded in real-time data from your running applications.

<!-- TODO: Add a short demo video here
[![Watch the demo](https://img.shields.io/badge/▶_Watch_Demo-blue)](https://your-video-link)
-->

---

## Quick start

### 1. Get your API token

Create an API token in the [Miggo Integrations portal](https://app.miggo.io/integrations/accessKey).

### 2. Install

<details>
<summary><strong>Claude Desktop (one-click MCPB)</strong></summary>

1. Download the latest `.mcpb` from the [releases page](https://github.com/miggo-io/miggo-mcp/releases)
2. Open the file — Claude Desktop installs it automatically
3. Enter your API token when prompted

Claude Desktop ships its own [`uv`](https://docs.astral.sh/uv/) and provisions the Python runtime from the bundle's `pyproject.toml`. No system Python install required.

</details>

<details>
<summary><strong>Cursor</strong></summary>

Click the badge to auto-install:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=miggo-mcp&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL21pZ2dvLWlvL21pZ2dvLW1jcCIsIm1pZ2dvLW1jcCJdLCJlbnYiOnsiTUlHR09fUFVCTElDX1RPS0VOIjoibWlnZ28tYXBpLXRva2VuIn19)

Or manually add to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "miggo": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/miggo-io/miggo-mcp", "miggo-mcp"],
      "env": {
        "MIGGO_PUBLIC_TOKEN": "<your-token>"
      }
    }
  }
}
```

Requires [`uv`](https://docs.astral.sh/uv/getting-started/installation/) on your `PATH`.

</details>

<details>
<summary><strong>VS Code / GitHub Copilot</strong></summary>

Add to your VS Code `settings.json` (`Cmd+Shift+P` → "Preferences: Open User Settings (JSON)"):

```json
{
  "mcp": {
    "servers": {
      "miggo": {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/miggo-io/miggo-mcp", "miggo-mcp"],
        "env": {
          "MIGGO_PUBLIC_TOKEN": "<your-token>"
        }
      }
    }
  }
}
```

Requires [`uv`](https://docs.astral.sh/uv/getting-started/installation/) on your `PATH`.

</details>

<details>
<summary><strong>JetBrains IDEs (IntelliJ, PyCharm, WebStorm, etc.)</strong></summary>

1. Open **Settings → Tools → AI Assistant → MCP Servers**
2. Add a new server with the following configuration:

```json
{
  "miggo": {
    "command": "uvx",
    "args": ["--from", "git+https://github.com/miggo-io/miggo-mcp", "miggo-mcp"],
    "env": {
      "MIGGO_PUBLIC_TOKEN": "<your-token>"
    }
  }
}
```

Requires [`uv`](https://docs.astral.sh/uv/getting-started/installation/) on your `PATH`.

</details>

<details>
<summary><strong>Other MCP-compatible clients</strong></summary>

Point your client at `uvx` using the standard MCP stdio configuration:

```json
{
  "mcpServers": {
    "miggo": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/miggo-io/miggo-mcp", "miggo-mcp"],
      "env": {
        "MIGGO_PUBLIC_TOKEN": "<your-token>"
      }
    }
  }
}
```

Requires [`uv`](https://docs.astral.sh/uv/getting-started/installation/) on your `PATH`.

</details>

---

## Example prompts

Once installed, try these to see what Miggo + your AI assistant can do:

| Prompt | What it does |
|--------|-------------|
| _"Give me a security overview of my environment — what are the top risks I should address first?"_ | Pulls services, findings, and vulnerabilities to build a prioritized risk summary. |
| _"Am I affected by CVE-2024-3094?"_ | Searches your dependencies and vulnerabilities for a specific CVE and shows which services are impacted. |
| _"List all my internet-facing endpoints and flag any with critical findings."_ | Combines endpoint and findings data to surface your most exposed attack surface. |

---

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `MIGGO_PUBLIC_TOKEN` | Yes | — | API token from the [Integrations portal](https://app.miggo.io/integrations/accessKey) |
| `MIGGO_PUBLIC_API_URL` | No | `https://api-beta.miggo.io` | Base URL of the Miggo API |
| `MIGGO_PUBLIC_DEFAULT_TAKE` | No | `10` | Default page size for list endpoints (max 50 per API call) |
| `MIGGO_PUBLIC_DEFAULT_SKIP` | No | `0` | Default offset for list endpoints |
| `MIGGO_PUBLIC_DEFAULT_SORT` | No | `risk,desc` | Default sort as `field,direction` pairs |

---

## Development

### Running locally

> **Note:** Ensure `MIGGO_PUBLIC_TOKEN` is exported in your environment.

```bash
# Start the stdio server
uv run ./run.py

# Or launch the MCP Inspector for interactive testing
uv run mcp dev ./run.py
```

### Building artifacts

```bash
uv run python scripts/build.py
```

Produces the MCPB bundle at `dist/miggo-mcp.mcpb` (a small zip containing `manifest.json`, `pyproject.toml`, `uv.lock`, `run.py`, and the `src/` tree). Claude Desktop's bundled `uv` provisions the runtime on the user's machine when the `.mcpb` is installed; no platform-specific binaries are produced. Pass `--help` for options.

### Testing, formatting, linting

```bash
uv run pytest
uv run ruff format .
uv run ruff check .
```

Install pre-commit hooks:

```bash
uv run pre-commit install
```

### Release process

We use [release-please](https://github.com/googleapis/release-please) to automate releases and version bumps. In normal operation, just review and merge the release PR that release-please opens. The workflow can also be triggered manually if needed.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on submitting issues and pull requests.

---

## License

[MIT](LICENSE)
