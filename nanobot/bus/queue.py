"""Async message queue for decoupled channel-agent communication."""

import asyncio
import time
from collections import defaultdict

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage


class MessageBus:
    """
    Async message bus that decouples chat channels from the agent core.

    Channels push messages to the inbound queue, and the agent processes
    them and pushes responses to the outbound queue.
    """

    def __init__(self):
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()

        # Rate limiting state
        self._bus_rate_limit: dict[str, tuple[int, float]] = defaultdict(lambda: (0, time.time()))
        self._rate_limit_lock = asyncio.Lock()

    async def publish_inbound(self, msg: InboundMessage) -> None:
        """Publish a message from a channel to the agent."""
        # Check bus-level rate limiting
        if not await self._check_bus_rate_limit(msg.channel, msg.sender_id):
            logger.warning("Bus rate limit exceeded for {}:{}", msg.channel, msg.sender_id)
            return

        await self.inbound.put(msg)

    async def _check_bus_rate_limit(self, channel: str, user_id: str) -> bool:
        """
        Check bus-level rate limiting to prevent flooding.

        Limits: 100 messages per minute per user-channel combination
        """
        async with self._rate_limit_lock:
            key = f"{channel}:{user_id}"
            count, last_reset = self._bus_rate_limit[key]

            # Reset counter if more than 60 seconds have passed
            if time.time() - last_reset > 60:
                count = 0
                last_reset = time.time()

            # Check limit
            if count >= 100:  # 100 messages per minute
                return False

            # Update counter
            self._bus_rate_limit[key] = (count + 1, last_reset)
            return True

    async def consume_inbound(self) -> InboundMessage:
        """Consume the next inbound message (blocks until available)."""
        return await self.inbound.get()

    async def publish_outbound(self, msg: OutboundMessage) -> None:
        """Publish a response from the agent to channels."""
        await self.outbound.put(msg)

    async def consume_outbound(self) -> OutboundMessage:
        """Consume the next outbound message (blocks until available)."""
        return await self.outbound.get()

    @property
    def inbound_size(self) -> int:
        """Number of pending inbound messages."""
        return self.inbound.qsize()

    @property
    def outbound_size(self) -> int:
        """Number of pending outbound messages."""
        return self.outbound.qsize()
