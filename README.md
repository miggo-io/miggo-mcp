# Miggo Public API MCP Server

This package ships a self-contained MCP stdio server that talks to Miggo's
[public API](https://api-beta.miggo.io).

## Installation

In all installation scenarios, you'll first need to create an API token [through the Integrations portal](https://app.miggo.io/integrations/accessKey).

### Claude Desktop - MCPB

This server is packaged as an MCP Bundle (MCPB) for easy one-click installation in compatible applications.

1. Download the latest `.mcpb` bundle from the [releases page](https://github.com/miggo/miggo-public-mcp/releases)
2. Open to install in Claude Desktop
3. Configure your `MIGGO_PUBLIC_TOKEN` in the application's MCP settings

### Cursor, VSCode, other MCP clients

Download the latest `miggo-server-mcp` from the [releases page](https://github.com/miggo/miggo-public-mcp/releases)

> ![NOTE]
> On Mac, you'll need to move the file outside of the Downloads folder
> On Windows, download the exe

If you're using Cursor, use this shortcut:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=miggo-public-mcp&config=eyJjb21tYW5kIjoiYmFzaCIsImFyZ3MiOlsiLWMiLCInL3BhdGgvdG8vbWlnZ28tcHVibGljLW1jcCciXSwiZW52Ijp7Ik1JR0dPX1BVQkxJQ19UT0tFTiI6Im1pZ2dvLWFwaS10b2tlbiJ9fQ%3D%3D)

Or, add the following configuration to your MCP client:

```json
{
  "mcpServers": {
    "miggo-public": {
      "command": "bash",
      "args": ["-c", "'/path/to/miggo-public-mcp'"],
      "env": {
        "MIGGO_PUBLIC_TOKEN": "miggo-api-token"
      }
    }
  }
}
```

## Configuration

Export the following environment variables before launching the server:

| Variable | Required | Description |
| --- | --- | --- |
| `MIGGO_PUBLIC_TOKEN` | Yes | Bearer token issued by Miggo's authentication flow. |
| `MIGGO_PUBLIC_API_URL` | No | Base URL of the Miggo public API. Defaults to `https://api-beta.miggo.io`. |
| `MIGGO_PUBLIC_DEFAULT_TAKE` | Optional | Default page size for list endpoints (max 50). |
| `MIGGO_PUBLIC_DEFAULT_SKIP` | Optional | Default offset for list endpoints. |
| `MIGGO_PUBLIC_DEFAULT_SORT` | Optional | Default `field,direction` pairs (e.g. `risk,desc`). |

## CLI use

> ![NOTE]
> Ensure you're exporting the env var MIGGO_PUBLIC_TOKEN

Launch the stdio server with a run wrapper:

```bash
uv run ./run.py
```

This can be run from any directory - you can embed any full path that you like.

You can also run the MCP inspector:

```bash
uv run mcp dev ./run.py
```

## Building artefacts

Run the combined build helper to produce both the standalone binaries and MCPB bundle:

```bash
uv run python scripts/build.py
```

This regenerates the [Pyfuze](https://github.com/TanixLu/pyfuze) executables in `dist/` (`miggo-public-mcp`, `miggo-public-mcp.exe`) and writes the MCP bundle to `dist/miggo-public-mcp.mcpb`. Pass `--help` to see more options.

## Contributing

This server is implemented with:
- FastMCP as the mcp abstraction
- uv for package management
- pytest for testing
- ruff for formatting and linting
- pyfuze for standalone executable bundling

Quick contrib scripts:

```sh
# Test
uv run pytest

# Format & lint
uv run ruff format .
uv run ruff check .

# Build MCPB bundle
uv run python scripts/build.py
```

Install pre-commit hooks for greater ease:

```bash
uv run pre-commit install
```

Note that Pyfuze is relatively new - expect difficulties around upgrades.
