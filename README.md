# A Web-based Whiteboard with MCP interface

whiteboard-mcp is a simple whiteboard web application, providing a convenient way for displaying Chatbot/LLM's output.

## Features

- **Web whiteboard** — Browser UI to show content pushed by agents or other clients; good for demos and side-by-side LLM output.
- **Any screen** — Open the board URL in a browser on any monitor, projector, or device on your network.
- **Dual MCP transports** — **Streamable HTTP** at `/mcp` and **SSE** at `/sse` for clients that only support one style.
- **REST API** — `GET`/`POST /api/content` for non-MCP integrations; history list/restore/delete under `/api/history`.
- **History** — Server-side history of updates; reopen a past version from the history UI (and via the history API).
- **Export** — Save the current view as **HTML** or **Markdown** from the menu; **Print / PDF** (browser print-to-PDF) when the board shows HTML or Markdown.
- **Bilingual UI** — English and Chinese interface, file or in-app settings.

## Install

### From PYPI

```
pip install whiteboard-mcp
# or:
# uv tool install whiteboard-mcp
whiteboard-mcp
```

### From source

```
git clone .../whiteboard-mcp
cd whiteboard-mcp
uv run whiteboard_mcp
```

The server listens on `0.0.0.0:5000` by default.

## MCP endpoints

| Transport       | URL (local)                                      |
|-----------------|--------------------------------------------------|
| StreamableHTTP  | `http://127.0.0.1:5000/mcp` (POST `/mcp`)       |
| SSE (+ messages)| `http://127.0.0.1:5000/sse` (+ `POST /sse/messages/`) |

Use your machine's LAN IP instead of `127.0.0.1` when connecting from another device on the same network.

## MCP tools

The MCP server exposes these tools (names as registered with clients):

| Tool | Purpose |
|------|---------|
| `update_whiteboard_url` | Set the board to load a URL (`url`). |
| `update_whiteboard_html` | Render raw HTML (`html`). |
| `update_whiteboard_markdown` | Render Markdown (`markdown`). |

## MCP configure

### Standard /mcp API

Clients that support **Streamable HTTP** natively should point their MCP server URL at `http://127.0.0.1:5000/mcp` (adjust host/port for LAN as needed).

#### **Hermes-Agent** [MCP config](https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/mcp/mcp-native-mcp) example:

Add an HTTP transport entry under `mcp_servers` in `~/.hermes/config.yaml`, then restart Hermes. Example:

```yaml
mcp_servers:
  whiteboard:
    url: "http://127.0.0.1:5000/mcp"
```

### Compatible /sse API

For example you can use mcp-remote to connect /sse API:

```
{
    "mcpServers": {
        "whiteboard-mcp": {
            "command": "npx",
            "args": [
                "mcp-remote",
                "http://127.0.0.1:5000/sse",
                "--allow-http"
            ]
        }
    }
}
```
