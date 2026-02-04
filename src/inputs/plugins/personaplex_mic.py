import logging
import zenoh
from pydantic import Field
from typing import Optional

from inputs.base import Message, SensorConfig
from inputs.base.loop import FuserInput
from zenoh_msgs import open_zenoh_session

class PersonaPlexMicConfig(SensorConfig):
    """
    Configuration for PersonaPlex Microphone Proxy.
    Sends raw audio data to the PersonaPlex fork via Zenoh.
    """
    input_name: str = Field(default="PersonaPlex Mic", description="Name of the input")
    topic: str = Field(default="pepper/audio/mic", description="Zenoh topic for mic audio")

class PersonaPlexMicInput(FuserInput[PersonaPlexMicConfig, Optional[str]]):
    """
    Captures audio data and publishes it to Zenoh for the PersonaPlex process.
    This keeps the audio capture decoupled from the reasoning.
    """
    def __init__(self, config: PersonaPlexMicConfig):
        super().__init__(config)
        self.session = open_zenoh_session()
        self.publisher = self.session.declare_publisher(self.config.topic)
        logging.info(f"PersonaPlex Mic Proxy initialized on {self.config.topic}")

    async def _poll(self) -> Optional[str]:
        # Here you would capture real audio from Pepper's Naoqi or PyAudio
        # and publish it to Zenoh.
        # For now, it's a skeleton for the decoupled architecture.
        return None

    async def raw_to_text(self, raw_input: Optional[str]):
        # In a hybrid setup, PersonaPlex handles the audio-to-audio.
        # This plugin can optionally return transcribed text from Zenoh
        # if PersonaPlex publishes it back.
        pass

    def formatted_latest_buffer(self) -> Optional[str]:
        return None
