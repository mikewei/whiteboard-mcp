# A Web-based Whiteboard with MCP interface

whiteboard-mcp is a simple whiteboard web application, providing a convenient way for displaying Chatbot/LLM's output.

## Install from source

```
git clone .../whiteboard-mcp
cd whiteboard-mcp
uv run whiteboard_mcp
```

## MCP configure

```
{
    "mcpServers": {
        "whiteboard-mcp": {
            "command": "npx",
            "args": [
                "mcp-remote",
                "http://127.0.0.1:5000/mcp/sse",
                "--allow-http"
            ]
        }
    }
}
```

