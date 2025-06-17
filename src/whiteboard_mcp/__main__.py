import sys
import asyncio

def main():
    """主入口点"""
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        # 启动MCP服务
        from .mcp_server import main as mcp_main
        asyncio.run(mcp_main())
    elif len(sys.argv) > 1 and sys.argv[1] == "--help":
        # 显示帮助信息
        from .start_services import print_usage_info
        print_usage_info()
    else:
        # 默认启动Web服务
        from .app import main as web_main
        web_main()

if __name__ == "__main__":
    main() 