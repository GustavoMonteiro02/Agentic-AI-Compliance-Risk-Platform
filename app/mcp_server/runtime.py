from app.config import get_settings
from app.mcp_server.server import PROMPTS, RESOURCES, TOOLS, create_fastmcp_server


def runtime_config() -> dict:
    settings = get_settings()
    return {
        "server_name": settings.mcp_server_name,
        "transport": settings.mcp_transport,
        "host": settings.mcp_host,
        "port": settings.mcp_port,
        "tool_count": len(TOOLS),
        "resource_count": len(RESOURCES),
        "prompt_count": len(PROMPTS),
    }


def run_mcp_server() -> None:
    settings = get_settings()
    server = create_fastmcp_server()
    if settings.mcp_transport == "stdio":
        server.run()
        return
    try:
        server.run(transport=settings.mcp_transport, host=settings.mcp_host, port=settings.mcp_port)
    except TypeError:
        server.run(settings.mcp_transport)
