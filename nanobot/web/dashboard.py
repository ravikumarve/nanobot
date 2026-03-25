#!/usr/bin/env python3
"""
FastAPI web dashboard for nanobot.
Provides real-time monitoring UI with WebSocket support.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocketState

from nanobot.bus.queue import MessageBus
from nanobot.config.schema import WebConfig
from loguru import logger


class WebDashboard:
    """Web dashboard for real-time nanobot monitoring."""

    def __init__(self, bus: MessageBus, config: WebConfig):
        self.bus = bus
        self.config = config
        self.app = FastAPI(title="nanobot Dashboard", version="0.1.0")

        # Setup templates and static files
        base_dir = Path(__file__).parent
        self.templates = Jinja2Templates(directory=base_dir / "templates")

        self.app.mount("/static", StaticFiles(directory=base_dir / "static"), name="static")

        # WebSocket connections
        self.active_connections: list[WebSocket] = []

        # Setup routes
        self.setup_routes()

    def setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            return self.templates.TemplateResponse("dashboard.html", {"request": {}})

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                # Send initial state
                await self.send_initial_state(websocket)

                # Listen for messages
                while True:
                    data = await websocket.receive_text()
                    await self.handle_websocket_message(websocket, data)

            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)

    async def send_initial_state(self, websocket: WebSocket):
        """Send initial dashboard state."""
        state = {
            "type": "initial_state",
            "agents": 1,  # TODO: Get actual agent count
            "sessions": 0,  # TODO: Get session count
            "messages_processed": 0,  # TODO: Get message count
            "status": "running",
        }
        await websocket.send_json(state)

    async def handle_websocket_message(self, websocket: WebSocket, data: str):
        """Handle incoming WebSocket messages."""
        try:
            message = json.loads(data)

            if message.get("type") == "subscribe":
                # Handle subscription requests
                await self.handle_subscription(websocket, message)

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received: {data}")

    async def handle_subscription(self, websocket: WebSocket, message: dict):
        """Handle subscription requests."""
        channels = message.get("channels", [])
        # TODO: Implement channel-based subscription

        response = {"type": "subscription_ack", "channels": channels, "status": "subscribed"}
        await websocket.send_json(response)

    async def broadcast_message(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            if connection.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to WebSocket: {e}")
                    self.active_connections.remove(connection)

    async def start(self):
        """Start the web dashboard."""
        import uvicorn

        logger.info(f"Starting nanobot web dashboard on {self.config.host}:{self.config.port}")

        config = uvicorn.Config(
            self.app, host=self.config.host, port=self.config.port, log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


def create_web_dashboard(bus: MessageBus, config: WebConfig) -> WebDashboard:
    """Create and return a web dashboard instance."""
    return WebDashboard(bus, config)
