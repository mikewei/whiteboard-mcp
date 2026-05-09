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
    return templates.TemplateResponse("index.html", {"request": request})


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


def main():
    app.mount("/sse", mcp.sse_app(mount_path="/sse"))
    app.mount("/mcp", streamable_http_asgi)
    uvicorn.run(app, host="0.0.0.0", port=5000)
