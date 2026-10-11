"""
Entrypoint runner for InsureChain VoiceGuard FastAPI backend.
Configures WindowsSelectorEventLoopPolicy and loop="none" for psycopg 3 async compatibility.
"""
import sys

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

async def main():
    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        loop="none",
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
