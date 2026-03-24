"""Base channel interface for chat platforms."""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.config.schema import RateLimitConfig
from nanobot.utils.rate_limit import RateLimitManager


class BaseChannel(ABC):
    """
    Abstract base class for chat channel implementations.

    Each channel (Telegram, Discord, etc.) should implement this interface
    to integrate with the nanobot message bus.
    """

    name: str = "base"

    def __init__(self, config: Any, bus: MessageBus):
        """
        Initialize the channel.

        Args:
            config: Channel-specific configuration.
            bus: The message bus for communication.
        """
        self.config = config
        self.bus = bus
        self._running = False
        self.rate_limit_manager = RateLimitManager()

        # Configure channel-level rate limiting
        if hasattr(config, "rate_limit") and isinstance(config.rate_limit, RateLimitConfig):
            self.rate_limit_manager.configure_channel(
                self.name, config.rate_limit.max_requests_per_minute, config.rate_limit.burst_size
            )

    @abstractmethod
    async def start(self) -> None:
        """
        Start the channel and begin listening for messages.

        This should be a long-running async task that:
        1. Connects to the chat platform
        2. Listens for incoming messages
        3. Forwards messages to the bus via _handle_message()
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel and clean up resources."""
        pass

    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """
        Send a message through this channel.

        Args:
            msg: The message to send.
        """
        pass

    def is_allowed(self, sender_id: str) -> bool:
        """Check if *sender_id* is permitted.  Empty list → deny all; ``"*"`` → allow all."""
        allow_list = getattr(self.config, "allow_from", [])
        if not allow_list:
            logger.warning("{}: allow_from is empty — all access denied", self.name)
            return False
        if "*" in allow_list:
            return True
        sender_str = str(sender_id)
        return sender_str in allow_list or any(p in allow_list for p in sender_str.split("|") if p)

    async def _handle_message(
        self,
        sender_id: str,
        chat_id: str,
        content: str,
        media: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        session_key: str | None = None,
    ) -> None:
        """
        Handle an incoming message from the chat platform.

        This method checks permissions and forwards to the bus.

        Args:
            sender_id: The sender's identifier.
            chat_id: The chat/channel identifier.
            content: Message text content.
            media: Optional list of media URLs.
            metadata: Optional channel-specific metadata.
            session_key: Optional session key override (e.g. thread-scoped sessions).
        """
        if not self.is_allowed(sender_id):
            logger.warning(
                "Access denied for sender {} on channel {}. "
                "Add them to allowFrom list in config to grant access.",
                sender_id,
                self.name,
            )
            return

        # Check rate limiting
        rate_limit_config = getattr(self.config, "rate_limit", None)
        if not await self.rate_limit_manager.check_rate_limit(
            self.name, str(sender_id), rate_limit_config
        ):
            logger.warning("Rate limit exceeded for sender {} on channel {}", sender_id, self.name)
            # Send rate limit message if channel supports it
            await self._send_rate_limit_message(sender_id, chat_id)
            return

        msg = InboundMessage(
            channel=self.name,
            sender_id=str(sender_id),
            chat_id=str(chat_id),
            content=content,
            media=media or [],
            metadata=metadata or {},
            session_key_override=session_key,
        )

        await self.bus.publish_inbound(msg)

    async def _send_rate_limit_message(self, sender_id: str, chat_id: str) -> None:
        """Send rate limit exceeded message to user."""
        try:
            rate_limit_msg = OutboundMessage(
                channel=self.name,
                sender_id=str(sender_id),
                chat_id=str(chat_id),
                content="⚠️ Rate limit exceeded. Please wait before sending more messages.",
                media=[],
                metadata={"rate_limit": True},
            )
            await self.send(rate_limit_msg)
        except Exception:
            logger.warning("Failed to send rate limit message to {}:{}", self.name, sender_id)

    @property
    def is_running(self) -> bool:
        """Check if the channel is running."""
        return self._running
