from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
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

app = FastAPI(title="Whiteboard Service")

# 存储白板内容的文件
CONTENT_FILE = BASE_DIR / 'whiteboard_content.json'

# 设置模板
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 存储所有活动的SSE连接
active_connections: List[asyncio.Queue] = []

class ContentUpdate(BaseModel):
    type: Literal["html", "url"]
    content: str

def load_content():
    if CONTENT_FILE.exists():
        with open(CONTENT_FILE, 'r') as f:
            return json.load(f)
    return {'type': 'html', 'content': '<h1>欢迎使用白板</h1>'}

def save_content(content):
    with open(CONTENT_FILE, 'w') as f:
        json.dump(content, f)

async def notify_clients(content):
    """通知所有连接的客户端内容已更新"""
    for queue in active_connections:
        await queue.put(content)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/content")
async def get_content():
    return load_content()

@app.post("/api/content")
async def update_content(content: ContentUpdate):
    content_data = {
        'type': content.type,
        'content': content.content,
        'updated_at': datetime.now().isoformat()
    }
    save_content(content_data)
    # 通知所有客户端
    await notify_clients(content_data)
    return {"message": "内容已更新"}

@app.get("/api/events")
async def events():
    """SSE事件流端点"""
    async def event_generator():
        # 创建新的消息队列
        queue = asyncio.Queue()
        active_connections.append(queue)
        try:
            # 发送初始内容
            initial_content = load_content()
            yield {
                "event": "message",
                "data": json.dumps(initial_content)
            }
            
            # 等待新消息
            while True:
                content = await queue.get()
                yield {
                    "event": "message",
                    "data": json.dumps(content)
                }
        finally:
            # 清理连接
            active_connections.remove(queue)

    return EventSourceResponse(event_generator())

mcp = FastMCP(name="whiteboard", version="1.0.0", description="白板服务")

@mcp.tool()
async def update_whiteboard_url(url: str):
    """通过指定URL更新白板内容"""
    await update_content(ContentUpdate(type="url", content=url))
    return {"message": "whiteboard updated"}

@mcp.tool()
async def update_whiteboard_html(html: str):
    """通过指定HTML更新白板内容"""
    await update_content(ContentUpdate(type="html", content=html))
    return {"message": "whiteboard updated"}


def main():
    app.mount("/mcp", mcp.sse_app())
    uvicorn.run(app, host="0.0.0.0", port=5000)

if __name__ == '__main__':
    main() 