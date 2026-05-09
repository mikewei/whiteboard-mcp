import argparse
import importlib.metadata
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
from datetime import datetime
from typing import Literal, List
import uvicorn
from pathlib import Path
import asyncio
from sse_starlette.sse import EventSourceResponse
from mcp.server.fastmcp import FastMCP

# 获取当前文件所在目录
BASE_DIR = Path(__file__).resolve().parent

# 存储白板内容的文件
CONTENT_FILE = BASE_DIR / "whiteboard_content.json"

# 设置模板
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 存储所有活动的SSE连接
active_connections: List[asyncio.Queue] = []


class ContentUpdate(BaseModel):
    type: Literal["html", "url"]
    content: str


def load_content():
    if CONTENT_FILE.exists():
        with open(CONTENT_FILE, "r") as f:
            return json.load(f)
    return {"type": "html", "content": "<h1>欢迎使用白板</h1>"}


def save_content(content):
    with open(CONTENT_FILE, "w") as f:
        json.dump(content, f)


async def notify_clients(content):
    """通知所有连接的客户端内容已更新"""
    for queue in active_connections:
        await queue.put(content)


async def apply_content_update(content: ContentUpdate):
    """供 HTTP API 与 MCP 工具共用。"""
    content_data = {
        "type": content.type,
        "content": content.content,
        "updated_at": datetime.now().isoformat(),
    }
    save_content(content_data)
    await notify_clients(content_data)
    return {"message": "内容已更新"}


mcp = FastMCP(
    name="whiteboard",
    instructions="白板服务 MCP：可通过工具更新白板显示内容。",
    host="0.0.0.0",
    sse_path="/",
    message_path="/messages/",
    streamable_http_path="/",
)


@mcp.tool()
async def update_whiteboard_url(url: str):
    """通过指定URL更新白板内容"""
    await apply_content_update(ContentUpdate(type="url", content=url))
    return {"message": "whiteboard updated"}


@mcp.tool()
async def update_whiteboard_html(html: str):
    """通过指定HTML更新白板内容"""
    await apply_content_update(ContentUpdate(type="html", content=html))
    return {"message": "whiteboard updated"}


streamable_http_asgi = mcp.streamable_http_app()


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="Whiteboard Service", lifespan=app_lifespan)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )


@app.get("/api/content")
async def get_content():
    return load_content()


@app.post("/api/content")
async def update_content(content: ContentUpdate):
    return await apply_content_update(content)


@app.get("/api/events")
async def events():
    """SSE事件流端点"""

    async def event_generator():
        queue = asyncio.Queue()
        active_connections.append(queue)
        try:
            initial_content = load_content()
            yield {
                "event": "message",
                "data": json.dumps(initial_content),
            }
            while True:
                content = await queue.get()
                yield {
                    "event": "message",
                    "data": json.dumps(content),
                }
        finally:
            active_connections.remove(queue)

    return EventSourceResponse(event_generator())


def _version_from_pyproject(path: Path) -> str | None:
    """Read `version` from the `[project]` table in pyproject.toml."""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
            continue
        if in_project and stripped.startswith("[") and stripped.endswith("]"):
            break
        if in_project:
            match = re.match(r'version\s*=\s*"([^"]*)"', stripped)
            if match:
                return match.group(1)
    return None


def package_version() -> str:
    """Version from pyproject (installed wheel metadata first, then source tree)."""
    try:
        return importlib.metadata.version("whiteboard-mcp")
    except importlib.metadata.PackageNotFoundError:
        pass
    pyproject = BASE_DIR.parent.parent / "pyproject.toml"
    v = _version_from_pyproject(pyproject)
    if v is not None:
        return v
    return "unknown"


def main():
    parser = argparse.ArgumentParser(
        prog="whiteboard-mcp",
        description="Web whiteboard API and MCP server",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {package_version()}",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Bind port (default: 5000)",
    )
    args = parser.parse_args()

    app.mount("/sse", mcp.sse_app(mount_path="/sse"))
    app.mount("/mcp", streamable_http_asgi)
    uvicorn.run(app, host=args.host, port=args.port)
