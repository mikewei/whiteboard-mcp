# A Web-based Whiteboard with MCP interface

whiteboard-mcp is a simple whiteboard web application, providing a convenient way for displaying Chatbot/LLM's output.

## Install from source

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

## MCP configure (SSE via mcp-remote)

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

Clients that support **Streamable HTTP** natively should point their MCP server URL at `http://127.0.0.1:5000/mcp` (adjust host/port for LAN as needed).
