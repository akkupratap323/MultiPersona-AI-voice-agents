"""
Patched FastAPI WebSocket transport for pipecat 0.0.101.

This module provides a patched version of FastAPIWebsocketInputTransport that
fixes a bug where broadcast_frame was called with a frame instance instead of
a frame class, causing "'InputTransportMessageFrame' object is not callable" error.

The fix uses broadcast_frame_instance() instead of broadcast_frame() when
handling existing InputTransportMessageFrame instances from the deserializer.
"""

from typing import Optional

from loguru import logger

from pipecat.frames.frames import (
    InputAudioRawFrame,
    InputTransportMessageFrame,
)
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketInputTransport as OriginalInputTransport,
    FastAPIWebsocketOutputTransport,
    FastAPIWebsocketTransport as OriginalTransport,
    FastAPIWebsocketParams,
    FastAPIWebsocketClient,
    FastAPIWebsocketCallbacks,
)

try:
    from fastapi import WebSocket
except ModuleNotFoundError:
    raise Exception("Missing FastAPI module")


class PatchedFastAPIWebsocketInputTransport(OriginalInputTransport):
    """Patched input transport that fixes the broadcast_frame bug.

    The original code in _receive_messages() calls:
        await self.broadcast_frame(frame)

    But broadcast_frame() expects a frame CLASS, not an instance.
    This patch uses broadcast_frame_instance() instead.
    """

    async def _receive_messages(self):
        """Receive and process incoming WebSocket messages.

        This is a patched version that correctly handles InputTransportMessageFrame
        by using broadcast_frame_instance() instead of broadcast_frame().
        """
        try:
            async for message in self._client.receive():
                if not self._params.serializer:
                    continue

                frame = await self._params.serializer.deserialize(message)

                if not frame:
                    continue

                if isinstance(frame, InputAudioRawFrame):
                    await self.push_audio_frame(frame)
                elif isinstance(frame, InputTransportMessageFrame):
                    # FIX: Use broadcast_frame_instance for existing frame instances
                    await self.broadcast_frame_instance(frame)
                else:
                    await self.push_frame(frame)
        except Exception as e:
            logger.error(f"{self} exception receiving data: {e.__class__.__name__} ({e})")

        # Trigger `on_client_disconnected` if the client actually disconnects,
        # that is, we are not the ones disconnecting.
        if not self._client.is_closing:
            await self._client.trigger_client_disconnected()


class PatchedFastAPIWebsocketTransport(OriginalTransport):
    """Patched transport that uses the fixed input transport."""

    def __init__(
        self,
        websocket: WebSocket,
        params: FastAPIWebsocketParams,
        input_name: Optional[str] = None,
        output_name: Optional[str] = None,
    ):
        # Call BaseTransport's __init__ directly to set up base properties
        BaseTransport.__init__(self, input_name=input_name, output_name=output_name)

        self._params = params

        self._callbacks = FastAPIWebsocketCallbacks(
            on_client_connected=self._on_client_connected,
            on_client_disconnected=self._on_client_disconnected,
            on_session_timeout=self._on_session_timeout,
        )

        self._client = FastAPIWebsocketClient(websocket, self._callbacks)

        # Use patched input transport instead of original
        self._input = PatchedFastAPIWebsocketInputTransport(
            self, self._client, self._params, name=self._input_name
        )
        self._output = FastAPIWebsocketOutputTransport(
            self, self._client, self._params, name=self._output_name
        )

        # Register supported handlers
        self._register_event_handler("on_client_connected")
        self._register_event_handler("on_client_disconnected")
        self._register_event_handler("on_session_timeout")

        logger.debug("Using patched FastAPIWebsocketTransport with broadcast_frame_instance fix")
