import logging
import zenoh
import time
from pydantic import Field
from typing import Optional, List

from inputs.base import Message, SensorConfig
from inputs.base.loop import FuserInput
from zenoh_msgs import open_zenoh_session
from providers.io_provider import IOProvider

class PersonaPlexMicConfig(SensorConfig):
    """
    Configuration for PersonaPlex Microphone Proxy.
    """
    input_name: str = Field(default="PersonaPlex Mic", description="Name of the input")
    mic_topic: str = Field(default="pepper/audio/mic", description="Zenoh topic for raw mic audio (outgoing)")
    transcription_topic: str = Field(default="pepper/audio/transcription", description="Zenoh topic for transcribed text (incoming)")

class PersonaPlexMicInput(FuserInput[PersonaPlexMicConfig, Optional[str]]):
    """
    Captures transcribed text from PersonaPlex via Zenoh.
    """
    def __init__(self, config: PersonaPlexMicConfig):
        super().__init__(config)
        self.session = open_zenoh_session()
        self.io_provider = IOProvider()
        self.publisher = self.session.declare_publisher(self.config.mic_topic)
        self.subscriber = self.session.declare_subscriber(self.config.transcription_topic, self._on_transcription)
        self._current_buffer: List[str] = []
        self._latest_messages: List[str] = []
        logging.info(f"PersonaPlex Mic Proxy initialized. Listening for text on {self.config.transcription_topic}")

    def _on_transcription(self, sample):
        try:
            text = sample.payload.to_string()
            self._current_buffer.append(text)
        except Exception as e:
            logging.error(f"Error parsing transcription: {e}")

    async def _poll(self) -> Optional[str]:
        # Concatenate buffered tokens into a single string for this tick
        if not self._current_buffer:
            return None
        
        full_text = "".join(self._current_buffer)
        self._current_buffer = [] # Clear buffer
        
        # Add to history for brain
        self._latest_messages.append(full_text)
        
        # Add to IOProvider for simulator
        self.io_provider.add_input(self.config.input_name, full_text, time.time())
        
        return full_text

    async def raw_to_text(self, raw_input: Optional[str]) -> Optional[str]:
        return raw_input # Already text from Zenoh

    def formatted_latest_buffer(self) -> Optional[str]:
        if not self._latest_messages:
            return None
        
        combined = " ".join(self._latest_messages)
        self._latest_messages = []
        
        return f"""
{self.config.input_name} INPUT
// START
{combined}
// END
"""

